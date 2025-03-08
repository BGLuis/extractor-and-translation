import json
import os
from extractor.BaseExtractor import BaseExtractor
import commun.TextsUtils as TextsUtils
import re


class RPGMakerExtractor(BaseExtractor):
    name = 'RPG Maker'
    files_types = ['json', 'rvdata2']
    pattern_code_355 = re.compile(re.escape(' \"') + '.*?' + re.escape('\"'))
    def __init__(self, translate):
        super().__init__(translate)

    @staticmethod
    def extract_files(file_path):
        if not file_path.endswith('.json'):
            return [os.path.basename(file_path), None]
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [os.path.basename(file_path), data]

    @staticmethod
    def extract_text(file_name, new_json):
        text = []

        def extract_event_text(item):
            if item:
                event = {"id": item['id'], 'pages': []}
                for i, page in enumerate(item['pages']):
                    page_obj = {"id": i, "list": []}
                    for j, list_item in enumerate(page['list']):
                        text_obj = {"id": j, "text": []}

                        if list_item['code'] == 401:
                            text_obj['text'] = list_item['parameters']

                        elif list_item['code'] == 102:
                            text_obj['text'] = list_item['parameters'][0]

                        elif list_item['code'] == 355:
                            if (list_item['parameters'][0].startswith("$gameVariables.setValue") or list_item['parameters'][0].startswith("BattleManager._logWindow.push('addText'")) and RPGMakerExtractor.pattern_code_355.search(list_item['parameters'][0]):
                                find = RPGMakerExtractor.pattern_code_355.findall(list_item['parameters'][0])[0]
                                if find:
                                    text_obj['text'] = find
                        elif list_item['code'] == 320:
                            text_obj['text'] = list_item['parameters'][1]

                        if len(text_obj['text']) > 0:
                            page_obj['list'].append(text_obj)

                    if len(page_obj['list']) > 0:
                        event['pages'].append(page_obj)

                if len(event['pages']) > 0:
                    text.append(event)


        if re.search(r'Map\d{3,}', file_name):
            for item in new_json['events']:
                extract_event_text(item)

        elif file_name == 'CommonEvents.json':
            for item in new_json:
                if item:
                    event = {"id": item['id'], 'list': []}
                    for i, iten in enumerate(item['list']):
                        list_obj = {"id": i, "text": []}
                        if iten['code'] == 401:
                            list_obj['text'] = iten['parameters']
                        elif iten['code'] == 102:
                            list_obj['text'] = iten['parameters'][0]
                        elif iten['code'] == 355:
                            if (iten['parameters'][0].startswith("$gameVariables.setValue") or iten['parameters'][0].startswith("BattleManager._logWindow.push('addText'")) and RPGMakerExtractor.pattern_code_355.search(iten['parameters'][0]):
                                find = RPGMakerExtractor.pattern_code_355.findall(iten['parameters'][0])[0]
                                if find:
                                    list_obj['text'] = find
                        elif iten['code'] == 320:
                            list_obj['text'] = iten['parameters'][1]

                        if len(list_obj['text']) > 0:
                            event['list'].append(list_obj)
                    if len(event['list']) > 0:
                        text.append(event)

        elif file_name == "System.json":
            text.append({'armorTypes': new_json['armorTypes']})
            text.append({'equipTypes': new_json['equipTypes']})
            text.append({'gameTitle': new_json['gameTitle']})
            text.append({'skillTypes': new_json['skillTypes']})
            text.append({'terms': new_json['terms']})

        elif file_name == "Troops.json":
            for item in new_json:
                extract_event_text(item)


        elif file_name in ["MapInfos.json", "Weapons.json", "Items.json", "Skills.json", "States.json", "Enemies.json",
                           "Actors.json", "Armors.json"]:
            for item in new_json:
                if item and item['name'] != '':
                    obj = {'id': item['id']}
                    keys_pattern = re.compile(r'name|profile|description|message\d{1}')
                    for key, value in item.items():
                        if keys_pattern.match(key) and value != '':
                            obj[key] = value
                    text.append(obj)

        return text

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

    @staticmethod
    def update_json(file_name, new_json, new_data):
        if re.search(r'Map\d{3,}', file_name):
            for texts in new_data:
                for b in texts['pages']:
                    for c in b['list']:
                        value = new_json['events'][texts['id']]['pages'][b['id']]['list'][c['id']]

                        if value['code'] == 401:
                            value['parameters'] = c['text']
                        elif value['code'] == 102:
                            value['parameters'][0] = c['text']
                        elif value['code'] == 355:
                            if value['parameters'][0].startswith("$gameVariables.setValue") or value['parameters'][0].startswith("BattleManager._logWindow.push('addText'"):
                                find = RPGMakerExtractor.pattern_code_355.findall(value['parameters'][0])[0]
                                if find:
                                    value['parameters'][0] = re.sub(RPGMakerExtractor.pattern_code_355, c['text'], value['parameters'][0])
                        elif value['code'] == 320:
                            value['parameters'][1] = c['text']

                        new_json['events'][texts['id']]['pages'][b['id']]['list'][c['id']] = value

        elif file_name == 'CommonEvents.json':
            for texts in new_data:
                for i, a in enumerate(texts['list']):
                    value = new_json[texts['id']]['list'][a['id']]
                    if value['code'] == 401:
                        value['parameters'] = a['text']
                    elif value['code'] == 102:
                        value['parameters'][0] = a['text']
                    elif value['code'] == 355:
                        if value['parameters'][0].startswith("$gameVariables.setValue") or value['parameters'][0].startswith("BattleManager._logWindow.push('addText'"):
                            find = RPGMakerExtractor.pattern_code_355.findall(value['parameters'][0])[0]
                            if find:
                                value['parameters'][0] = re.sub(RPGMakerExtractor.pattern_code_355, a['text'],value['parameters'][0])
                    elif value['code'] == 320:
                        value['parameters'][1] = a['text']

                    new_json[texts['id']]['list'][a['id']] = value

        elif file_name == "System.json":
            new_json['armorTypes'] = new_data[0]['armorTypes']
            new_json['equipTypes'] = new_data[1]['equipTypes']
            new_json['gameTitle'] = new_data[2]['gameTitle']
            new_json['skillTypes'] = new_data[3]['skillTypes']
            new_json['terms'] = new_data[4]['terms']
            new_json['terms']['messages'] = new_data[4]['terms']['messages']

        elif file_name == "Troops.json":
            for texts in new_data:
                for b in texts['pages']:
                    for c in b['list']:
                        value = new_json[texts['id']]['pages'][b['id']]['list'][c['id']]

                        if value['code'] == 401:
                            value['parameters'] = c['text']
                        elif value['code'] == 102:
                            value['parameters'][0] = c['text']

                        new_json[texts['id']]['pages'][b['id']]['list'][c['id']] = value


        elif file_name in ["MapInfos.json", "Weapons.json", "Items.json", "Skills.json", "States.json", "Enemies.json",
                           "Actors.json", "Armors.json"]:
            for texts in new_data:
                for keys in texts:
                    if keys != 'id':
                        new_json[texts['id']][keys] = texts[keys]

        return new_json