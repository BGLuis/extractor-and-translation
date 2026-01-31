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

    def _create_batches(self, texts):
        """
        Default implementation: chunks texts based on char_limit.
        Can be overridden by subclasses if different batching logic is needed.
        """
        import commun.TextsUtils as TextsUtils
        batches = []
        current_batch = []
        current_length = 0

        for text in texts:
            text_unicode = TextsUtils.convert_special_chars_to_unicode(text)
            text_limiter = text_unicode + self.delimiter
            
            # If adding this text exceeds the limit and we have a non-empty batch, start a new one
            if current_length + len(text_limiter) >= self.char_limit and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_length = 0
            
            current_batch.append(text)
            current_length += len(text_limiter)

        if current_batch:
            batches.append(current_batch)
            
        return batches

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

    def translate_batch(self, texts, progress_callback=None):
        if texts is None:
            return None

        # 1. Identify what needs to be translated vs what is cached
        translated_texts = [None] * len(texts)
        cache_indices = []
        non_cached_indices = []
        none_indices = [] # Indices where input text is None

        for i, text in enumerate(texts):
            if text is None:
                none_indices.append(i)
            elif isinstance(text, str) and text in self.__class__.cache:
                translated_texts[i] = self.__class__.cache[text]
                cache_indices.append(i)
            else:
                non_cached_indices.append(i)

        non_cached_texts = [texts[i] for i in non_cached_indices]

        # 2. Process non-cached texts
        if non_cached_texts:
            batches = self._create_batches(non_cached_texts)
            translated_results = self.translate_batch_parallel(batches, progress_callback)

            # 3. Merge results back
            # We must be careful if translated_results count matches non_cached_texts count
            # Ideally they should match 1-to-1 if _translate_single_batch works correctly
            
            current_result_idx = 0
            for i in range(len(non_cached_indices)):
                original_idx = non_cached_indices[i]
                original_text = texts[original_idx]
                
                if current_result_idx < len(translated_results):
                    result = translated_results[current_result_idx]
                    translated_texts[original_idx] = result
                    if isinstance(original_text, str):
                         self.__class__.cache[original_text] = result
                    current_result_idx += 1
                else:
                    # Fallback if translation returned fewer items than expected
                    translated_texts[original_idx] = original_text # Or handle error

        # 4. Restore None values
        for index in none_indices:
            translated_texts[index] = None

        return translated_texts


    @abstractmethod
    def translator(self, texts, progress_callback=None):
        pass
