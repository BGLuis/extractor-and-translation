from src.translate.BaseTranslate import BaseTranslate
from dotenv import load_dotenv
import os
import ollama
import src.utils.TextsUtils as TextsUtils
load_dotenv()


class OllamaTranslate(BaseTranslate):
    agent = 'ollamaTranslator'
    MAX_REQUESTS_SIMULTANEOUSLY = 10
    char_limit = 10000
    context_function = 'Translate the following text. Provide only the translated text, without any additional comments, explanations, or notes.'
    context_additional = "Act as an expert game localizer. Your mission is to translate text for a video game, ensuring the translation is engaging and immersive for the player. The text below could be character dialogue, an item description, a quest objective, or a UI menu element. Adapt the translation to fit the gaming context, using appropriate and common gaming jargon. Maintain the original tone, whether it's serious, humorous, or epic. Provide only the direct translation. Do not provide a literal, word-for-word translation if a more natural, context-aware alternative exists."

    @classmethod
    def requires_synopsis(cls):
        return True

    @classmethod
    def get_interactive_questions(cls):
        return [
            {
                'key': 'synopsis',
                'question': 'Digite a sinopse do jogo (ou pressione Enter para pular):',
                'title': '\n=== SINOPSE DO JOGO (OPCIONAL) ===',
                'description': 'A sinopse ajuda a melhorar significativamente a qualidade da tradução fornecendo contexto ao modelo Ollama.',
                'color': 'yellow',
                'required': False
            }
        ]

    def apply_configuration(self, config):
        if 'synopsis' in config and config['synopsis']:
            self.set_game_synopsis(config['synopsis'])

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
    def preprocess_text(texts):
        for i, text in enumerate(texts):
            texts[i] = text


    @staticmethod
    def postprocess_text(texts):
        for i, text in enumerate(texts):
            texts[i] = text

    def _create_batches(self, texts):
        """Ollama prefers single-item batches to manage context window and prompt size."""
        return [[text] for text in texts]

    def _translate_single_batch(self, texts):
        if not texts or len(texts) != 1:
            return texts

        text = texts[0]

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

        return [result]

    def translator(self, texts, progress_callback=None):
        treated_text = TextsUtils.dictToList(texts)
        self.preprocess_text(treated_text)
        translate_text = self.translate_batch(treated_text, progress_callback)
        self.postprocess_text(translate_text)
        TextsUtils.interactive_item(texts, translate_text)
        return texts
