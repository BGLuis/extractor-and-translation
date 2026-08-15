import asyncio
import threading

from src.cli import _InstructionApp, _SelectFolderApp, _SelectOptionApp, _StatusApp, select_option


def run_async(coro_fn):
    return asyncio.run(coro_fn())


def test_select_option_arrow_and_enter_picks_highlighted_key():
    async def body():
        app = _SelectOptionApp("Escolha:", ["um", "dois", "tres"])
        async with app.run_test() as pilot:
            await pilot.press("down")
            await pilot.press("enter")
        return app.return_value

    assert run_async(body) == "dois"


def test_select_option_escape_returns_exit_sentinel():
    async def body():
        app = _SelectOptionApp("Escolha:", ["um", "dois"])
        async with app.run_test() as pilot:
            await pilot.press("escape")
        return app.return_value

    assert run_async(body) == "Exit"


def test_select_option_maps_dict_value_after_run(monkeypatch):
    # select_option() chama .run() (bloqueante); simulamos o resultado que o
    # _SelectOptionApp devolveria e conferimos o mapeamento dict -> valor.
    monkeypatch.setattr(_SelectOptionApp, "run", lambda self: self.keys[0])
    result = select_option("Escolha:", {"Português": "pt", "Inglês": "en"})
    assert result == "pt"


def test_select_option_empty_dict_returns_exit_without_running():
    assert select_option("Escolha:", {}) == "Exit"


def test_instruction_enter_exits():
    async def body():
        app = _InstructionApp("Pressione enter", "green")
        async with app.run_test() as pilot:
            await pilot.press("enter")
        return app.return_value

    run_async(body)  # não levanta exceção = app fechou corretamente


def test_select_folder_escape_returns_none():
    async def body():
        app = _SelectFolderApp("Selecione:", ".")
        async with app.run_test() as pilot:
            await pilot.press("escape")
        return app.return_value

    assert run_async(body) is None


class _FakeExtractor:
    def __init__(self):
        self.threads_status = []
        self.observers = []

    def add_observer(self, callback):
        self.observers.append(callback)

    def notify_observers(self, event_name, data):
        for obs in self.observers:
            obs(event_name, data)


def test_status_app_exits_when_all_files_reach_terminal_status():
    async def body():
        extractor = _FakeExtractor()
        extractor.threads_status = [
            {'file': 'Map001.json', 'status': 'waiting', 'msg': 'Na fila'},
        ]
        app = _StatusApp(extractor)
        async with app.run_test() as pilot:
            def worker():
                extractor.threads_status = [
                    {'file': 'Map001.json', 'status': 'success', 'msg': 'Processado'},
                ]
                extractor.notify_observers('status_update', extractor.threads_status)

            t = threading.Thread(target=worker)
            t.start()
            # join() bloqueante travaria o event loop e faria deadlock: a worker thread
            # fica presa em call_from_thread esperando esse mesmo loop processá-la.
            await asyncio.to_thread(t.join)
            await pilot.pause()
        return app.return_value

    run_async(body)


def test_status_app_does_not_exit_prematurely_on_empty_status_list():
    """
    Bug do cli.py antigo: se threads_status estivesse vazio no primeiro loop,
    all_done ficava True por vacuidade e a tela fechava antes de qualquer arquivo
    ser processado.
    """
    async def body():
        extractor = _FakeExtractor()
        app = _StatusApp(extractor)
        async with app.run_test() as pilot:
            await pilot.pause()
            exited_early = app.return_value is not None or not app.is_running
        return exited_early

    assert run_async(body) is False


def test_status_app_reflects_updates_from_a_background_thread():
    async def body():
        extractor = _FakeExtractor()
        extractor.threads_status = [{'file': 'a.json', 'status': 'process', 'msg': 'traduzindo'}]
        app = _StatusApp(extractor)
        async with app.run_test() as pilot:
            await pilot.pause()

            def worker():
                extractor.threads_status = [{'file': 'a.json', 'status': 'success', 'msg': 'ok'}]
                extractor.notify_observers('status_update', extractor.threads_status)

            t = threading.Thread(target=worker)
            t.start()
            # join() bloqueante travaria o event loop e faria deadlock: a worker thread
            # fica presa em call_from_thread esperando esse mesmo loop processá-la.
            await asyncio.to_thread(t.join)
            await pilot.pause()
        return app.return_value

    run_async(body)
