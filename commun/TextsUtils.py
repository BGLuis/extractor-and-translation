from commun.IntWrapper import IntWrapper


def dictToList(dictionary, extract=None):
    if extract is None:
        extract = []
    if isinstance(dictionary, dict) or isinstance(dictionary, list):
        haystack = dictionary.items() if isinstance(dictionary, dict) else enumerate(dictionary)
        for key, value in haystack:
            dictToList(value, extract)
    elif isinstance(dictionary, str):
        extract.append(dictionary)
    return extract


def interactive_item(obj, texts, occurrences=None):
    if occurrences is None:
        occurrences = IntWrapper(0)
    if isinstance(obj, dict) or isinstance(obj, list):
        haystack = obj.items() if isinstance(obj, dict) else enumerate(obj)
        for key, value in haystack:
            if isinstance(value, str):
                obj[key] = texts[occurrences.get()]
                occurrences.add(1)
            else:
                interactive_item(value, texts, occurrences)


def convert_special_chars_to_unicode(text):
    return text.encode('unicode_escape').decode('utf-8')


def decode_unicode_escape(text):
    return text.encode('utf-8').decode('unicode_escape')