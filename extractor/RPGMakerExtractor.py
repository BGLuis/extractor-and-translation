import json
import os
from extractor.BaseExtractor import BaseExtractor
import commun.TextsUtils as TextsUtils
import re


class RPGMakerExtractor(BaseExtractor):
    name = 'RPG Maker'
    files_types = ['json', 'rvdata2']
    _quotes = r'[\"|\']'
    quote_extraction_pattern = re.compile(_quotes + '.*?' + _quotes)

    def __init__(self, translate):
        super().__init__(translate)

    _codes_simple_straction = [401, 405, 408, 108, 118]
    _codes_fist_element_straction = [102]
    _codes_funtion_straction = [355, 655]
    _codes_second_element_straction = [320]
    _codes_fifth_element_straction = [122, 101]
    _codes_prefix_straction = [356]

    _codes_find = (
        _codes_simple_straction +
        _codes_fist_element_straction +
        _codes_funtion_straction +
        _codes_second_element_straction +
        _codes_fifth_element_straction +
        _codes_prefix_straction
    )

    _prefixes = [
        "D_TEXT",
        "addLog",
        r"InformationWindow \d+ Text:"
    ]

    _attributes_find = [
        r'name',
        r'note',
        r'profile',
        r'description',
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

    def ignore_text(text):
        ignore_prefixes = ["$", "D_TEXT"]
        if isinstance(text, str) and any(text.startswith(prefix) for prefix in ignore_prefixes):
            return True
        return False

    def extarctor_text_codes_item(iten, i):
        list_obj = {"id": i, "text": []}
        if iten['code'] in RPGMakerExtractor._codes_simple_straction:
            if not RPGMakerExtractor.ignore_text(iten['parameters']):
                list_obj['text'] = iten['parameters']

        elif iten['code'] in RPGMakerExtractor._codes_fist_element_straction:
            if not RPGMakerExtractor.ignore_text(iten['parameters'][0]):
                list_obj['text'] = iten['parameters'][0]

        elif iten['code'] in RPGMakerExtractor._codes_funtion_straction:
            funtions = ["$gameVariables.setValue", "BattleManager._logWindow.push('addText'"]
            for func in funtions:
                if iten['parameters'][0].startswith(func) and RPGMakerExtractor.quote_extraction_pattern.search(iten['parameters'][0]):
                    find = RPGMakerExtractor.quote_extraction_pattern.findall(iten['parameters'][0])[0]
                    if find and not RPGMakerExtractor.ignore_text(find):
                        list_obj['text'] = find
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
                not RPGMakerExtractor.ignore_text(iten['parameters'][4]):
                list_obj['text'] = iten['parameters'][4][1:-1]

        elif iten['code'] in RPGMakerExtractor._codes_prefix_straction:
            for prefix in RPGMakerExtractor._prefixes:
                if re.match(prefix, iten['parameters'][0]):
                    split_result = re.split(f"{prefix} ", iten['parameters'][0], maxsplit=1)
                    if len(split_result) > 1:
                        find = split_result[1]
                        if find and not RPGMakerExtractor.ignore_text(find):
                            list_obj['text'] = find
                            break

        return list_obj

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

    def insert_text_map_item(iten, list_item):
        if iten['code'] in RPGMakerExtractor._codes_simple_straction:
            iten['parameters'] = list_item['text']

        if iten['code'] in RPGMakerExtractor._codes_fist_element_straction:
            iten['parameters'][0] = list_item['text']

        if iten['code'] in RPGMakerExtractor._codes_funtion_straction:
            if RPGMakerExtractor.quote_extraction_pattern.search(iten['parameters'][0]):
                iten['parameters'][0] = re.sub(
                    RPGMakerExtractor._quotes + '.*?' + RPGMakerExtractor._quotes,
                    f'"{list_item["text"]}"',
                    iten['parameters'][0]
                )
            elif re.search(r'\d_t=\d{2,}_subject=', iten['parameters'][0]):
                text_parts = iten['parameters'][0].split('_subject=')
                text_parts[1] = f'{list_item["text"]}"'
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

    def insert_text_map(new_json, new_data):
        for texts in new_data:
            for page in texts['pages']:
                for list_item in page['list']:
                    value = new_json['events'][texts['id']]['pages'][page['id']]['list'][list_item['id']]
                    RPGMakerExtractor.insert_text_map_item(value, list_item)

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

    def insert_text_common_events(new_json, new_data):
        for texts in new_data:
            for list_item in texts['list']:
                value = new_json[texts['id']]['list'][list_item['id']]
                RPGMakerExtractor.insert_text_map_item(value, list_item)

    def extarctor_text_troops(new_json):
        text = []
        for item in new_json:
            if item:
                for i, page in enumerate(item['pages']):
                    page_obj = {"id": i, "list": []}
                    for j, list_item in enumerate(page['list']):
                        text_obj = RPGMakerExtractor.extarctor_text_codes_item(list_item, j)
                        if len(text_obj['text']) > 0:
                            page_obj['list'].append(text_obj)
                    if len(page_obj['list']) > 0:
                        text.append(page_obj)
        return text

    def insert_text_troops(new_json, new_data):
        for texts in new_data:
            for page in texts['pages']:
                for list_item in page['list']:
                    value = new_json[texts['id']]['pages'][page['id']]['list'][list_item['id']]
                    RPGMakerExtractor.insert_text_map_item(value, list_item)

    def extarctor_text_object(new_json):
        text = []
        for item in new_json:
            if item and item['name'] != '':
                obj = {'id': item['id']}
                for attr in RPGMakerExtractor._attributes_find:
                    if attr in item and item[attr] != '' and not RPGMakerExtractor.ignore_text(item[attr]):
                        obj[attr] = item[attr]
                text.append(obj)
        return text

    def insert_text_object(new_json, new_data):
        for texts in new_data:
            for attr in RPGMakerExtractor._attributes_find:
                if attr in texts and texts[attr] != '':
                    new_json[texts['id']][attr] = texts[attr]

    def extarctor_text_System(new_json):
        text = []
        for key, value in new_json.items():
            if key in RPGMakerExtractor._attributes_system_find:
                text.append(value)
        return text

    def insert_text_System(new_json, new_data):
        for texts in new_data:
            for attr in RPGMakerExtractor._attributes_system_find:
                if attr in texts and texts[attr] != '':
                    new_json[attr] = texts[attr]

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
            (r'\b[a-zA-Z]{1,2} [\[\(]', lambda m: m.group(0).replace(' ', '').lower()),
            (r'(?i)\bif \(', lambda m: m.group(0).replace(' ', '').lower()),
            (r'\b \-\b', lambda m: m.group(0).replace(' ', '')),
            (r'\" \"', lambda m: m.group(0).replace('\" \"', '\"')),
            (r'\\n ', lambda m: m.group(0).replace(' ', '')),
        ]

        for i,text in enumerate(texts_list):
            for pattern, repl in patterns:
                text = re.sub(pattern, repl, text)
            texts_list[i] = text

        TextsUtils.interactive_item(texts, texts_list)
