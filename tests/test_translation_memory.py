import pytest

from src.translate.TranslationMemory import TranslationMemory


@pytest.fixture
def tm(tmp_path):
    return TranslationMemory(str(tmp_path / 'memory.db'), 'en', 'pt', engine='googleTraslator')


def test_dict_like_interface(tm):
    assert 'hello' not in tm
    tm['hello'] = 'ola'
    assert 'hello' in tm
    assert tm['hello'] == 'ola'


def test_cross_engine_reuse(tmp_path, tm):
    tm['hello'] = 'ola'
    other_engine = TranslationMemory(str(tmp_path / 'memory.db'), 'en', 'pt', engine='ollamaTranslator')
    assert other_engine['hello'] == 'ola'


def test_machine_write_does_not_overwrite_reviewed_translation(tm):
    """
    Bug real encontrado ao testar TMX import/export: o UPSERT original só protegia
    status='locked'. Uma retradução de máquina (status='machine') para o mesmo texto
    sobrescrevia silenciosamente o target de uma linha já revisada, mantendo o rótulo
    'reviewed' só que agora mentindo sobre o conteúdo.
    """
    tm.store('X', 'traducao_revisada', status='reviewed')
    tm.store('X', 'traducao_de_maquina', status='machine')

    assert tm.lookup('X') == 'traducao_revisada'


def test_reviewed_write_upgrades_a_machine_translation(tm):
    tm.store('X', 'traducao_de_maquina', status='machine')
    tm.store('X', 'traducao_revisada', status='reviewed')

    assert tm.lookup('X') == 'traducao_revisada'


def test_locked_entry_is_never_overwritten(tm):
    tm.lock_term('X', 'termo_fixo')
    tm.store('X', 'tentativa_machine', status='machine')
    tm.store('X', 'tentativa_reviewed', status='reviewed')

    assert tm.lookup('X') == 'termo_fixo'


def test_fuzzy_candidates_stay_in_sync_via_fts_triggers(tm):
    tm['hello world'] = 'ola mundo'
    candidates = tm.fuzzy_candidates('hello')
    assert any(c['source'] == 'hello world' for c in candidates)
