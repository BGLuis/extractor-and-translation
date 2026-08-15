import hashlib
import os
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS segment (
    id INTEGER PRIMARY KEY,
    src_lang TEXT NOT NULL,
    tgt_lang TEXT NOT NULL,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    engine TEXT NOT NULL,
    model TEXT,
    game TEXT,
    context TEXT,
    status TEXT NOT NULL DEFAULT 'machine',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_seg_lookup
    ON segment(src_lang, tgt_lang, source_hash, engine);
CREATE INDEX IF NOT EXISTS idx_seg_status ON segment(status);
CREATE VIRTUAL TABLE IF NOT EXISTS segment_fts USING fts5(source, content='segment', content_rowid='id');

CREATE TRIGGER IF NOT EXISTS segment_ai AFTER INSERT ON segment BEGIN
    INSERT INTO segment_fts(rowid, source) VALUES (new.id, new.source);
END;
CREATE TRIGGER IF NOT EXISTS segment_au AFTER UPDATE ON segment BEGIN
    INSERT INTO segment_fts(segment_fts, rowid, source) VALUES('delete', old.id, old.source);
    INSERT INTO segment_fts(rowid, source) VALUES (new.id, new.source);
END;
CREATE TRIGGER IF NOT EXISTS segment_ad AFTER DELETE ON segment BEGIN
    INSERT INTO segment_fts(segment_fts, rowid, source) VALUES('delete', old.id, old.source);
END;
"""

def _status_rank_expr(column_ref):
    return f"CASE {column_ref} WHEN 'locked' THEN 0 WHEN 'reviewed' THEN 1 ELSE 2 END"


_STATUS_RANK = _status_rank_expr('status')


def normalize_source(text):
    return ' '.join(text.split())


def source_hash(text):
    return hashlib.sha1(normalize_source(text).encode('utf-8')).hexdigest()


class TranslationMemory:
    """
    Backend SQLite para o cache de traduções, com interface parecida com dict
    (`in`, `[]`, `[]=`) para não exigir mudanças em BaseTranslate.translate_batch.

    Uma conexão (com seu próprio lock) é compartilhada por db_path entre todas as
    instâncias/threads/deepcopies que apontam para o mesmo arquivo .db.
    """

    _connections = {}
    _connections_lock = threading.Lock()

    def __init__(self, db_path, src_lang, tgt_lang, engine, game=None):
        self.db_path = db_path
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.engine = engine
        self.game = game
        self._conn, self._lock = self._get_shared_connection(db_path)

    @classmethod
    def _get_shared_connection(cls, db_path):
        with cls._connections_lock:
            entry = cls._connections.get(db_path)
            if entry is None:
                os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
                conn = sqlite3.connect(db_path, check_same_thread=False)
                conn.execute('PRAGMA journal_mode=WAL')
                conn.executescript(SCHEMA)
                conn.commit()
                entry = {'conn': conn, 'lock': threading.Lock()}
                cls._connections[db_path] = entry
        return entry['conn'], entry['lock']

    def __contains__(self, text):
        return self.lookup(text) is not None

    def __getitem__(self, text):
        result = self.lookup(text)
        if result is None:
            raise KeyError(text)
        return result

    def __setitem__(self, text, translated):
        self.store(text, translated)

    def lookup(self, text):
        h = source_hash(text)
        with self._lock:
            row = self._conn.execute(
                f"""SELECT target FROM segment
                    WHERE src_lang=? AND tgt_lang=? AND source_hash=?
                    ORDER BY {_STATUS_RANK} LIMIT 1""",
                (self.src_lang, self.tgt_lang, h),
            ).fetchone()
        return row[0] if row else None

    def store(self, text, translated, status='machine', context=None):
        h = source_hash(text)
        now = time.strftime('%Y-%m-%dT%H:%M:%S')
        with self._lock:
            self._conn.execute(
                f"""INSERT INTO segment
                       (src_lang, tgt_lang, source, target, source_hash, engine, game, context, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(src_lang, tgt_lang, source_hash, engine) DO UPDATE SET
                       target=excluded.target, status=excluded.status, updated_at=excluded.updated_at
                       WHERE {_status_rank_expr('excluded.status')} <= {_status_rank_expr('segment.status')}""",
                (self.src_lang, self.tgt_lang, text, translated, h, self.engine, self.game, context, status, now, now),
            )
            self._conn.commit()

    def lock_term(self, source_text, translated_text):
        self.store(source_text, translated_text, status='locked')

    def fuzzy_candidates(self, text, limit=5):
        """Sugestões por similaridade textual (FTS5), nunca aplicadas automaticamente."""
        with self._lock:
            rows = self._conn.execute(
                """SELECT segment.source, segment.target, segment.status FROM segment_fts
                   JOIN segment ON segment.id = segment_fts.rowid
                   WHERE segment_fts.source MATCH ? AND segment.src_lang=? AND segment.tgt_lang=?
                   LIMIT ?""",
                (normalize_source(text), self.src_lang, self.tgt_lang, limit),
            ).fetchall()
        return [{'source': r[0], 'target': r[1], 'status': r[2]} for r in rows]
