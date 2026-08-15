"""
Códigos de formato do RPG Maker (\\M, \\V, \\C...) precisam sobreviver ao ciclo de
tradução com a capitalização original intacta: um \\m[INFO_0001] minúsculo é
silenciosamente ignorado pelo motor do jogo, então "\\M" virar "\\m" quebra a
mensagem no jogo real (caso documentado em FIX_FORMAT_CODES.md, Map010.json:1588).
"""
import pytest

from src.extractor.rpgmaker.RPGMakerExtractor import RPGMakerExtractor


UPPERCASE_CASES = [
    ("<center>\\m[INFO_0001]</center>", "<center>\\M[INFO_0001]</center>", "\\M (mensagem externa)"),
    ("Olá \\v[5]!", "Olá \\V[5]!", "\\V (variável)"),
    ("Cor \\c[2]azul\\c[0]", "Cor \\C[2]azul\\C[0]", "\\C (cor)"),
    ("Ícone \\i[10]", "Ícone \\I[10]", "\\I (ícone)"),
    ("Nome \\n[1]", "Nome \\N[1]", "\\N (nome do ator)"),
    ("Jogador \\p[2]", "Jogador \\P[2]", "\\P (personagem)"),
    ("Ouro \\g", "Ouro \\G", "\\G (moeda)"),
]

LOWERCASE_CASES = [
    ("Tamanho \\fs[24]", "Tamanho \\fs[24]", "\\fs (font size)"),
    ("Negrito \\b[on]", "Negrito \\b[on]", "\\b (bold)"),
]

MIXED_CASE = (
    "<center>\\m[INFO_0001] \\v[5] \\c[2]ouro\\c[0]</center>",
    "<center>\\M[INFO_0001] \\V[5] \\C[2]ouro\\C[0]</center>",
    "Múltiplos códigos",
)


@pytest.mark.parametrize("translated,expected,description", UPPERCASE_CASES + LOWERCASE_CASES + [MIXED_CASE])
def test_format_code_capitalization_is_restored(translated, expected, description):
    translated_list = [translated]
    RPGMakerExtractor.fix_text_translate(translated_list, [expected])
    assert translated_list[0] == expected, description


def test_map010_uppercase_M_regression():
    """Caso real do Map010.json: \\M não pode virar \\m mesmo sem contexto de código original."""
    original = "<center>\\M[INFO_0001]</center>"
    translated = "<center>\\m[INFO_0001]</center>"

    translated_list = [translated]
    RPGMakerExtractor.fix_text_translate(translated_list, [original])

    assert translated_list[0] == original
