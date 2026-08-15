#!/usr/bin/env python3
"""
Script para analisar detalhadamente um código específico em arquivos JSON
"""

import json
import sys
from pathlib import Path


def analyze_message_code(input_file, output_file, search_code):
    """Analisa um código de mensagem específico (ex: AS_0088)"""

    with open(input_file, 'r', encoding='utf-8') as f:
        original = json.load(f)

    with open(output_file, 'r', encoding='utf-8') as f:
        translated = json.load(f)

    print("\n" + "="*80)
    print(f"ANÁLISE DETALHADA: {search_code}")
    print("="*80)

    # Buscar no input
    print(f"\n📄 ARQUIVO INPUT: {input_file}")
    print("-"*80)

    input_occurrences = find_code_occurrences(original, search_code)

    if input_occurrences:
        print(f"\n✓ Encontrado {len(input_occurrences)} ocorrência(s):\n")
        for occ in input_occurrences:
            print_occurrence(occ)
    else:
        print(f"\n⚠️ Código '{search_code}' NÃO encontrado no input")

    # Buscar no output
    print(f"\n📄 ARQUIVO OUTPUT: {output_file}")
    print("-"*80)

    output_occurrences = find_code_occurrences(translated, search_code)

    if output_occurrences:
        print(f"\n✓ Encontrado {len(output_occurrences)} ocorrência(s):\n")
        for occ in output_occurrences:
            print_occurrence(occ)
    else:
        print(f"\n⚠️ Código '{search_code}' NÃO encontrado no output")

    # Comparação
    print("\n" + "="*80)
    print("COMPARAÇÃO")
    print("="*80)

    if len(input_occurrences) != len(output_occurrences):
        print(f"\n⚠️ DIFERENÇA NA QUANTIDADE:")
        print(f"   Input:  {len(input_occurrences)} ocorrência(s)")
        print(f"   Output: {len(output_occurrences)} ocorrência(s)")
    else:
        print(f"\n✓ Quantidade idêntica: {len(input_occurrences)} ocorrência(s)")

        if input_occurrences and output_occurrences:
            print("\n🔍 Comparando detalhes:")

            for i, (inp, out) in enumerate(zip(input_occurrences, output_occurrences), 1):
                print(f"\n  Ocorrência #{i}:")

                if inp['event_id'] != out['event_id']:
                    print(f"    ⚠️ Event ID diferente: {inp['event_id']} → {out['event_id']}")
                else:
                    print(f"    ✓ Event ID: {inp['event_id']}")

                if inp['code'] != out['code']:
                    print(f"    ⚠️ Código diferente: {inp['code']} → {out['code']}")
                else:
                    print(f"    ✓ Código: {inp['code']}")

                if inp['full_text'] != out['full_text']:
                    print(f"    ⚠️ Texto diferente:")
                    print(f"       Input:  {inp['full_text']}")
                    print(f"       Output: {out['full_text']}")
                else:
                    print(f"    ✓ Texto idêntico: {inp['full_text']}")

    # Verificar se há referência ao CSV externo
    print("\n" + "="*80)
    print("ANÁLISE DO PADRÃO \\M[...]")
    print("="*80)

    if search_code.startswith(('INFO_', 'AS_', 'NPC_', 'NAME_')):
        print(f"\n✓ '{search_code}' é uma referência a mensagem externa")
        print(f"  Este código deve estar definido em: input/Mgp_ExternMessage.csv")
        print(f"\n  O padrão \\M[{search_code}] significa:")
        print(f"  - \\M = código de formato RPG Maker para mensagens externas")
        print(f"  - [{search_code}] = ID da mensagem no CSV")

        # Tentar ler o CSV
        csv_file = Path('input/Mgp_ExternMessage.csv')
        if csv_file.exists():
            print(f"\n  📂 Verificando {csv_file}...")

            # Tentar diferentes encodings
            encodings = ['utf-8', 'shift-jis', 'cp932', 'utf-8-sig', 'latin-1']

            for encoding in encodings:
                try:
                    with open(csv_file, 'r', encoding=encoding) as f:
                        for line in f:
                            if line.startswith(search_code):
                                content = line.split(',', 1)[1].strip() if ',' in line else line
                                print(f"\n  ✓ ENCONTRADO no CSV (encoding: {encoding}):")
                                print(f"    {search_code},{content[:200]}...")
                                break
                        else:
                            continue
                        break
                except (UnicodeDecodeError, Exception) as e:
                    if encoding == encodings[-1]:
                        print(f"\n  ⚠️ Erro ao ler CSV: {e}")
                    continue
            else:
                print(f"\n  ⚠️ '{search_code}' não encontrado no CSV ou erro de leitura")
        else:
            print(f"\n  ⚠️ Arquivo CSV não encontrado: {csv_file}")

    print("\n" + "="*80)


def find_code_occurrences(data, search_code):
    """Busca todas as ocorrências de um código nos eventos"""
    occurrences = []

    if 'events' not in data:
        return occurrences

    for event in data['events']:
        if not event:
            continue

        event_id = event.get('id', '?')
        event_name = event.get('name', 'unnamed')

        for page_idx, page in enumerate(event.get('pages', [])):
            for list_idx, item in enumerate(page.get('list', [])):
                code = item.get('code')
                params = item.get('parameters', [])

                # Verificar se o código aparece nos parâmetros
                params_str = str(params)
                if search_code in params_str:
                    occurrences.append({
                        'event_id': event_id,
                        'event_name': event_name,
                        'page': page_idx,
                        'list_idx': list_idx,
                        'code': code,
                        'parameters': params,
                        'full_text': params_str
                    })

    return occurrences


def print_occurrence(occ):
    """Imprime detalhes de uma ocorrência"""
    print(f"  🎯 Event {occ['event_id']}: {occ['event_name']}")
    print(f"     Localização: Page {occ['page']}, Item #{occ['list_idx']}")
    print(f"     Código evento: {occ['code']}")
    print(f"     Parâmetros ({len(occ['parameters'])} item(s)):")

    for i, param in enumerate(occ['parameters']):
        if isinstance(param, str):
            print(f"       [{i}] {param}")
        else:
            print(f"       [{i}] {type(param).__name__}: {param}")
    print()


def main():
    if len(sys.argv) < 4:
        print("Uso: python analyze_code.py <input_file> <output_file> <search_code>")
        print("\nExemplo:")
        print("  python analyze_code.py input/Map021.json output/Map021.json AS_0088")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    search_code = sys.argv[3]

    if not input_file.exists():
        print(f"❌ Arquivo não encontrado: {input_file}")
        sys.exit(1)

    if not output_file.exists():
        print(f"❌ Arquivo não encontrado: {output_file}")
        sys.exit(1)

    analyze_message_code(input_file, output_file, search_code)

    print("\nAnálise concluída!\n")


if __name__ == "__main__":
    main()
