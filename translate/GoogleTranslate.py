from translate.BaseTranslate import BaseTranslate
from deep_translator import GoogleTranslator
import commun.TextsUtils as TextsUtils


class GoogleTranslate(BaseTranslate):
    agent = 'googleTraslator'
    MAX_REQUESTS_SIMULTANEOUSLY = 9

    def __init__(self, delimiter=None, char_limit=None, lang_source=None, lang_target=None):
        super().__init__(delimiter, char_limit, lang_source, lang_target)
        self.translate_client = GoogleTranslator(source=self.lang_source, target=self.lang_target)


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
            elif isinstance(text, str) and text in GoogleTranslate.cache:
                translated_texts[i] = GoogleTranslate.cache[text]
                cache_indices.append(i)
            else:
                non_cached_indices.append(i)

        non_cached_texts = [text for text in texts if isinstance(text, str) and text not in GoogleTranslate.cache]

        if non_cached_texts:
            batches = []
            current_batch = []
            current_length = 0

            for text in non_cached_texts:
                if current_length + len(text) > GoogleTranslate.char_limit:
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
                translated_non_cached_texts.extend(translate_list)

            non_cached_index = 0
            for i in range(len(translated_texts)):
                if translated_texts[i] is None and non_cached_index < len(translated_non_cached_texts):
                    translated_texts[i] = translated_non_cached_texts[non_cached_index]
                    if isinstance(texts[non_cached_indices[non_cached_index]], str):
                        GoogleTranslate.cache[texts[non_cached_indices[non_cached_index]]] = translated_non_cached_texts[
                            non_cached_index]
                    non_cached_index += 1

            for index in none_indices:
                translated_texts.insert(index, None)

        return translated_texts


    def translator(self, texts):
        treated_text = TextsUtils.dictToList(texts)
        translate_text = self.translate_batch(treated_text)
        TextsUtils.interactive_item(texts, translate_text)
        return texts