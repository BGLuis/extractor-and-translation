#!/usr/bin/env python3
"""
Exporta a Translation Memory (cache/memory.db) para TMX 1.4b, o formato padrão da
indústria para intercâmbio com CAT tools (OmegaT, Weblate...).

Uso:
    python scripts/tm_export.py --src ja --tgt pt --out review.tmx
    python scripts/tm_export.py --src ja --tgt pt --status reviewed,locked --out glossario.tmx
"""
import argparse
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_PATH = os.path.join('cache', 'memory.db')


def export_tmx(db_path, src_lang, tgt_lang, out_path, statuses=None):
    conn = sqlite3.connect(db_path)
    query = "SELECT DISTINCT source, target FROM segment WHERE src_lang=? AND tgt_lang=?"
    params = [src_lang, tgt_lang]
    if statuses:
        placeholders = ','.join('?' for _ in statuses)
        query += f" AND status IN ({placeholders})"
        params.extend(statuses)

    rows = conn.execute(query, params).fetchall()

    tmx = ET.Element('tmx', version='1.4')
    header = ET.SubElement(tmx, 'header', {
        'creationtool': 'extractor-and-translation',
        'creationtoolversion': '1.0',
        'datatype': 'plaintext',
        'segtype': 'sentence',
        'adminlang': 'en',
        'srclang': src_lang,
        'o-tmf': 'extractor-and-translation',
    })
    body = ET.SubElement(tmx, 'body')

    for source, target in rows:
        tu = ET.SubElement(body, 'tu')
        tuv_src = ET.SubElement(tu, 'tuv', {'xml:lang': src_lang})
        ET.SubElement(tuv_src, 'seg').text = source
        tuv_tgt = ET.SubElement(tu, 'tuv', {'xml:lang': tgt_lang})
        ET.SubElement(tuv_tgt, 'seg').text = target

    ET.ElementTree(tmx).write(out_path, encoding='utf-8', xml_declaration=True)
    return len(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--src', required=True, help='Idioma de origem (ex: ja)')
    parser.add_argument('--tgt', required=True, help='Idioma de destino (ex: pt)')
    parser.add_argument('--out', required=True, help='Caminho do arquivo .tmx de saída')
    parser.add_argument('--status', help='Filtrar por status, separado por vírgula (ex: reviewed,locked)')
    parser.add_argument('--db', default=DB_PATH, help=f'Caminho do banco (padrão: {DB_PATH})')
    args = parser.parse_args()

    statuses = args.status.split(',') if args.status else None
    count = export_tmx(args.db, args.src, args.tgt, args.out, statuses)
    print(f"{count} segmentos exportados para {args.out}")
