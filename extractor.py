import os
import json
import re


def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def extract_files(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return [os.path.basename(file_path), data]


def findId(data, id):
    for item in data:
        if item['id'] == id:
            return item
    return None


def merge_lists(list1, list2):
    unique_items = set()
    merged_list = []

    for item in list1 + list2:
        item_tuple = tuple(item.items())
        if item_tuple not in unique_items:
            unique_items.add(item_tuple)
            merged_list.append(item)

    return merged_list


def remove_none_values(lst):
    return [item for item in lst if item is not None]


def extract_text(file_name, data):
    new_json = data
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

    elif file_name == "Tilesets.json" or file_name == "ContainerProperties.json" or file_name == "Animations.json":
        pass

    else:
        for item in new_json:
            if item and item['name'] != '':
                obj = {'id': item['id']}
                keys = ['name', 'description', 'message1', 'message2']

                for key in keys:
                    if key in item and item[key] != '':
                        obj[key] = item[key]

                text.append(obj)

    return text


def update_json(file_name, data, new_data):
    new_json = data

    if re.search(r'Map\d{3,}', file_name):
        for texts in new_data:
            for b in texts['pages']:
                for c in b['list']:
                    value = new_json['events'][texts['id']]['pages'][b['id']]['list'][c['id']]

                    if value['code'] == 401:
                        value['parameters'] = c['text']
                    elif value['code'] == 102:
                        value['parameters'][0] = c['text']

                    new_json['events'][texts['id']]['pages'][b['id']]['list'][c['id']] = value

    elif file_name == 'CommonEvents.json':
        for texts in new_data:
            for i, a in enumerate(texts['list']):
                value = new_json[texts['id']]['list'][a['id']]
                if value['code'] == 401:
                    value['parameters'] = a['text']
                elif value['code'] == 102:
                    value['parameters'][0] = a['text']

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

    else:
        for texts in new_data:
            for keys in texts:
                if keys != 'id':
                    new_json[texts['id']][keys] = texts[keys]

    return new_json


def import_files(file_name, json_data, folder='output'):
    create_directory_if_not_exists(folder)
    infos = json_data

    with open(os.path.join(folder, file_name), 'w', encoding='utf-8') as f:
        json.dump(infos, f, ensure_ascii=False, indent=4)
