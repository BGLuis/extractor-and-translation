from src.translate.BaseTranslate import BaseTranslate
from deep_translator import GoogleTranslator
import src.utils.TextsUtils as TextsUtils
from src.factory import register_translator

@register_translator("googleTraslator")
class GoogleTranslate(BaseTranslate):
    # Evita inconsistências em lotes com o cliente HTTP compartilhado.
    MAX_REQUESTS_SIMULTANEOUSLY = 7

    @classmethod
    def requires_synopsis(cls):
        return False

    @classmethod
    def get_interactive_questions(cls):
        return []

    def apply_configuration(self, config):
        pass

    def __init__(self, delimiter=None, char_limit=None, lang_source=None, lang_target=None):
        super().__init__(delimiter, char_limit, lang_source, lang_target)
        self.translate_client = GoogleTranslator(source=self.lang_source, target=self.lang_target)


    @staticmethod
    def preprocess_text(texts):
        for i, text in enumerate(texts):
            texts[i] = text


    @staticmethod
    def postprocess_text(texts):
        for i,text in enumerate(texts):
            texts[i] = text

    def _translate_single_batch(self, texts):
        if not texts:
            return []

        import time

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                list_join = self.delimiter.join(texts)
                translate_str = self.translate_client.translate(list_join)
                if not translate_str:
                    raise ValueError("Empty translation received")
                translate_list = translate_str.split(self.delimiter)

                # Se o delimitador for alterado pelo provedor, o batch pode ficar desalinhado.
                # Nessa situação, traduzimos item a item para manter mapeamento correto.
                if len(translate_list) != len(texts):
                    safe_results = []
                    for text in texts:
                        try:
                            res = self.translate_client.translate(text)
                            safe_results.append(res if res is not None else text)
                        except Exception:
                            safe_results.append(text)
                    return safe_results

                return translate_list
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1.0 * (attempt + 1))
                else:
                    if len(texts) > 1:
                        safe_results = []
                        for text in texts:
                            try:
                                res = self.translate_client.translate(text)
                                safe_results.append(res if res is not None else text)
                            except Exception:
                                safe_results.append(text)
                        return safe_results
                    raise last_error


    def translator(self, texts, progress_callback=None):
        treated_text = TextsUtils.dictToList(texts)
        self.preprocess_text(treated_text)
        translate_text = self.translate_batch(treated_text, progress_callback)
        self.postprocess_text(translate_text)
        TextsUtils.interactive_item(texts, translate_text)
        return texts
