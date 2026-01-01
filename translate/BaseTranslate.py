from abc import ABC, abstractmethod
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


class BaseTranslate(ABC):
    agent = 'BaseTranslate'
    cache = {}
    cache_path = ''
    delimiter = '\n<span> </span>\n'
    char_limit = 5000
    CHAR_LIMIT_MIN = 1000
    CHAR_LIMIT_DECREMENT = 1000
    lang_source = 'en'
    lang_target = 'pt'
    cache_path_base = 'cache'
    MAX_REQUESTS_SIMULTANEOUSLY = 99

    def __init__(self, delimiter=None, char_limit=None,lang_source=None, lang_target=None):
        self.delimiter = delimiter if delimiter else self.__class__.delimiter
        self.char_limit = char_limit if char_limit else self.__class__.char_limit
        self.__class__.lang_source = lang_source if lang_source else self.__class__.lang_source
        self.__class__.lang_target = lang_target if lang_target else self.__class__.lang_target
        self.translate_client = None
        self.game_synopsis = None
        self.__class__.cache_path = f'{self.__class__.cache_path_base}/{self.__class__.agent}/cache_{self.__class__.lang_source}_{self.__class__.lang_target}.json'
        self.__class__.init_cache()


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
        if self.char_limit > self.__class__.CHAR_LIMIT_MIN:
            self.char_limit -= self.__class__.CHAR_LIMIT_DECREMENT
            return True

    def list_lang(self):
        return self.translate_client.get_supported_languages()

    def set_game_synopsis(self, synopsis):
        self.game_synopsis = synopsis.strip() if synopsis else None

    def get_game_synopsis(self):
        return self.game_synopsis

    def change_language(self, lang_source, lang_target):
        self.lang_source = lang_source
        self.lang_target = lang_target

        self.translate_client.target = self.lang_target
        self.translate_client.source = self.lang_source
        self.__class__.cache_path = f'{self.__class__.cache_path_base}/{self.__class__.agent}/cache_{self.lang_source}_{self.lang_target}.json'
        self.__class__.cache = {}
        self.init_cache()

    @classmethod
    def init_cache(cls):
        os.makedirs(os.path.dirname(cls.cache_path), exist_ok=True)

        if not os.path.exists(cls.cache_path):
            with open(cls.cache_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps({"": ""}, ensure_ascii=False, indent=4))

        if not cls.cache:
            with open(cls.cache_path, 'r', encoding='utf-8') as f:
                cls.cache = json.load(f)

    @classmethod
    def save_cache(cls):
        if os.path.exists(cls.cache_path):
            with open(cls.cache_path, 'r', encoding='utf-8') as f:
                file_cache = json.load(f)

            file_cache.update(cls.cache)

            with open(cls.cache_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(file_cache, ensure_ascii=False, indent=4))


    @classmethod
    def requires_synopsis(cls):
        return False

    @classmethod
    def get_interactive_questions(cls):
        return []

    def apply_configuration(self, config):
        pass

    @abstractmethod
    def _translate_single_batch(self, texts):
        pass

    def translate_batch_parallel(self, batches, progress_callback=None):
        if not batches:
            return []

        max_workers = min(self.MAX_REQUESTS_SIMULTANEOUSLY, len(batches))

        translated_batches = [None] * len(batches)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self._translate_single_batch, batch): idx
                for idx, batch in enumerate(batches)
            }

            completed = 0
            for future in as_completed(future_to_index):
                batch_idx = future_to_index[future]
                try:
                    translated_batches[batch_idx] = future.result()
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(batches))
                except Exception as e:
                    translated_batches[batch_idx] = []
                    print(f"Error translating batch {batch_idx}: {e}")

        all_translations = []
        for batch in translated_batches:
            if batch:
                all_translations.extend(batch)

        return all_translations

    @abstractmethod
    def translate_batch(self, texts, progress_callback=None):
        pass


    @abstractmethod
    def translator(self, texts, progress_callback=None):
        pass
