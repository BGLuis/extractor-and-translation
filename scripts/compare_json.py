#!/usr/bin/env python3
"""
Script para comparar arquivos JSON grandes (input vs output)
Mostra diferenças de forma estruturada e focada em textos traduzidos
"""

import json
import sys
from pathlib import Path
from difflib import unified_diff


def load_json(file_path):
    """Carrega arquivo JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_values(original, translated, path=""):
    """Compara valores recursivamente e retorna diferenças"""
    differences = []

    if type(original) != type(translated):
        differences.append({
            'path': path,
            'type': 'type_change',
            'original': f"{type(original).__name__}: {original}",
            'translated': f"{type(translated).__name__}: {translated}"
        })
        return differences

    if isinstance(original, dict):
        all_keys = set(original.keys()) | set(translated.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key

            if key not in original:
                differences.append({
                    'path': new_path,
                    'type': 'added',
                    'original': None,
                    'translated': translated[key]
                })
            elif key not in translated:
                differences.append({
                    'path': new_path,
                    'type': 'removed',
                    'original': original[key],
                    'translated': None
                })
            else:
                differences.extend(compare_values(original[key], translated[key], new_path))

    elif isinstance(original, list):
        max_len = max(len(original), len(translated))
        for i in range(max_len):
            new_path = f"{path}[{i}]"

            if i >= len(original):
                differences.append({
                    'path': new_path,
                    'type': 'added',
                    'original': None,
                    'translated': translated[i]
                })
            elif i >= len(translated):
                differences.append({
                    'path': new_path,
                    'type': 'removed',
                    'original': original[i],
                    'translated': None
                })
            else:
                differences.extend(compare_values(original[i], translated[i], new_path))

    else:
        # Valores simples
        if original != translated:
            differences.append({
                'path': path,
                'type': 'changed',
                'original': original,
                'translated': translated
            })

    return differences


def extract_event_texts(data):
    """Extrai textos de eventos do JSON"""
    texts = []

    if 'events' not in data:
        return texts

    for event in data['events']:
        if not event:
            continue

        event_id = event.get('id', '?')
        event_name = event.get('name', 'unnamed')

        for page_idx, page in enumerate(event.get('pages', [])):
            for list_idx, item in enumerate(page.get('list', [])):
                code = item.get('code')
                params = item.get('parameters', [])

                # Códigos que contêm texto
                text_codes = [101, 401, 102, 108, 118, 320, 355, 655, 122, 356, 357]

                if code in text_codes:
                    texts.append({
                        'event_id': event_id,
                        'event_name': event_name,
                        'page': page_idx,
                        'list_idx': list_idx,
                        'code': code,
                        'parameters': params
                    })

    return texts


def find_text_differences(original_texts, translated_texts):
    """Encontra diferenças nos textos extraídos"""
    differences = []

    for orig, trans in zip(original_texts, translated_texts):
        if orig['parameters'] != trans['parameters']:
            differences.append({
                'event': f"Event {orig['event_id']} ({orig['event_name']})",
                'location': f"Page {orig['page']}, Item {orig['list_idx']}",
                'code': orig['code'],
                'original': orig['parameters'],
                'translated': trans['parameters']
            })

    return differences


def format_parameter(param):
    """Formata parâmetro para exibição"""
    if isinstance(param, str):
        # Limitar tamanho
        if len(param) > 100:
            return param[:100] + "..."
        return param
    elif isinstance(param, list):
        return f"[{len(param)} items]"
    elif isinstance(param, dict):
        return f"{{{len(param)} keys}}"
    else:
        return str(param)


def main():
    if len(sys.argv) < 3:
        print("Uso: python compare_json.py <arquivo_input> <arquivo_output>")
        print("\nExemplo:")
        print("  python compare_json.py input/Map021.json output/Map021.json")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    if not input_file.exists():
        print(f"❌ Arquivo não encontrado: {input_file}")
        sys.exit(1)

    if not output_file.exists():
        print(f"❌ Arquivo não encontrado: {output_file}")
        sys.exit(1)

    print("\n" + "="*80)
    print(f"COMPARAÇÃO: {input_file.name}")
    print("="*80)
    print(f"\nOriginal:  {input_file}")
    print(f"Traduzido: {output_file}")

    # Carregar JSONs
    print("\n⏳ Carregando arquivos JSON...")
    original = load_json(input_file)
    translated = load_json(output_file)

    # Comparar campos básicos
    print("\n" + "="*80)
    print("1. CAMPOS BÁSICOS DO MAPA")
    print("="*80)

    basic_fields = ['displayName', 'note', 'width', 'height']
    has_basic_diff = False

    for field in basic_fields:
        orig_val = original.get(field)
        trans_val = translated.get(field)

        if orig_val != trans_val:
            has_basic_diff = True
            print(f"\n{field}:")
            print(f"  Original:  {orig_val}")
            print(f"  Traduzido: {trans_val}")

    if not has_basic_diff:
        print("\n✓ Nenhuma diferença nos campos básicos")

    # Extrair e comparar textos de eventos
    print("\n" + "="*80)
    print("2. TEXTOS DE EVENTOS")
    print("="*80)

    print("\n⏳ Extraindo textos dos eventos...")
    original_texts = extract_event_texts(original)
    translated_texts = extract_event_texts(translated)

    print(f"\nTotal de textos encontrados:")
    print(f"  Original:  {len(original_texts)} itens")
    print(f"  Traduzido: {len(translated_texts)} itens")

    if len(original_texts) != len(translated_texts):
        print(f"\n⚠️ AVISO: Quantidade de textos difere!")

    print("\n⏳ Comparando textos...")
    text_diffs = find_text_differences(original_texts, translated_texts)

    if text_diffs:
        print(f"\n🔍 Encontradas {len(text_diffs)} diferenças:")
        print("\n" + "-"*80)

        for i, diff in enumerate(text_diffs[:50], 1):  # Mostrar primeiras 50
            print(f"\n#{i} - {diff['event']} - {diff['location']} (código {diff['code']})")
            print(f"\n  Original:")
            for j, param in enumerate(diff['original']):
                print(f"    [{j}] {format_parameter(param)}")

            print(f"\n  Traduzido:")
            for j, param in enumerate(diff['translated']):
                print(f"    [{j}] {format_parameter(param)}")

        if len(text_diffs) > 50:
            print(f"\n... e mais {len(text_diffs) - 50} diferenças (omitidas)")
    else:
        print("\n✓ Nenhuma diferença encontrada nos textos de eventos")

    # Buscar especificamente por AS_0088
    print("\n" + "="*80)
    print("3. BUSCA ESPECÍFICA: AS_0088")
    print("="*80)

    found_as0088 = []

    for text in translated_texts:
        params_str = str(text['parameters'])
        if 'AS_0088' in params_str:
            found_as0088.append(text)

    if found_as0088:
        print(f"\n✓ Encontrado {len(found_as0088)} ocorrência(s) de AS_0088:\n")

        for occurrence in found_as0088:
            print(f"  Event {occurrence['event_id']} ({occurrence['event_name']})")
            print(f"  Page {occurrence['page']}, Item {occurrence['list_idx']}")
            print(f"  Código: {occurrence['code']}")
            print(f"  Parâmetros: {occurrence['parameters']}")
            print()
    else:
        print("\n⚠️ AS_0088 não encontrado no arquivo traduzido")

    # Estatísticas finais
    print("="*80)
    print("RESUMO")
    print("="*80)

    print(f"\n✓ Campos básicos: {'COM diferenças' if has_basic_diff else 'SEM diferenças'}")
    print(f"✓ Textos de eventos: {len(text_diffs)} diferenças encontradas")
    print(f"✓ AS_0088: {len(found_as0088)} ocorrência(s)")

    # Comparação completa de estrutura (resumida)
    print("\n⏳ Comparando estrutura completa...")
    all_diffs = compare_values(original, translated)

    # Filtrar diferenças significativas (ignorar 'data' array)
    significant_diffs = [d for d in all_diffs if not d['path'].startswith('data[')]

    print(f"\nDiferenças estruturais (excluindo array 'data'): {len(significant_diffs)}")

    if significant_diffs and len(significant_diffs) <= 20:
        print("\nDiferenças encontradas:")
        for diff in significant_diffs[:20]:
            print(f"\n  Caminho: {diff['path']}")
            print(f"  Tipo: {diff['type']}")
            if diff['type'] == 'changed':
                print(f"  Original:  {format_parameter(diff['original'])}")
                print(f"  Traduzido: {format_parameter(diff['translated'])}")

    print("\n" + "="*80)
    print("Comparação concluída!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
