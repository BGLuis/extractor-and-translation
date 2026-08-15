import unittest
import json
import os
import sys

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extractor.rpgmaker import RPGMakerExtractor

class TestRPGMakerExtractorRefactor(unittest.TestCase):
    def setUp(self):
        self.extractor = RPGMakerExtractor(None)

    def test_extract_show_text(self):
        # Código 401: Show Text
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 401, "parameters": ["Olá Mundo!"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['pages'][0]['list'][0]['text'], "Olá Mundo!")

    def test_extract_script_call_safe(self):
        # Código 355: Script Call - Casos SEGUROS (Lista Branca)
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 355, "parameters": ["$gameMessage.add(\"Texto para traduzir\")"], "indent": 0},
                                {"code": 655, "parameters": ["$gameMessage.add('Outro texto')"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        # Atualmente a implementação atual PODE falhar ou extrair errado dependendo da regex
        # Vamos ver o que ela faz hoje.
        texts = []
        for event in result:
            for page in event['pages']:
                for item in page['list']:
                    if isinstance(item['text'], str):
                        texts.append(item['text'])
                    elif isinstance(item['text'], list):
                        texts.extend(item['text'])
        
        # A implementação atual usa startsWith("functions") que inclui $gameVariables.setValue mas não $gameMessage.add explicitamente no array hardcoded (ela tem BattleManager._logWindow.push)
        # Vamos verificar se ela extrai.
        self.assertIn("Texto para traduzir", str(result))

    def test_extract_script_call_unsafe_should_ignore(self):
        # Código 355: Script Call - Casos INSEGUROS (Devem ser ignorados)
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 355, "parameters": ["this.character(0).setStepAnime(true)"], "indent": 0},
                                {"code": 355, "parameters": ["$gameScreen.showPicture(1, 'Actor1_1', 0, 0, 0, 100, 100, 255, 0)"], "indent": 0},
                                {"code": 355, "parameters": ["var x = 'local_variable'"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        
        # Atualmente a implementação atual usa quote_extraction_pattern que PEGA 'Actor1_1' e 'local_variable'
        # se eles não estiverem no ignore_text.
        extracted_texts = []
        if result:
            for event in result:
                for page in event['pages']:
                    for item in page['list']:
                        if isinstance(item['text'], str):
                            extracted_texts.append(item['text'])
        
        # Isso é o que queremos EVITAR com a refatoração
        # Por enquanto, vamos apenas documentar o que acontece
        print(f"\nTextos extraídos indevidamente (Script): {extracted_texts}")

    def test_extract_plugin_command_mz_safe_only(self):
        # Código 357: MZ Plugin Command
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {
                                    "code": 357, 
                                    "parameters": [
                                        "PluginName", "CommandName", "Label",
                                        {
                                            "text": "Texto Real",
                                            "image": "img/faces/Actor1",
                                            "switchId": 10,
                                            "description": "Descrição do item"
                                        }
                                    ], 
                                    "indent": 0
                                },
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        
        # Queremos que "Texto Real" e "Descrição do item" sejam extraídos.
        # "image" e "switchId" devem ser ignorados.
        extracted_dict = {}
        if result:
            for event in result:
                for page in event['pages']:
                    for item in page['list']:
                        if isinstance(item['text'], dict):
                            extracted_dict.update(item['text'])
        
        self.assertIn("text", extracted_dict)
        self.assertIn("description", extracted_dict)
        self.assertNotIn("image", extracted_dict)
        self.assertNotIn("switchId", extracted_dict)

    def test_extract_control_variables(self):
        # Código 122: Control Variables - O 5º parâmetro pode ser uma string (Script)
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 122, "parameters": [1, 1, 0, 4, "Script de Texto"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        self.assertEqual(result[0]['pages'][0]['list'][0]['text'], "Script de Texto")

    def test_extract_change_name(self):
        # Código 320: Change Actor Name - O 2º parâmetro é o novo nome
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 320, "parameters": [1, "Novo Nome"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        self.assertEqual(result[0]['pages'][0]['list'][0]['text'], "Novo Nome")

    def test_insert_control_variables(self):
        # Código 122: Control Variables
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 122, "parameters": [1, 1, 0, 4, "Texto Antigo"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        translated_data = [
            {
                "id": 1,
                "pages": [
                    {
                        "id": 0,
                        "list": [
                            {"id": 0, "text": "Texto Novo"}
                        ]
                    }
                ]
            }
        ]
        updated_json = self.extractor.update_json("Map001.json", data, translated_data)
        # O 5º parâmetro (índice 4) deve ser atualizado
        self.assertEqual(updated_json['events'][1]['pages'][0]['list'][0]['parameters'][4], "Texto Novo")

    def test_extract_choice_branch(self):
        # Código 402: texto de uma ramificação de escolha (ex: "Attack") precisa ser
        # traduzido - antes desta correção, ChoiceBranchStrategy existia mas nunca era
        # registrada em _strategies, então nada era extraído para o código 402.
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 402, "parameters": [0, "Attack"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        self.assertEqual(result[0]['pages'][0]['list'][0]['text'], "Attack")

    def test_extract_change_nickname_and_profile(self):
        # Códigos 324/325: mesmo formato de CHANGE_NAME ([actorId, texto]). Apelido e
        # perfil do ator são texto visível ao jogador, então precisam de tradução.
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 324, "parameters": [1, "Apelido Novo"], "indent": 0},
                                {"code": 325, "parameters": [1, "Perfil Novo"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        texts = [item['text'] for item in result[0]['pages'][0]['list']]
        self.assertIn("Apelido Novo", texts)
        self.assertIn("Perfil Novo", texts)

    def test_extract_label_is_not_translated(self):
        # Código 118: label é um identificador interno de salto (ex: "loop_start"),
        # não texto de jogador - deve continuar sem extrair nada, de propósito.
        data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "id": 0,
                            "list": [
                                {"code": 118, "parameters": ["loop_start"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 0}
                            ]
                        }
                    ]
                }
            ]
        }
        result = self.extractor.extract_text("Map001.json", data)
        self.assertEqual(result, [])

    def test_note_tag_round_trip_preserves_tag_name(self):
        # _note_tag_pattern tinha um bug de agrupamento: o "<" só ficava preso à
        # primeira alternativa, então o grupo 1 (nome da tag) vinha com "<Desc" para
        # a tag Desc, quebrando a reconstrução em insert_text_object.
        note = "Item raro. <Desc: A rare sword> <InfoRarity: Legendary>"
        data = [None, {"id": 1, "name": "Sword", "note": note}]

        extracted = self.extractor.extract_text_object(data)
        self.assertEqual(extracted[0]['note'], {"Desc": "A rare sword", "InfoRarity": "Legendary"})

        self.extractor.insert_text_object(
            data, [{"id": 1, "note": {"Desc": "Uma espada rara", "InfoRarity": "Lendário"}}]
        )
        self.assertIn("<Desc: Uma espada rara>", data[1]['note'])
        self.assertIn("<InfoRarity: Lendário>", data[1]['note'])

if __name__ == '__main__':
    unittest.main()
