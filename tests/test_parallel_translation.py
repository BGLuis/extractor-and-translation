"""
Tradução paralela real via Google Translate / Ollama. Requer rede (e, para Ollama, um
servidor local rodando) - por isso fica desligado por padrão, para "pytest" não bater
em serviços externos sem avisar. Rode com RUN_LIVE_TRANSLATION_TESTS=1 para habilitar.
"""
import os

import pytest

from src.translate.GoogleTranslate import GoogleTranslate
from src.translate.OllamaTranslate import OllamaTranslate

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_TRANSLATION_TESTS"),
    reason="Requer rede (Google Translate) e/ou um servidor Ollama local; "
           "defina RUN_LIVE_TRANSLATION_TESTS=1 para habilitar.",
)


def test_google_translate_parallel():
    translator = GoogleTranslate(lang_source='en', lang_target='pt', char_limit=100)
    texts = [
        "Hello, how are you?",
        "The weather is nice today.",
        "I love programming in Python.",
        "Artificial Intelligence is fascinating.",
        "Video games are fun.",
        "Good morning everyone!",
        "Thank you for your help.",
        "See you later.",
        "Have a great day!",
        "This is a test message.",
    ] * 2

    progress_calls = []

    def progress_callback(current, total, eta_seconds=None):
        progress_calls.append((current, total))

    translated = translator.translate_batch(texts, progress_callback)

    assert len(translated) == len(texts)
    assert all(isinstance(t, str) and t for t in translated)
    assert progress_calls


def test_ollama_translate_parallel():
    translator = OllamaTranslate(lang_source='en', lang_target='pt')
    texts = [
        "Hello world!",
        "Goodbye friend.",
        "Thank you very much.",
        "Good luck!",
        "Nice to meet you.",
    ]

    translated = translator.translate_batch(texts)

    assert len(translated) == len(texts)
    assert all(isinstance(t, str) and t for t in translated)
