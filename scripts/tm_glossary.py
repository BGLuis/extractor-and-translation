#!/usr/bin/env python3
"""
Promove um termo a status='locked' na Translation Memory: fica imune a sobrescrita
por traduções de máquina ou revisadas, e passa a ser o resultado preferido em
qualquer lookup (glossário). O lookup já consulta 'locked' antes de qualquer coisa,
então nada mais precisa ser configurado além de rodar este comando.

Uso:
    python scripts/tm_glossary.py --src ja --tgt pt --source "ルイ" --target "Rui"
    python scripts/tm_glossary.py --src ja --tgt pt --list
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.translate.TranslationMemory import TranslationMemory

DB_PATH = os.path.join('cache', 'memory.db')


def list_glossary(db_path, src_lang, tgt_lang):
    conn = sqlite3.connect(db_path)
    return conn.execute(
        "SELECT source, target FROM segment WHERE src_lang=? AND tgt_lang=? AND status='locked'",
        (src_lang, tgt_lang),
    ).fetchall()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--src', required=True)
    parser.add_argument('--tgt', required=True)
    parser.add_argument('--source', help='Termo de origem a travar')
    parser.add_argument('--target', help='Tradução fixa para o termo')
    parser.add_argument('--list', action='store_true', help='Listar termos já travados')
    parser.add_argument('--db', default=DB_PATH)
    args = parser.parse_args()

    if args.list:
        for source, target in list_glossary(args.db, args.src, args.tgt):
            print(f"{source} -> {target}")
    elif args.source and args.target:
        tm = TranslationMemory(args.db, args.src, args.tgt, engine='glossary')
        tm.lock_term(args.source, args.target)
        print(f"Travado: {args.source!r} -> {args.target!r}")
    else:
        parser.error('Use --source e --target para travar um termo, ou --list para listar.')
