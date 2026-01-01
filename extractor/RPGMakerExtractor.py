import json
import os
from extractor.BaseExtractor import BaseExtractor
import commun.TextsUtils as TextsUtils
import re
import logging


class RPGMakerExtractor(BaseExtractor):
    name = 'RPG Maker'
    files_types = ['json', 'rvdata2']
    _quotes = r'[\"|\']'
    quote_extraction_pattern = re.compile(r"'.*?'|\".*?\"")
    tag_extraction_pattern = re.compile(r'<.*?>*?</.*?>')
    title_extraction_pattern = re.compile(r'<([^<>]*)>|<<([^<>]*)>>')

    _note_tag_pattern = re.compile(fr'(<{re.escape("Desc")}|{re.escape("Help")}|{re.escape("Text")}|{re.escape("Profile")}|{re.escape("Message")}|{re.escape("Info")}[^:>]*):\s*([^>]+)>', re.IGNORECASE)

    _choice_condition_pattern = re.compile(r'^(?:if|show_if|hide_if|en|pt|ja|es|fr)\s*\(.*?\)\s*', re.IGNORECASE)

    _variable_pattern = re.compile(r'[a-zA-Z]{1,2}\[.*?\]')
    _subject_pattern = re.compile(r'\d_t=\d{2,}_subject=')
    _fs_pattern = re.compile(r'fs\[\d+\]')

    @classmethod
    def get_interactive_questions(cls):
        return []

    def apply_configuration(self, config):
        pass

    def __init__(self, translate):
        super().__init__(translate)

    def get_mask_patterns(self, file_name=None, data=None):
        """
        Retorna uma lista de padrões compilados (re.Pattern) para mascaramento
        de tokens técnicos antes da tradução.
        """
        p_format_codes = re.compile(r'\\[A-Za-z]{1,3}\s*\[[^\]]*\]', re.IGNORECASE)

        game_keys = ['variables', 'switches', 'party', 'actors', 'player', 'map', 'system', 'screen', 'timer', 'message', 'temp', 'troop', 'interpreter']
        p_game = re.compile(r'\$game(' + '|'.join(game_keys) + r')\b', re.IGNORECASE)

        p_bracket_vars = re.compile(r'!?(?<!\\)\b[A-Za-z]{1,2}\s*\[\s*\d+\s*\]', re.IGNORECASE)

        p_if_condition = re.compile(r'if\s*\(\s*!?\s*[A-Za-z]{1,2}\s*\[\s*\d+\s*\]\s*\)', re.IGNORECASE)

        p_lang_wrapper = re.compile(r'\b(?:en|pt|ja|es|fr)\s*\([^)]+\)', re.IGNORECASE)

        p_boolean_literals = re.compile(r'\b(?:true|false|null|undefined|NaN)\b', re.IGNORECASE)

        p_operators = re.compile(r'(?:&&|\|\||>=|<=|!==|===|!=|==)')

        p_dollar_camel = re.compile(r'\$\s*[a-z]+[A-Z][a-zA-Z]*')

        return [p_format_codes, p_game, p_bracket_vars, p_if_condition, p_lang_wrapper, p_boolean_literals, p_operators, p_dollar_camel]

    _codes_simple_straction = [401, 405, 408, 108, 118]
    _codes_fist_element_straction = [102]
    _codes_funtion_straction = [355, 655]
    _codes_second_element_straction = [320]
    _codes_fifth_element_straction = [122, 101]
    _codes_prefix_straction = [356]
    _codes_fourth_element=[357]

    _codes_find = (
        _codes_simple_straction +
        _codes_fist_element_straction +
        _codes_funtion_straction +
        _codes_second_element_straction +
        _codes_fifth_element_straction +
        _codes_prefix_straction +
        _codes_fourth_element
    )

    _prefixes = [
        "D_TEXT",
        "addLog",
        r"InformationWindow \d+ Text:",
        "mes ="
    ]

    _compiled_prefixes = [re.compile(prefix) for prefix in _prefixes]

    _text_keys = [
        "icon:",
        "secret:",
        "title:",
        "name:",
        "text:",
        "message:",
        "text1:",
        "text2:",
        "secretText:",
        "id:"
    ]

    _attributes_find = [
        r'name',
        r'note',
        r'profile',
        r'description',
        r'nickname',
        r'message\d{1}'
    ]
    _attributes_system_find = [
        'armorTypes',
        'equipTypes',
        'gameTitle',
        'skillTypes',
        'terms',
        'switches'
    ]

    @staticmethod
    def is_string_numeric(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_string_boolean(string):
        return string.lower() in ['true', 'false']

    @staticmethod
    def ignore_text(text):
        ignore_prefixes = [
            "$", "D_TEXT", "\"+", "\'+", "voice_", "ChoiceVariableId", "PLM", "\"00",
            "let result", "const ", "var ", "this.", "return", "if", "else", "while", "for", "function", "=>",
            "new ", "class ", "extends ", "super(", "import ", "export ", "async ", "await ",
            "try", "catch", "finally", "{", "}", "[", "]", "!", "false", "true", "null", "undefined", "NaN",
        ]

        ignore_param = [
            "&&", "||", "==", "!=", "===", "!==", "$gamevariables.value", "Math."
        ]
        if isinstance(text, str):
            if text == '':
                return True

            if any(text.startswith(prefix) for prefix in ignore_prefixes):
                return True

            if any(param in text for param in ignore_param):
                return True
        elif isinstance(text, list):
            if all(isinstance(item, str) and any(item.startswith(prefix) for prefix in ignore_prefixes) for item in
                   text):
                return True
            elif any(isinstance(item, str) and param in item for item in text for param in ignore_param):
                return True

        return False

    @staticmethod
    def extarctor_text_codes_item(iten, i):
        list_obj = {"id": i, "text": []}

        if iten['code'] in RPGMakerExtractor._codes_simple_straction:
            for param in iten['parameters']:
                if not RPGMakerExtractor.ignore_text(param):
                    title_match = RPGMakerExtractor.title_extraction_pattern.search(param)
                    if title_match:
                        groups = [group for group in title_match.groups() if group]
                        if groups:
                            title = groups[0]
                            text = param[title_match.end():].strip()
                            if text and not RPGMakerExtractor.ignore_text(title):
                                list_obj['text'].append([title, text])
                    elif any(param.startswith(key) for key in RPGMakerExtractor._text_keys):
                        remaining_text = param.split(":", 1)[-1].strip()
                        if (remaining_text and
                            not RPGMakerExtractor.is_string_numeric(remaining_text) and
                            not RPGMakerExtractor.is_string_boolean(remaining_text)):
                            list_obj['text'].append(remaining_text)
                    else:
                        list_obj['text'].append(param)

        elif iten['code'] in RPGMakerExtractor._codes_fist_element_straction:
            if not RPGMakerExtractor.ignore_text(iten['parameters'][0]):
                cleaned_choices = []
                for choice in iten['parameters'][0]:
                    choice = choice.strip()
                    match = RPGMakerExtractor._choice_condition_pattern.match(choice)
                    if match:
                        cleaned_choices.append(choice[match.end():])
                    else:
                        cleaned_choices.append(choice)
                list_obj['text'] = cleaned_choices

        elif iten['code'] in RPGMakerExtractor._codes_funtion_straction:
            funtions = [
                "$gameVariables.setValue", "BattleManager._logWindow.push('addText'", "mes = \"", "text ="
            ]
            for func in funtions:
                if iten['parameters'][0].startswith(func) and RPGMakerExtractor.quote_extraction_pattern.search(iten['parameters'][0]):
                    find = RPGMakerExtractor.quote_extraction_pattern.findall(iten['parameters'][0])
                    if find and len(find) == 2  and not RPGMakerExtractor.ignore_text(find[1]):
                        list_obj['text'] = find[1][1:-1]
                        break
                    elif find and len(find) == 1 and find[0][1:-1] != 'addText' and not RPGMakerExtractor.ignore_text(find[0]):
                        list_obj['text'] = find[0][1:-1]
                        break

            if RPGMakerExtractor._subject_pattern.search(iten['parameters'][0]):
                extract_text = iten['parameters'][0][1:-1].split('_subject=')[1]
                if not RPGMakerExtractor.ignore_text(extract_text):
                    list_obj['text'] = extract_text

        elif iten['code'] in RPGMakerExtractor._codes_second_element_straction:
            if not RPGMakerExtractor.ignore_text(iten['parameters'][1]):
                list_obj['text'] = iten['parameters'][1]

        elif iten['code'] in RPGMakerExtractor._codes_fifth_element_straction:
            if len(iten['parameters']) > 4 and \
                iten['parameters'][4] and isinstance(iten['parameters'][4], str) and \
                not RPGMakerExtractor.ignore_text(iten['parameters'][4]) and \
                not RPGMakerExtractor.is_string_numeric(iten['parameters'][4]) and \
                not RPGMakerExtractor.is_string_boolean(iten['parameters'][4]) and \
                    (iten['parameters'][4].startswith(("'", '"', '`')) or iten['code'] == 101):

                val = iten['parameters'][4]
                if val.startswith(("'", '"', '`')):
                     list_obj['text'] = val[1:-1]
                else:
                     list_obj['text'] = val

        elif iten['code'] in RPGMakerExtractor._codes_prefix_straction:
            for compiled_prefix in RPGMakerExtractor._compiled_prefixes:
                match = compiled_prefix.match(iten['parameters'][0])
                if match:
                    prefix_used = match.group(0)
                    split_result = iten['parameters'][0].split(prefix_used + " ", 1)
                    if len(split_result) > 1:
                        find = split_result[1]
                        if find and not RPGMakerExtractor.ignore_text(find) and not RPGMakerExtractor._variable_pattern.findall(find):
                            list_obj['text'] = find
                            break

        elif iten['code'] in RPGMakerExtractor._codes_fourth_element:
            if len(iten['parameters']) > 3 and \
                iten['parameters'][3]:
                if isinstance(iten['parameters'][3], dict):
                    extracted_params = {}
                    for p_key, p_val in iten['parameters'][3].items():
                        if isinstance(p_val, str) and not RPGMakerExtractor.ignore_text(p_val):
                            extracted_params[p_key] = p_val

                    if extracted_params:
                        if len(extracted_params) == 1 and 'text' in extracted_params:
                             list_obj['text'] = extracted_params['text']
                        else:
                             list_obj['text'] = extracted_params

        return list_obj

    @staticmethod
    def extarctor_text_map(new_json):
        text = []
        for item in new_json['events']:
            if item:
                event = {"id": item['id'], 'pages': []}
                for i, page in enumerate(item['pages']):
                    page_obj = {"id": i, "list": []}
                    for j, list_item in enumerate(page['list']):
                        text_obj = RPGMakerExtractor.extarctor_text_codes_item(list_item, j)
                        if text_obj.get('text') and len(text_obj['text']) > 0:
                            page_obj['list'].append(text_obj)
                    if len(page_obj['list']) > 0:
                        event['pages'].append(page_obj)
                if len(event['pages']) > 0:
                    text.append(event)
        return text

    @staticmethod
    def insert_text_map_item(iten, list_item):
        if iten['code'] in RPGMakerExtractor._codes_simple_straction:
            # Handle cases where list_item['text'] might be string (if manually edited) or list
            texts_to_insert = list_item['text']
            if isinstance(texts_to_insert, str):
                texts_to_insert = [texts_to_insert]

            if len(iten['parameters']) == 1 and len(texts_to_insert) >= 1:
                 iten_text = iten['parameters'][0]
                 new_text = texts_to_insert[0]
                 if isinstance(new_text, list):
                     new_text = new_text[1]

                 match = RPGMakerExtractor.title_extraction_pattern.search(iten_text)
                 if match:
                    origin_title = [group for group in match.groups() if group][0]
                    iten['parameters'][0] = iten_text.replace(iten_text[match.end():].strip(), str(new_text).strip())
                 elif any(iten_text.startswith(key) for key in RPGMakerExtractor._text_keys):
                    iten_text_parts = iten_text.split(":", 1)
                    if len(iten_text_parts) > 1:
                        iten['parameters'][0] = iten_text_parts[0] + ": " + str(new_text)
                 else:
                    iten['parameters'][0] = str(new_text)

            elif isinstance(texts_to_insert, list) and len(texts_to_insert) > 0:
                for iten_text, list_item_text in zip(iten['parameters'], texts_to_insert):
                    match = RPGMakerExtractor.title_extraction_pattern.search(iten_text)
                    if match:
                        origin_title = [group for group in match.groups() if group][0]
                        new_title = match.group(0).replace(origin_title, list_item_text[0])
                        iten_text = iten_text.replace(match.group(0), new_title)
                        iten_text = iten_text.split(new_title, 1)[0] + new_title + list_item_text[1]
                        iten['parameters'] = [iten_text]
                    else:
                        iten['parameters'] = [list_item_text]

        if iten['code'] in RPGMakerExtractor._codes_fist_element_straction:
            if not RPGMakerExtractor.ignore_text(iten['parameters'][0]):
                original_list = iten['parameters'][0]
                translated_list = list_item['text']

                if isinstance(translated_list, list) and len(original_list) == len(translated_list):
                    final_list = []
                    for orig, trans in zip(original_list, translated_list):
                        orig_clean = orig.strip()
                        match = RPGMakerExtractor._choice_condition_pattern.match(orig_clean)
                        if match:
                            prefix = match.group(0)
                            # Remover espaços finais do prefixo e iniciais do texto
                            # para garantir concatenação estrita se o original era assim
                            prefix = prefix.rstrip()
                            text_clean = str(trans).strip()
                            final_list.append(prefix + text_clean)
                        else:
                            final_list.append(str(trans).strip())
                    iten['parameters'][0] = final_list
                else:
                    iten['parameters'][0] = list_item['text']

        if iten['code'] in RPGMakerExtractor._codes_funtion_straction:
            if RPGMakerExtractor.quote_extraction_pattern.search(iten['parameters'][0]):
                text_to_insert = list_item["text"]
                if isinstance(text_to_insert, list):
                    text_to_insert = " ".join(text_to_insert)

                iten['parameters'][0] = re.sub(
                    RPGMakerExtractor.quote_extraction_pattern,
                    lambda m: f'\'{text_to_insert[::-1]}\'',
                    iten['parameters'][0][::-1],
                    count=1
                )[::-1]

            elif RPGMakerExtractor._subject_pattern.search(iten['parameters'][0]):
                text_parts = iten['parameters'][0].split('_subject=')
                text_to_insert = list_item["text"]
                if isinstance(text_to_insert, list):
                    text_to_insert = " ".join(text_to_insert)
                text_parts[1] = f'{text_to_insert}"'
                iten['parameters'][0] = '_subject='.join(text_parts)

        if iten['code'] in RPGMakerExtractor._codes_second_element_straction:
            iten['parameters'][1] = list_item['text']

        if iten['code'] in RPGMakerExtractor._codes_fifth_element_straction:
            val = iten['parameters'][4]
            if val and isinstance(val, str) and val.startswith(("'", '"', '`')):
                 iten['parameters'][4] = f'\"{list_item["text"]}"'
            else:
                 iten['parameters'][4] = list_item["text"]

        if iten['code'] in RPGMakerExtractor._codes_prefix_straction:
            for compiled_prefix in RPGMakerExtractor._compiled_prefixes:
                match = compiled_prefix.match(iten['parameters'][0])
                if match:
                    prefix_used = match.group(0)
                    iten['parameters'][0] = f'{prefix_used} {list_item["text"]}'
                    break

        if iten['code'] in RPGMakerExtractor._codes_fourth_element:
            # MZ Plugin Command insertion
            if len(iten['parameters']) > 3 and \
                iten['parameters'][3] and isinstance(iten['parameters'][3], dict):

                if isinstance(list_item['text'], dict):
                    # New generalized logic
                    for key, val in list_item['text'].items():
                        if key in iten['parameters'][3]:
                            iten['parameters'][3][key] = val
                elif 'text' in iten['parameters'][3] and isinstance(list_item['text'], str):
                    # Fallback legacy logic
                    iten['parameters'][3]['text'] = list_item['text']

    @staticmethod
    def insert_text_map(new_json, new_data):
        for texts in new_data:
            for page in texts['pages']:
                for list_item in page['list']:
                    value = new_json['events'][texts['id']]['pages'][page['id']]['list'][list_item['id']]
                    RPGMakerExtractor.insert_text_map_item(value, list_item)

    @staticmethod
    def extarctor_text_common_events(new_json):
        text = []
        for item in new_json:
            if item:
                event = {"id": item['id'], 'list': []}
                for i, list_item in enumerate(item['list']):
                    text_obj = RPGMakerExtractor.extarctor_text_codes_item(list_item, i)
                    if text_obj.get('text') and len(text_obj['text']) > 0:
                        event['list'].append(text_obj)
                if len(event['list']) > 0:
                    text.append(event)
        return text

    @staticmethod
    def insert_text_common_events(new_json, new_data):
        for texts in new_data:
            for list_item in texts['list']:
                value = new_json[texts['id']]['list'][list_item['id']]
                RPGMakerExtractor.insert_text_map_item(value, list_item)

    @staticmethod
    def extarctor_text_troops(new_json):
        text = []
        for item in new_json:
            if item:
                object = {"id": item['id'], 'pages': []}
                for i, page in enumerate(item['pages']):
                    page_obj = {"id": i, "list": []}
                    for j, list_item in enumerate(page['list']):
                        text_obj = RPGMakerExtractor.extarctor_text_codes_item(list_item, j)
                        if text_obj.get('text') and len(text_obj['text']) > 0:
                            page_obj['list'].append(text_obj)
                    if len(page_obj['list']) > 0:
                        object['pages'].append(page_obj)
                if len(object['pages']) > 0:
                    text.append(object)
        return text

    @staticmethod
    def insert_text_troops(new_json, new_data):
        for texts in new_data:
            for page in texts['pages']:
                for list_item in page['list']:
                    value = new_json[texts['id']]['pages'][page['id']]['list'][list_item['id']]
                    RPGMakerExtractor.insert_text_map_item(value, list_item)

    @staticmethod
    def extarctor_text_object(new_json):
        text = []
        for item in new_json:
            if item and item.get('name', '') != '':
                obj = {'id': item['id']}
                for key in item.keys():
                    # Check for standard attributes
                    if any(re.match(pattern, key) for pattern in RPGMakerExtractor._attributes_find):

                        # Special handling for 'note' to extract only tag contents
                        if key == 'note':
                            if item[key]:
                                matches = RPGMakerExtractor._note_tag_pattern.findall(item[key])
                                if matches:
                                    # Store matches as a dictionary {Tag: Content} for context
                                    # or simplified key for translation
                                    note_data = {}
                                    for tag, content in matches:
                                        note_data[tag] = content
                                    if note_data:
                                        obj[key] = note_data

                        elif not RPGMakerExtractor.ignore_text(item[key]):
                            obj[key] = item[key]

                if len(obj) > 1:
                    text.append(obj)
        return text

    @staticmethod
    def insert_text_object(new_json, new_data):
        for texts in new_data:
            # Handle Note reconstruction carefully
            if 'note' in texts and isinstance(texts['note'], dict):
                original_note = new_json[texts['id']].get('note', '')
                translated_notes = texts['note']

                for tag, new_content in translated_notes.items():
                    # Replace content for specific tag: <Tag: OldContent> -> <Tag: NewContent>
                    pattern = re.compile(fr'(<{re.escape(tag)}\s*:\s*)([^>]+)(>)', re.IGNORECASE)
                    original_note = pattern.sub(lambda m: f"{m.group(1)}{new_content}{m.group(3)}", original_note)

                new_json[texts['id']]['note'] = original_note
                # Remove note from texts to avoid overwriting by the generic update below if we want to be safe
                # But the generic update below does {**new_json... **texts}.
                # We need to update 'texts' to have the FULL note string now, or remove 'note' from 'texts'.
                # Simplest is to update 'texts' with the fully reconstructed string.
                texts['note'] = original_note

            new_json[texts['id']] = {**new_json[texts['id']],**texts}

    @staticmethod
    def extarctor_text_System(new_json):
        text = {}
        for key, value in new_json.items():
            if key in RPGMakerExtractor._attributes_system_find:
                text[key] = value
        return text

    @staticmethod
    def insert_text_System(new_json, new_data):
        for key, value in new_data.items():
            if key in RPGMakerExtractor._attributes_system_find:
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        if (i < len(new_json[key]) and
                            isinstance(new_json[key][i], str) and
                            RPGMakerExtractor.ignore_text(new_json[key][i])):
                            value[i] = new_json[key][i]
                new_json[key] = value

    extract_map = [
        {
            "files_name": [r'Map\d{3,}'],
            "findes": _codes_find,
            "extarctor": extarctor_text_map,
            "insert": insert_text_map,
        },
        {
            "files_name": [r'CommonEvents'],
            "findes": _codes_find,
            "extarctor": extarctor_text_common_events,
            "insert": insert_text_common_events,
        },
        {
            "files_name": [r'Troops'],
            "findes": _codes_find,
            "extarctor": extarctor_text_troops,
            "insert": insert_text_troops,
        },
        {
            "files_name": [r'MapInfos', r'Weapons', r'Items', r'Weapons', r'Skills', r'States', r'Enemies', r'Actors', r'Armors',],
            "findes": _attributes_find,
            "extarctor": extarctor_text_object,
            "insert": insert_text_object,
        },
        {
            "files_name": [r'System'],
            "findes": _attributes_system_find,
            "extarctor": extarctor_text_System,
            "insert": insert_text_System,
        }
    ]

    def extract_text(self, file_name, new_json):
        for item in RPGMakerExtractor.extract_map:
            for file_pattern in item['files_name']:
                if re.search(file_pattern, file_name):
                    return item['extarctor'](new_json)
        return None

    def update_json(self, file_name, new_json, new_data):
        for item in RPGMakerExtractor.extract_map:
            for file_pattern in item['files_name']:
                if re.search(file_pattern, file_name):
                    item['insert'](new_json, new_data)
                    return new_json
        return new_json

    @staticmethod
    def fix_text_translate(texts, original_texts=None):
        """
        Corrige textos traduzidos restaurando a capitalização correta de variáveis e código.
        """
        texts_list = TextsUtils.dictToList(texts)
        original_list = TextsUtils.dictToList(original_texts) if original_texts else None

        _format_codes_pattern = re.compile(
            r'\\([A-Za-z]{1,3})\s*(\[[^\]]*\])',
            re.IGNORECASE
        )

        _compiled_patterns = [
            (re.compile(r'\\\s+'), lambda m: '\\'),
            (re.compile(r'(?i)\bif\s*\('), lambda m: 'if('),
            (re.compile(r'"\s+"'), lambda m: '""'),
            (re.compile(r'\\n\s+'), lambda m: '\\n'),
            (re.compile(r'\s*_\s*'), lambda m: '_'),
            (re.compile(r'<\s*>'), lambda m: '<>'),
            (re.compile(r'\$\s+'), lambda m: '$'),
            (re.compile(r'>\s*='), lambda m: '>='),
            (re.compile(r'<\s*='), lambda m: '<='),
            (re.compile(r'!\s*='), lambda m: '!='),
            (re.compile(r'=\s*='), lambda m: '=='),
        ]

        _game_objects = {
            'variables': 'Variables',
            'switches': 'Switches',
            'party': 'Party',
            'actors': 'Actors',
            'player': 'Player',
            'map': 'Map',
            'system': 'System',
            'screen': 'Screen',
            'timer': 'Timer',
            'message': 'Message',
            'temp': 'Temp',
            'troop': 'Troop',
            'interpreter': 'Interpreter',
        }

        _game_pattern = re.compile(
            r'\$game(' + '|'.join(_game_objects.keys()) + r')\b',
            re.IGNORECASE
        )

        _property_pattern = re.compile(r'\.([_a-zA-Z][_a-zA-Z0-9]*)(?=[\[\(\.]|\s|$)')

        _code_pattern = re.compile(
            r'(\$\s*game\s*[a-zA-Z]+(?:\s*\.\s*[_a-zA-Z][_a-zA-Z0-9]*(?:\s*\[\s*[^\]]+\s*\])?)*|'
            r'\$\s*[a-z]+[A-Z][a-zA-Z]*|'
            r'!(?<!\\)\b[A-Za-z]{1,2}\s*\[\s*\d+\s*\]|'
            r'(?<!\\)(?<!!)\b[A-Za-z]{1,2}\s*\[\s*\d+\s*\])',
            re.IGNORECASE
        )

        for i, text in enumerate(texts_list):
            if not isinstance(text, str):
                continue

            original_text = original_list[i] if original_list and i < len(original_list) else None

            _format_upper = {'c', 'v', 'i', 'ce'}

            def fix_format_code(match):
                name = match.group(1)
                params = match.group(2)
                chosen = name.upper() if name.lower() in _format_upper else name.lower()
                return f'\\{chosen}{params}'

            text = _format_codes_pattern.sub(fix_format_code, text)

            for pattern, repl in _compiled_patterns:
                text = pattern.sub(repl, text)

            boolean_corrections = {
                r'\b(?:verdadeiro|verdadeira)\b': 'true',
                r'\b(?:falso|falsa)\b': 'false',
                r'\b(?:nulo|nula)\b': 'null',
                r'\bindefinido\b': 'undefined',
                r'\b(?:verdadero|verdadera)\b': 'true',
                r'\b(?:falso|falsa)\b': 'false',
                r'\bnulo\b': 'null',
                r'\bindefinido\b': 'undefined',
                r'\b(?:vrai|vraie)\b': 'true',
                r'\b(?:faux|fausse)\b': 'false',
                r'\bnul\b': 'null',
                r'\bindéfini\b': 'undefined',
            }

            for pattern, replacement in boolean_corrections.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

            if original_text:
                original_codes = {}
                for match in _code_pattern.finditer(original_text):
                    code = match.group(0)
                    key = re.sub(r'\s+', '', code).lower()
                    if key not in original_codes:
                        original_codes[key] = code

                def restore_original_code(match):
                    code = match.group(0)
                    key = re.sub(r'\s+', '', code).lower()

                    if '\\' in code:
                        try:
                            m_fmt = re.match(r'(!)?(\\)\s*([A-Za-z]{1,3})(\s*\[.*\])', code)
                            if m_fmt:
                                bang = m_fmt.group(1) or ''
                                name = m_fmt.group(3)
                                params = m_fmt.group(4) or ''
                                chosen = name.upper() if name.lower() in _format_upper else name.lower()
                                return f"{bang}\\{chosen}{params}"
                        except Exception:
                            pass

                    if key in original_codes:
                        return original_codes[key]

                    try:
                        def _norm_token(m):
                            bang = m.group(1) or ''
                            name = m.group(2)
                            num = m.group(3)
                            return f"{bang}{name}[{num}]"
                        code_clean = re.sub(r'(!)?([A-Za-z]{1,2})\s*\[\s*(\d+)\s*\]', _norm_token, code, flags=re.IGNORECASE)
                        return code_clean
                    except Exception:
                        return re.sub(r'\s+', '', code)

                if original_codes:
                    text = _code_pattern.sub(restore_original_code, text)

            def fix_game_object(match):
                obj_name = match.group(1).lower()
                return f'$game{_game_objects.get(obj_name, match.group(1))}'

            text = _game_pattern.sub(fix_game_object, text)

            if not original_text:
                def fix_property(match):
                    prop = match.group(1)
                    if prop.isupper() or (len(prop) > 1 and prop[0].isupper() and '_' in prop):
                        return '.' + prop.lower()
                    return match.group(0)

                text = _property_pattern.sub(fix_property, text)

            texts_list[i] = text

            try:
                code_triggers = ['if(', 'var ', 'return', '=>', 'function', 'mes =', 'text =']
                if any(t in text for t in code_triggers):
                    parts = re.split(r'(".*?"|\'.*?\')', text)
                    for j in range(len(parts)):
                        if j % 2 == 0:
                            parts[j] = re.sub(r'\b0+([1-9]\d*)\b', r'\1', parts[j])
                            parts[j] = re.sub(r'\b00+\b', '0', parts[j])
                    text = ''.join(parts)
                    texts_list[i] = text
            except Exception as e:
                logging.warning(f'Erro ao sanitizar literais octais: {e}')

        TextsUtils.interactive_item(texts, texts_list)
