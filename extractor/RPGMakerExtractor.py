import json
import os
from extractor.BaseExtractor import BaseExtractor
import commun.TextsUtils as TextsUtils
import re


class RPGMakerExtractor(BaseExtractor):
    name = 'RPG Maker'
    files_types = ['json', 'rvdata2']
    _quotes = r'[\"|\']'
    # quote_extraction_pattern = re.compile(_quotes + '.*?' + _quotes)
    quote_extraction_pattern = re.compile('\'.*?\'|\".*?\"')
    tag_extraction_pattern = re.compile(r'<.*?>*?</.*?>')
    title_extraction_pattern = re.compile(r'<([^<>]*)>|<<([^<>]*)>>')

    @classmethod
    def get_interactive_questions(cls):
        return []

    def apply_configuration(self, config):
        pass

    def __init__(self, translate):
        super().__init__(translate)

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
        # r'note',
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
                        try:
                            int(remaining_text[-1].strip())
                        except ValueError:
                            if remaining_text[-1].strip().lower() in ['true', 'false']:
                                list_obj['text'].append(remaining_text)
                    else:
                        list_obj['text'].append(param)

        elif iten['code'] in RPGMakerExtractor._codes_fist_element_straction:
            if not RPGMakerExtractor.ignore_text(iten['parameters'][0]):
                list_obj['text'] = iten['parameters'][0]

        elif iten['code'] in RPGMakerExtractor._codes_funtion_straction:
            funtions = [
                "$gameVariables.setValue", "BattleManager._logWindow.push('addText'", "mes = \"", "text ="]
            for func in funtions:
                if iten['parameters'][0].startswith(func) and RPGMakerExtractor.quote_extraction_pattern.search(iten['parameters'][0]):
                    find = RPGMakerExtractor.quote_extraction_pattern.findall(iten['parameters'][0])
                    if find and len(find) == 2  and not RPGMakerExtractor.ignore_text(find[1]):
                        list_obj['text'] = find[1][1:-1]
                        break
                    elif find and len(find) == 1 and find[0][1:-1] != 'addText' and not RPGMakerExtractor.ignore_text(find[0]):
                        list_obj['text'] = find[0][1:-1]
                        break

            if re.search(r'\d_t=\d{2,}_subject=', iten['parameters'][0]):
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
                    iten['parameters'][4].startswith(("'", '"', '`')):
                list_obj['text'] = iten['parameters'][4][1:-1]

        elif iten['code'] in RPGMakerExtractor._codes_prefix_straction:
            for prefix in RPGMakerExtractor._prefixes:
                if re.match(prefix, iten['parameters'][0]):
                    split_result = re.split(f"{prefix} ", iten['parameters'][0], maxsplit=1)
                    if len(split_result) > 1:
                        find = split_result[1]
                        if find and not RPGMakerExtractor.ignore_text(find) and not re.findall(r'[a-zA-Z]{1,2}\[.*?\]', find):
                            if re.search(r'fs\[\d+\]', find):
                                list_obj['text'] = find
                            list_obj['text'] = find
                            break

        elif iten['code'] in RPGMakerExtractor._codes_fourth_element:
            if len(iten['parameters']) > 3 and \
                iten['parameters'][3]:
                if isinstance(iten['parameters'][3], dict):
                    if 'text' in iten['parameters'][3] and not RPGMakerExtractor.ignore_text(iten['parameters'][3]['text']):
                        list_obj['text'] = iten['parameters'][3]['text']

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
                        if len(text_obj['text']) > 0:
                            page_obj['list'].append(text_obj)
                    if len(page_obj['list']) > 0:
                        event['pages'].append(page_obj)
                if len(event['pages']) > 0:
                    text.append(event)
        return text

    @staticmethod
    def insert_text_map_item(iten, list_item):
        if iten['code'] in RPGMakerExtractor._codes_simple_straction:
            for iten_text, list_item_text in zip(iten['parameters'], list_item['text']):
                match = RPGMakerExtractor.title_extraction_pattern.search(iten_text)

                if match:
                    origin_title = [group for group in match.groups() if group][0]
                    new_title = match.group(0).replace(origin_title, list_item_text[0])
                    iten_text = iten_text.replace(
                        match.group(0),
                        new_title
                    )
                    iten_text = iten_text.split(new_title, 1)
                    iten_text = iten_text[0] + new_title + list_item_text[1]
                    iten['parameters'] = [iten_text]
                elif any(iten_text.startswith(key) for key in RPGMakerExtractor._text_keys):
                    iten_text = iten_text.split(":", 1)
                    if RPGMakerExtractor.is_string_numeric(iten_text[-1].strip()) and \
                            RPGMakerExtractor.is_string_numeric(list_item_text):
                        iten['parameters'] = iten_text[0].strip() + ":" + list_item_text
                else:
                    iten['parameters'] = [list_item_text]

        if iten['code'] in RPGMakerExtractor._codes_fist_element_straction:
            if not RPGMakerExtractor.ignore_text(iten['parameters'][0]):
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


            elif re.search(r'\d_t=\d{2,}_subject=', iten['parameters'][0]):
                text_parts = iten['parameters'][0].split('_subject=')
                text_to_insert = list_item["text"]
                if isinstance(text_to_insert, list):
                    text_to_insert = " ".join(text_to_insert)
                text_parts[1] = f'{text_to_insert}"'
                iten['parameters'][0] = '_subject='.join(text_parts)

        if iten['code'] in RPGMakerExtractor._codes_second_element_straction:
            iten['parameters'][1] = list_item['text']

        if iten['code'] in RPGMakerExtractor._codes_fifth_element_straction:
            iten['parameters'][4] = f'"{list_item["text"]}"'

        if iten['code'] in RPGMakerExtractor._codes_prefix_straction:
            for prefix in RPGMakerExtractor._prefixes:
                match = re.match(prefix, iten['parameters'][0])
                if match:
                    prefix_used = match.group(0)
                    iten['parameters'][0] = f'{prefix_used} {list_item["text"]}'
                    break

        if iten['code'] in RPGMakerExtractor._codes_fourth_element:
            if len(iten['parameters']) > 3 and \
                iten['parameters'][3] and isinstance(iten['parameters'][3], dict):
                if 'text' in iten['parameters'][3]:
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
                    if len(text_obj['text']) > 0:
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
                        if len(text_obj['text']) > 0:
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
            if item and item['name'] != '':
                obj = {'id': item['id']}
                for key in item.keys():
                    if any(re.match(pattern, key) for pattern in RPGMakerExtractor._attributes_find) and not RPGMakerExtractor.ignore_text(item[key]):
                        obj[key] = item[key]
                text.append(obj)
        return text

    @staticmethod
    def insert_text_object(new_json, new_data):
        for texts in new_data:
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
                    for i,item in enumerate(value):
                        if (isinstance(new_json[key][i], str) and
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
    def fix_text_translate(texts):
        texts_list = TextsUtils.dictToList(texts)

        patterns = [
            (r'\\ ', lambda m: m.group(0).replace(' ', '')),
            (r'\ [\[\(]', lambda m: m.group(0).replace(' ', '').lower()),
            (r'(?i)\bif \(', lambda m: m.group(0).replace(' ', '').lower()),
            (r'\bif[\(].*?[\)]', lambda m: m.group(0).replace(' ', '')),
            (r'\b \-\b', lambda m: m.group(0).replace(' ', '')),
            (r'\" \"', lambda m: m.group(0).replace('\" \"', '\"')),
            (r'\\n ', lambda m: m.group(0).replace(' ', '')),
            (r' ?_ ?', lambda m: m.group(0).replace(' ', '')),
            (r'\<*?\>', lambda m: m.group(0).replace(' ', '')),
            (r'\$ ', lambda m: m.group(0).replace(' ', '')),
            (r'\> \=', lambda m: m.group(0).replace(' ', '')),
            (r'\< \=', lambda m: m.group(0).replace(' ', '')),
            (r'\! \=', lambda m: m.group(0).replace(' ', '')),
            (r'\= \=', lambda m: m.group(0).replace(' ', '')),
            (r'[a-zA-Z]{1,2}\[', lambda m: m.group(0).upper()),
            (r'V\[', lambda m: m.group(0).lower()),
            (r'(\$game)([a-z])', lambda m: m.group(1) + m.group(2).upper()),
        ]

        for i,text in enumerate(texts_list):
            for pattern, repl in patterns:
                text = re.sub(pattern, repl, text)
            texts_list[i] = text

        TextsUtils.interactive_item(texts, texts_list)
