import copy

import pytest

from src.translate.GoogleTranslate import GoogleTranslate
from src.translate.TranslationMemory import TranslationMemory


@pytest.fixture
def isolated_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(GoogleTranslate, 'cache_path_base', str(tmp_path))
    TranslationMemory._connections.clear()
    yield tmp_path


def test_deepcopy_shares_cache_but_isolates_retry_state(isolated_cache_dir):
    original = GoogleTranslate(lang_source='en', lang_target='pt')
    per_file_copy = copy.deepcopy(original)

    assert per_file_copy.cache is original.cache
    assert per_file_copy.cache_lock is original.cache_lock

    per_file_copy.char_limit = 1000
    assert original.char_limit != 1000


def test_separate_instances_do_not_leak_language(isolated_cache_dir):
    en_pt = GoogleTranslate(lang_source='en', lang_target='pt')
    ja_pt = GoogleTranslate(lang_source='ja', lang_target='pt')

    assert en_pt.lang_source == 'en'
    assert ja_pt.lang_source == 'ja'


def test_from_languages_maps_keyword_arguments_correctly(isolated_cache_dir):
    translator = GoogleTranslate.from_languages('es', 'fr')
    assert translator.lang_source == 'es'
    assert translator.lang_target == 'fr'


def test_save_cache_persists_to_disk(isolated_cache_dir):
    translator = GoogleTranslate(lang_source='en', lang_target='pt')
    translator.cache['hello'] = 'ola'
    translator.save_cache()

    reopened = TranslationMemory(translator.cache_path, 'en', 'pt', engine=GoogleTranslate.agent)
    assert reopened['hello'] == 'ola'


def test_cache_is_reused_across_engines_for_the_same_pair(isolated_cache_dir):
    """
    O ponto central de trocar o cache por uma TM em SQLite: uma tradução feita pelo
    Google fica disponível para o Ollama, e vice-versa, em vez de cada engine manter
    seu próprio cache isolado como acontecia com os arquivos JSON separados.
    """
    google = GoogleTranslate(lang_source='en', lang_target='pt')
    google.cache['hello'] = 'ola'

    other_engine_view = TranslationMemory(google.cache_path, 'en', 'pt', engine='ollamaTranslator')
    assert other_engine_view['hello'] == 'ola'
