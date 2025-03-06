from abc import ABC, abstractmethod
import os
import json


class BaseTranslate(ABC):
    agent = 'BaseTranslate'
    cache = {}
    cache_path = ''
    delimiter = '\n<span> </span>\n'
    char_limit = 1000 # era pra ser 5000
    CHAR_LIMIT_MIN = 1000
    CHAR_LIMIT_DECREMENT = 1000
    lang_source = 'en'
    lang_target = 'pt'
    cache_path_base = 'cache'
    MAX_REQUESTS_SIMULTANEOUSLY = 99

    def __init__(self, agent, delimiter=None, char_limit=None,lang_source=None, lang_target=None):
        self.delimiter = delimiter if delimiter else BaseTranslate.delimiter
        self.char_limit = char_limit if char_limit else BaseTranslate.char_limit
        self.lang_source = lang_source if lang_source else BaseTranslate.lang_source
        self.lang_target = lang_target if lang_target else BaseTranslate.lang_target
        self.translate_client = None
        BaseTranslate.cache_path = f'{BaseTranslate.cache_path_base}/{agent}/cache_{self.lang_source}_{self.lang_target}.json'
        BaseTranslate.init_cache(self.cache_path)


    @classmethod
    def from_default(cls):
        return cls()


    @classmethod
    def from_languages(cls, lang_source, lang_target):
        return cls(lang_source, lang_target)


    @classmethod
    def from_all(cls):
        return cls(BaseTranslate.delimiter, BaseTranslate.char_limit, BaseTranslate.lang_source, BaseTranslate.lang_target)


    def reduce_limite(self):
        if self.char_limit > BaseTranslate.CHAR_LIMIT_MIN:
            self.char_limit -= BaseTranslate.CHAR_LIMIT_DECREMENT
            return True

    def list_lang(self):
        return self.translate_client.get_supported_languages()

    def change_language(self, lang_source, lang_target):
        self.lang_source = lang_source
        self.lang_target = lang_target

        self.translate_client.target = self.lang_target
        self.translate_client.source = self.lang_source
        BaseTranslate.cache_path = f'{BaseTranslate.cache_path_base}/{self.agent}/cache_{self.lang_source}_{self.lang_target}.json'
        BaseTranslate.init_cache(self.cache_path)

    @staticmethod
    def init_cache(cache_path):
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        if not os.path.exists(cache_path):
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({"": ""}, f, ensure_ascii=False, indent=4)

        with open(cache_path, 'r', encoding='utf-8') as f:
            BaseTranslate.cache = json.load(f)


    @staticmethod
    def save_cache():
        if os.path.exists(BaseTranslate.cache_path):
            with open(BaseTranslate.cache_path, 'r', encoding='utf-8') as f:
                file_cache = json.load(f)

            file_cache.update(BaseTranslate.cache)

            with open(BaseTranslate.cache_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(file_cache, ensure_ascii=False, indent=4))


    @abstractmethod
    def translate_batch(self, texts):
        pass


    @abstractmethod
    def translator(self, texts):
        pass