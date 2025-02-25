from deep_translator import GoogleTranslator
import re
import os
import json

class Translate:
    cache = {}
    cache_path = ''
    agent = 'googleTraslator'
    delimiter = '\n<span> </span>\n'
    char_limit = 1000 # era pra ser 5000
    lang_source = 'auto'
    lang_target = 'pt'
    cache_path_base = 'cache'


    def __init__(self, delimiter=None, char_limit=None,lang_source=None, lang_target=None):
        self._id_counter = 0
        self.delimiter = delimiter if delimiter else Translate.delimiter
        self.char_limit = char_limit if char_limit else Translate.char_limit
        self.lang_source = lang_source if lang_source else Translate.lang_source
        self.lang_target = lang_target if lang_target else Translate.lang_target
        self.translate_client = GoogleTranslator(source=self.lang_source, target=self.lang_target)
        Translate.cache_path = f'{Translate.cache_path_base}/{Translate.agent}/cache_{self.lang_source}_{self.lang_target}.json'
        Translate.init_cache(self.cache_path)


    @classmethod
    def from_default(cls):
        return cls()


    @classmethod
    def from_languages(cls, lang_source, lang_target):
        return cls(lang_source, lang_target)


    @classmethod
    def from_all(cls):
        return cls(Translate.delimiter, Translate.char_limit, Translate.lang_source, Translate.lang_target)


    @staticmethod
    def init_cache(cache_path):
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        if not os.path.exists(cache_path):
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({"": ""}, f, ensure_ascii=False, indent=4)

        with open(cache_path, 'r', encoding='utf-8') as f:
            Translate.cache = json.load(f)


    @staticmethod
    def save_cache():
        if os.path.exists(Translate.cache_path):
            with open(Translate.cache_path, 'r', encoding='utf-8') as f:
                file_cache = json.load(f)

            file_cache.update(Translate.cache)

            with open(Translate.cache_path, 'w', encoding='utf-8') as f:
                json.dump(file_cache, f, ensure_ascii=False, indent=4)


    def fix_text_variable(self, text):
        pattern_var = r'\\ \b[a-zA-Z]{1,2} \[\d+\]'
        vars = re.findall(pattern_var, text)
        for var in vars:
            text = text.replace(var, var.replace(' ', ''), 1)

        pattern_if = r'(?i)\bif \(\b[a-zA-Z]{1,2} \[\d+\]\)'
        ifs = re.findall(pattern_if, text)
        for if_ in ifs:
            text = text.replace(if_, if_.replace(' ', '').lower(), 1)

        pattern_sound_effect = r'\\ SE \[.*?\]'
        ses = re.findall(pattern_sound_effect, text)
        for se in ses:
            text = text.replace(se, se.replace(' ', ''), 1)

        pattern_var_var = r'\\ \b[a-zA-Z]{1,2} \[\\v\[\d+\]\]'
        var_vars = re.findall(pattern_var_var, text)
        for var_var in var_vars:
            text = text.replace(var_var, var_var.replace(' ', ''), 1)

        return text


    def dictToList(self, dictionary):
        treated_text = []
        for key, value in dictionary.items():
            if key != 'id':
                if isinstance(value, dict):
                    sub_treated_text, dictionary[key] = self.dictToList(value)
                    treated_text.extend(sub_treated_text)
                elif isinstance(value, list):
                    new_list = []
                    for sub_item in value:
                        if isinstance(sub_item, dict):
                            sub_treated_text, sub_item = self.dictToList(sub_item)
                            treated_text.extend(sub_treated_text)
                            new_list.append(sub_item)
                        else:
                            treated_text.append(sub_item)
                            new_list.append(f"id_{self._id_counter}")
                            self._id_counter += 1
                    dictionary[key] = new_list
                else:
                    treated_text.append(value)
                    dictionary[key] = f"id_{self._id_counter}"
                    self._id_counter += 1
        return treated_text, dictionary


    def interactive_item(self, obj, texts):
        def insert_text(i, item):
            if isinstance(item, (dict, list)):
                self.interactive_item(item, texts)
            elif isinstance(item, str) and re.search(r'id_\d{1,}',item):
                index = int(item.split('_')[1])
                if index < len(texts):
                    obj[i] = texts[index]
                else:
                    obj[i] = "Index out of range"

        if isinstance(obj, dict):
            for k, v in obj.items():
                insert_text(k, v)
            return obj
        elif isinstance(obj, list):
            for i, elem in enumerate(obj):
                insert_text(i, elem)
            return obj


    def translate_batch(self, texts):
        if texts is None:
            return None

        translated_texts = [None] * len(texts)
        cache_indices = []
        non_cached_indices = []
        none_indices = []

        for i, text in enumerate(texts):
            if text is None:
                none_indices.append(i)
            elif isinstance(text, str) and text in Translate.cache:
                translated_texts[i] = Translate.cache[text]
                cache_indices.append(i)
            else:
                non_cached_indices.append(i)

        non_cached_texts = [text for text in texts if isinstance(text, str) and text not in Translate.cache]

        if non_cached_texts:
            batches = []
            current_batch = []
            current_length = 0

            for text in non_cached_texts:
                if current_length + len(text) > Translate.char_limit:
                    batches.append(current_batch)
                    current_batch = []
                    current_length = 0
                current_batch.append(text)
                current_length += len(text)

            if current_batch:
                batches.append(current_batch)

            translated_non_cached_texts = []
            for batch in batches:
                list_join = self.delimiter.join(batch)
                translate_str = self.translate_client.translate(list_join)

                translate_list = translate_str.split(self.delimiter)
                for i,translated_text in enumerate(translate_list):
                    translate_list[i] = self.fix_text_variable(translated_text)
                translated_non_cached_texts.extend(translate_list)

            non_cached_index = 0
            for i in range(len(translated_texts)):
                if translated_texts[i] is None and non_cached_index < len(translated_non_cached_texts):
                    translated_texts[i] = translated_non_cached_texts[non_cached_index]
                    if isinstance(texts[non_cached_indices[non_cached_index]], str):
                        Translate.cache[texts[non_cached_indices[non_cached_index]]] = translated_non_cached_texts[
                            non_cached_index]
                    non_cached_index += 1

            for index in none_indices:
                translated_texts.insert(index, None)

        return translated_texts


    def translator(self, texts):
        if isinstance(texts, list):
            texts = {"root": texts}
        treated_text, temp = self.dictToList(texts)

        translate_text = self.translate_batch(treated_text)
        translate_dict = self.interactive_item(temp, translate_text)
        self._id_counter = 0
        return translate_dict["root"] if "root" in translate_dict else translate_dict