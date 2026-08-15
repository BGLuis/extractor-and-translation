"""
Duas proteções que, se quebrarem, corrompem o arquivo do jogo silenciosamente:
1. Tags HTML (<center>, <br>, tags customizadas do RPG Maker) precisam ser mascaradas
   antes de ir para o tradutor, senão o tradutor pode alterar/remover a tag.
2. import_file nunca pode escrever um JSON no disco sem antes validar que ele é
   serializável e recarregável (round-trip) - um dado inválido tem que levantar exceção
   antes de tocar o arquivo, não gerar um output/*.json corrompido.
"""
import json
import os
import shutil
import tempfile

import pytest

from src.extractor.BaseExtractor import BaseExtractor
from src.extractor.rpgmaker.RPGMakerExtractor import RPGMakerExtractor


HTML_CASES = [
    ("<center>Welcome to the game!</center>", "Tags <center> básicas"),
    ("<br>Line break test", "Tag auto-fechamento <br>"),
    ("<b>Bold text</b> and <i>italic</i>", "Múltiplas tags"),
    ("<wordWrap>Custom tag</wordWrap>", "Tag customizada RPG Maker"),
    ("<center>\\M[INFO_0001]</center>", "Tag + código de formato"),
    ("<img src='icon.png'>Image", "Tag com atributos"),
    ("<left>Left aligned</left>", "Tag de alinhamento"),
]


@pytest.fixture
def html_pattern():
    extractor = RPGMakerExtractor(None)
    patterns = extractor.get_mask_patterns()
    for p in patterns:
        if p.pattern.startswith(r'</?[a-zA-Z]'):
            return p
    pytest.fail("Padrão de máscara para tags HTML não encontrado em get_mask_patterns()")


@pytest.mark.parametrize("text,description", HTML_CASES)
def test_html_tags_are_matched_by_mask_pattern(html_pattern, text, description):
    assert html_pattern.findall(text), f"{description}: nenhuma tag detectada em {text!r}"


def test_import_file_writes_valid_json():
    temp_dir = tempfile.mkdtemp()
    try:
        valid_data = {"id": 1, "name": "Test", "items": [1, 2, 3], "nested": {"key": "value"}}
        BaseExtractor.import_file("valid.json", valid_data, temp_dir)

        file_path = os.path.join(temp_dir, "valid.json")
        assert os.path.exists(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded == valid_data
    finally:
        shutil.rmtree(temp_dir)


def test_import_file_rejects_non_serializable_data_before_writing():
    temp_dir = tempfile.mkdtemp()
    try:
        class CircularRef:
            def __init__(self):
                self.ref = self

        with pytest.raises(Exception):
            BaseExtractor.import_file("invalid.json", CircularRef(), temp_dir)

        # Nada deve ter sido escrito no disco quando a serialização falha.
        assert not os.path.exists(os.path.join(temp_dir, "invalid.json"))
    finally:
        shutil.rmtree(temp_dir)
