from translate.BaseTranslate import BaseTranslate
from dotenv import load_dotenv
import os
import ollama
import commun.TextsUtils as TextsUtils
load_dotenv()


class OllamaTranslate(BaseTranslate):
    agent = 'ollamaTranslator'
    MAX_REQUESTS_SIMULTANEOUSLY = 10
    char_limit = 10000
    context_function = 'Translate the following text. Provide only the translated text, without any additional comments, explanations, or notes.'
    context_additional = "Act as an expert game localizer. Your mission is to translate text for a video game, ensuring the translation is engaging and immersive for the player. The text below could be character dialogue, an item description, a quest objective, or a UI menu element. Adapt the translation to fit the gaming context, using appropriate and common gaming jargon. Maintain the original tone, whether it's serious, humorous, or epic. Provide only the direct translation. Do not provide a literal, word-for-word translation if a more natural, context-aware alternative exists."

    def __init__(self, delimiter=None, char_limit=None, lang_source=None, lang_target=None):
        super().__init__(delimiter, char_limit, lang_source, lang_target)
        self.model = os.getenv('OLLAMA_MODEL')
        self.max_requests = os.getenv('OLLAMA_MAX_REQUESTS')
        if not self.model or not self.max_requests:
            raise ValueError("Environment variables OLLAMA_MODEL and OLLAMA_MAX_REQUESTS must be defined.")
        self.context_language = f"Translate the text below from {self.lang_source} to {self.lang_target}:"

    def change_language(self, lang_source, lang_target):
        self.lang_source = lang_source
        self.lang_target = lang_target

        self.__class__.cache_path = f'{self.__class__.cache_path_base}/{self.__class__.agent}/cache_{self.lang_source}_{self.lang_target}.json'
        self.__class__.cache = {}
        self.context_language = f"Translate the text below from {self.lang_source} to {self.lang_target}:"
        self.init_cache()

    @staticmethod
    def treats_text(texts):
        for i, text in enumerate(texts):
            texts[i] = text


    @staticmethod
    def mistreats_text(texts):
        for i,text in enumerate(texts):
            texts[i] = text

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
            elif isinstance(text, str) and text in self.__class__.cache:
                translated_texts[i] = self.__class__.cache[text]
                cache_indices.append(i)
            else:
                non_cached_indices.append(i)

        non_cached_texts = [texts[i] for i in non_cached_indices]

        if non_cached_texts:
            for idx, text in zip(non_cached_indices, non_cached_texts):
                messages = [
                    {"role": "system", "content": self.context_function},
                    {"role": "system", "content": self.context_additional},
                ]

                if self.game_synopsis:
                    synopsis_context = f"Game Synopsis/Context: {self.game_synopsis}\n\nUse this synopsis to better understand the game's context and provide more accurate, context-aware translations."
                    messages.append({"role": "system", "content": synopsis_context})

                messages.append({"role": "system", "content": self.context_language})
                messages.append({"role": "user", "content": text})

                response = ollama.chat(
                    model=self.model,
                    messages=messages
                )
                result = response['message']['content'].strip()
                translated_texts[idx] = result
                self.__class__.cache[text] = result

        for index in none_indices:
            translated_texts.insert(index, None)

        return translated_texts

    def translator(self, texts):
        treated_text = TextsUtils.dictToList(texts)
        self.treats_text(treated_text)
        translate_text = self.translate_batch(treated_text)
        self.mistreats_text(translate_text)
        TextsUtils.interactive_item(texts, translate_text)
        return texts
