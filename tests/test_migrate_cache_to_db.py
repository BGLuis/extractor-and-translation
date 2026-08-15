import importlib
import json
import sqlite3

import pytest


@pytest.fixture
def migrate_module(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache_dir = tmp_path / 'cache' / 'googleTraslator'
    cache_dir.mkdir(parents=True)
    (cache_dir / 'cache_en_pt.json').write_text(json.dumps({
        "": "",
        "hello": "ola",
        "same": "same",
        "symbols only": None,
    }), encoding='utf-8')

    from src.translate.TranslationMemory import TranslationMemory
    TranslationMemory._connections.clear()

    import scripts.migrate_cache_to_db as module
    importlib.reload(module)
    return module


def test_migration_skips_sentinel_and_null_entries(migrate_module, capsys):
    migrate_module.migrate()
    conn = sqlite3.connect(migrate_module.DB_PATH)
    rows = conn.execute("SELECT source, target FROM segment").fetchall()

    assert ('hello', 'ola') in rows
    assert ('same', 'same') in rows
    assert not any(source == '' for source, _ in rows)
    assert not any(source == 'symbols only' for source, _ in rows)


def test_migration_is_idempotent(migrate_module):
    migrate_module.migrate()
    migrate_module.migrate()

    conn = sqlite3.connect(migrate_module.DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM segment").fetchone()[0]
    assert count == 2  # "hello" e "same"; sentinel e null ficam de fora
