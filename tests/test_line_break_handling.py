"""
fix_text_translate recebe qualquer string que a tradução automática devolveu, incluindo
combinações inesperadas de barra invertida e quebra de linha. Nenhuma dessas entradas pode
derrubar o processamento de um arquivo inteiro por uma exceção não tratada em regex.

Formaliza a investigação feita nos scripts de depuração test_fix.py / test_newline.py /
test_regex.py (raiz do projeto) para o item "Quebra de linha" do CheckList.md.
"""
import pytest

from src.extractor.rpgmaker.RPGMakerExtractor import RPGMakerExtractor

ADVERSARIAL_INPUTS = [
    r"\c[2]",
    r"if ( \v[1] )",
    r"\n ",
    r"\ ",
    r"hello \ world",
    "hello \\\\",
    "\\",
]


@pytest.mark.parametrize("text", ADVERSARIAL_INPUTS)
def test_fix_text_translate_does_not_raise_on_adversarial_backslashes(text):
    RPGMakerExtractor.fix_text_translate({"1": text}, {"1": text})
