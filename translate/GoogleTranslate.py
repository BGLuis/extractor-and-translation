from translate.BaseTranslate import BaseTranslate
from deep_translator import GoogleTranslator
import commun.TextsUtils as TextsUtils


class GoogleTranslate(BaseTranslate):
    agent = 'googleTraslator'
    MAX_REQUESTS_SIMULTANEOUSLY = 9

    def __init__(self, delimiter=None, char_limit=None, lang_source=None, lang_target=None):
        super().__init__(delimiter, char_limit, lang_source, lang_target)
        self.translate_client = GoogleTranslator(source=self.lang_source, target=self.lang_target)


    @staticmethod
    def treats_text(texts):
        for i, text in enumerate(texts):
            texts[i] = text


    @staticmethod
    def mistreats_text(texts):
        for i,text in enumerate(texts):
            texts[i] = text


    def translate_batch(self, texts, progress_callback=None):
        if texts is None:
            return None

        translated_texts = [None] * len(texts)
        cache_indices = []
        non_cached_indices = []
        none_indices = []

        for i, text in enumerate(texts):
            if text is None:
                none_indices.append(i)
            elif isinstance(text, str) and text in self.__class__.cache:
                translated_texts[i] = self.__class__.cache[text]
                cache_indices.append(i)
            else:
                non_cached_indices.append(i)

        non_cached_texts = [text for text in texts if isinstance(text, str) and text not in self.__class__.cache]

        if non_cached_texts:
            batches = []
            current_batch = []
            current_length = 0

            for text in non_cached_texts:
                text_unicode = TextsUtils.convert_special_chars_to_unicode(text)
                text_limiter = text_unicode + self.delimiter
                if current_length + len(text_limiter) >= self.char_limit:
                    batches.append(current_batch)
                    current_batch = []
                    current_length = 0
                current_batch.append(text)
                current_length += len(text_limiter)

            if current_batch:
                batches.append(current_batch)

            total_batches = len(batches)
            translated_non_cached_texts = []
            for batch_idx, batch in enumerate(batches, 1):
                if progress_callback:
                    progress_callback(batch_idx, total_batches)

                list_join = self.delimiter.join(batch)
                translate_str = self.translate_client.translate(list_join)
                translate_list = translate_str.split(self.delimiter)
                translated_non_cached_texts.extend(translate_list)

            non_cached_index = 0
            for i in range(len(translated_texts)):
                if translated_texts[i] is None and non_cached_index < len(translated_non_cached_texts):
                    translated_texts[i] = translated_non_cached_texts[non_cached_index]
                    if isinstance(texts[non_cached_indices[non_cached_index]], str):
                        self.__class__.cache[texts[non_cached_indices[non_cached_index]]] = translated_non_cached_texts[
                            non_cached_index]
                    non_cached_index += 1

            for index in none_indices:
                translated_texts.insert(index, None)

        return translated_texts


    def translator(self, texts, progress_callback=None):
        treated_text = TextsUtils.dictToList(texts)
        self.treats_text(treated_text)
        translate_text = self.translate_batch(treated_text, progress_callback)
        self.mistreats_text(translate_text)
        TextsUtils.interactive_item(texts, translate_text)
        return texts
