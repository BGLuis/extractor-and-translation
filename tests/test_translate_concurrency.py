import copy
import threading
import time

import pytest

from src.translate.BaseTranslate import BaseTranslate


class _FakeTranslate(BaseTranslate):
    agent = 'fakeConcurrencyTranslator'
    MAX_REQUESTS_SIMULTANEOUSLY = 4

    # threading.Lock não é deepcopy-ável: precisa ficar em atributo de CLASSE, não de
    # instância, senão copy.deepcopy(translator) (o que process_file faz por arquivo)
    # quebra tentando copiar o lock.
    _counter_lock = threading.Lock()
    current = 0
    max_seen = 0

    def __init__(self, **kw):
        super().__init__(**kw)
        self.translate_client = None

    def _translate_single_batch(self, texts):
        with _FakeTranslate._counter_lock:
            _FakeTranslate.current += 1
            _FakeTranslate.max_seen = max(_FakeTranslate.max_seen, _FakeTranslate.current)
        time.sleep(0.03)
        with _FakeTranslate._counter_lock:
            _FakeTranslate.current -= 1
        return [t.upper() for t in texts]

    def translator(self, texts, progress_callback=None):
        return texts


@pytest.fixture
def fake_translate_cls(tmp_path, monkeypatch):
    from src.translate.TranslationMemory import TranslationMemory
    monkeypatch.setattr(_FakeTranslate, 'cache_path_base', str(tmp_path))
    TranslationMemory._connections.clear()
    _FakeTranslate._request_semaphores.clear()
    _FakeTranslate.current = 0
    _FakeTranslate.max_seen = 0
    return _FakeTranslate


def test_request_semaphore_caps_total_concurrency_across_files(fake_translate_cls):
    """
    5 arquivos em paralelo x N lotes cada podia virar dezenas de requisições
    simultâneas (o cenário que já preocupava PARALLEL_TRANSLATION_IMPLEMENTATION.md).
    O semáforo precisa limitar o TOTAL, mesmo que cada arquivo use sua própria
    deepcopy do tradutor via process_file.
    """
    original = fake_translate_cls(lang_source='en', lang_target='pt')
    file_copies = [copy.deepcopy(original) for _ in range(3)]

    def run_one_file(translator):
        translator.translate_batch_parallel([[f"text{i}"] for i in range(6)])

    threads = [threading.Thread(target=run_one_file, args=(c,)) for c in file_copies]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert fake_translate_cls.max_seen <= fake_translate_cls.MAX_REQUESTS_SIMULTANEOUSLY
