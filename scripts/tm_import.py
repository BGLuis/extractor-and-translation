#!/usr/bin/env python3
"""
Importa um arquivo TMX 1.4b (revisado num CAT tool como OmegaT/Weblate) de volta para
a Translation Memory (cache/memory.db), com status='reviewed' por padrão - o que faz
essas traduções vencerem qualquer tradução de máquina já existente para o mesmo texto.

Uso:
    python scripts/tm_import.py --file review.tmx --engine human
    python scripts/tm_import.py --file glossario.tmx --engine human --status locked
"""
import argparse
import os
import sys

import defusedxml.ElementTree as safe_ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.translate.TranslationMemory import TranslationMemory

DB_PATH = os.path.join('cache', 'memory.db')


def _lang_attr(tuv):
    return tuv.get('{http://www.w3.org/XML/1998/namespace}lang') or tuv.get('lang')


def import_tmx(db_path, tmx_path, engine='human', status='reviewed'):
    tree = safe_ET.parse(tmx_path)
    imported = 0
    skipped = 0

    tm_cache = {}

    for tu in tree.getroot().iter('tu'):
        segments = {}
        for tuv in tu.findall('tuv'):
            lang = _lang_attr(tuv)
            seg = tuv.find('seg')
            if lang and seg is not None and seg.text:
                segments[lang] = seg.text

        if len(segments) < 2:
            skipped += 1
            continue

        (src_lang, source), (tgt_lang, target) = list(segments.items())[:2]

        key = (src_lang, tgt_lang)
        if key not in tm_cache:
            tm_cache[key] = TranslationMemory(db_path, src_lang, tgt_lang, engine=engine)
        tm_cache[key].store(source, target, status=status)
        imported += 1

    return imported, skipped


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--file', required=True, help='Caminho do arquivo .tmx a importar')
    parser.add_argument('--engine', default='human', help='Rótulo da origem da tradução (padrão: human)')
    parser.add_argument('--status', default='reviewed', choices=['reviewed', 'locked', 'machine'],
                         help='Status atribuído às entradas importadas (padrão: reviewed)')
    parser.add_argument('--db', default=DB_PATH, help=f'Caminho do banco (padrão: {DB_PATH})')
    args = parser.parse_args()

    imported, skipped = import_tmx(args.db, args.file, args.engine, args.status)
    print(f"{imported} segmentos importados (status={args.status}), {skipped} ignorados (incompletos)")
