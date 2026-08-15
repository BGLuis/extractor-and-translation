#!/usr/bin/env python3
"""
Verificação detalhada dos problemas encontrados nas comparações
"""
import json

print("="*80)
print("VERIFICAÇÃO DE PROBLEMAS NAS COMPARAÇÕES")
print("="*80)

# Problema 1: Map003 - switchTypeEX "A" sendo traduzido para "Um"
print("\n1. Map003.json - Verificando switchTypeEX")
with open('input/Map003.json', 'r', encoding='utf-8') as f:
    map003 = json.load(f)

# Event 1, page 1, list item 8 (código 357)
try:
    item = map003['events'][1]['pages'][1]['list'][8]
    if item['code'] == 357 and 'switchTypeEX' in item['parameters'][3]:
        print(f"   Event 1, Page 1, Item 8:")
        print(f"   switchTypeEX = '{item['parameters'][3]['switchTypeEX']}'")
        print(f"   ✓ Valor deve ser 'A' (não traduzir)")
except Exception as e:
    print(f"   ✗ Erro ao acessar: {e}")

# Problema 2: Map003 - \P[1] não desmascarado
print("\n2. Map003.json - Verificando \P[1]")
try:
    item = map003['events'][36]['pages'][0]['list'][2]
    if item['code'] == 101:
        print(f"   Event 36, Page 0, Item 2:")
        print(f"   parameters[4] = '{item['parameters'][4]}'")
        print(f"   ✓ Valor deve ser '\\P[1]' (não traduzir)")
except Exception as e:
    print(f"   ✗ Erro ao acessar: {e}")

# Problema 3: Map003 - "nochannel" e "end" traduzidos
print("\n3. Map003.json - Verificando nochannel/end")
try:
    item1 = map003['events'][46]['pages'][0]['list'][64]
    item2 = map003['events'][46]['pages'][0]['list'][71]
    if item1['code'] == 118:
        print(f"   Event 46, Page 0, Item 64:")
        print(f"   parameters[0] = '{item1['parameters'][0]}'")
        print(f"   ✓ Deve ser 'nochannel' (não traduzir)")
    if item2['code'] == 118:
        print(f"   Event 46, Page 0, Item 71:")
        print(f"   parameters[0] = '{item2['parameters'][0]}'")
        print(f"   ✓ Deve ser 'end' (não traduzir)")
except Exception as e:
    print(f"   ✗ Erro ao acessar: {e}")

# Problema 4: Map005 - Yes/No traduzidos
print("\n4. Map005.json - Verificando Yes/No")
with open('input/Map005.json', 'r', encoding='utf-8') as f:
    map005 = json.load(f)

try:
    item = map005['events'][4]['pages'][1]['list'][4]
    if item['code'] == 102:
        print(f"   Event 4, Page 1, Item 4:")
        print(f"   parameters[0] = {item['parameters'][0]}")
        print(f"   ✓ Deve ser ['Yes', 'No'] (não traduzir)")
except Exception as e:
    print(f"   ✗ Erro ao acessar: {e}")

# Problema 5: Map005 - \M[AS_0040] não desmascarado
print("\n5. Map005.json - Verificando \\M[AS_0040]")
try:
    item = map005['events'][13]['pages'][4]['list'][3]
    if item['code'] == 401:
        print(f"   Event 13, Page 4, Item 3:")
        print(f"   parameters[0] = '{item['parameters'][0]}'")
        print(f"   ✓ Deve ser '\\M[AS_0040]' (não traduzir)")
except Exception as e:
    print(f"   ✗ Erro ao acessar: {e}")

# Problema 6: Map010 - "No Change" traduzido
print("\n6. Map010.json - Verificando No Change")
with open('input/Map010.json', 'r', encoding='utf-8') as f:
    map010 = json.load(f)

try:
    item = map010['events'][1]['pages'][0]['list'][6]
    if item['code'] == 357 and 'WordWrap' in item['parameters'][3]:
        print(f"   Event 1, Page 0, Item 6:")
        print(f"   WordWrap = '{item['parameters'][3]['WordWrap']}'")
        print(f"   ✓ Deve ser 'No Change' (não traduzir)")
except Exception as e:
    print(f"   ✗ Erro ao acessar: {e}")

print("\n" + "="*80)
print("VERIFICAÇÃO COMPLETA")
print("="*80)
