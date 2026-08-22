import asyncio
import threading

import src.cli as cli_module
from src.cli import _InstructionApp, _SelectFolderApp, _SelectOptionApp, _StatusApp, select_option
from src.i18n import LANGUAGES, Translator


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


def test_select_option_maps_dict_value_after_run():
    # _SelectOptionApp agora resolve o mapeamento dict -> valor internamente
    # (necessário para poder re-resolver as opções ao trocar de idioma pela
    # paleta de comandos), então simulamos a seleção via Pilot em vez de
    # inspecionar o retorno bruto de .run().
    async def body():
        app = _SelectOptionApp("Escolha:", {"Português": "pt", "Inglês": "en"})
        async with app.run_test() as pilot:
            await pilot.press("enter")
        return app.return_value

    assert run_async(body) == "pt"


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


def test_language_palette_command_retranslates_current_screen_live(monkeypatch):
    # Trocar o idioma pela paleta de comandos (ctrl+p) não deve exigir reiniciar
    # a tela: o título e as opções já visíveis precisam refletir o novo idioma
    # assim que o comando é executado, sem fechar e reabrir a tela.
    persisted = {}
    monkeypatch.setattr(cli_module._settings, "set", lambda key, value: persisted.__setitem__(key, value))
    original_language = cli_module._i18n.language
    other_code = next(code for code in LANGUAGES if code != original_language)

    async def body():
        app = _SelectOptionApp(lambda: cli_module._i18n.tr('label_ui_language'), ["um", "dois"])
        async with app.run_test() as pilot:
            commands = list(app.get_system_commands(app.screen))
            target = next(c for c in commands if c.title.endswith(LANGUAGES[other_code]))
            target.callback()
            await pilot.pause()
            title_text = app.query_one("#prompt-title").render()
        return str(title_text), cli_module._i18n.language

    try:
        title_text, language_after_switch = run_async(body)
    finally:
        cli_module._i18n.set_language(original_language)

    assert language_after_switch == other_code
    assert persisted.get('ui_language') == other_code
    assert title_text == Translator(other_code).tr('label_ui_language')


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


def test_select_folder_input_valid_submits(tmp_path):
    async def body():
        app = _SelectFolderApp("Selecione:", ".", initial_input=str(tmp_path))
        async with app.run_test() as pilot:
            await pilot.press("enter")
        return app.return_value

    assert run_async(body) == str(tmp_path)


def test_select_folder_input_invalid_shows_error():
    async def body():
        app = _SelectFolderApp("Selecione:", ".", initial_input="/caminho_inexistente_12345")
        async with app.run_test() as pilot:
            await pilot.press("enter")
            err = app.query_one("#error-label").render()
            await pilot.press("escape")
        return str(err), app.return_value

    err_text, return_val = run_async(body)
    assert "não encontrada" in err_text or "not found" in err_text
    assert return_val is None


def test_select_folder_tree_selection(tmp_path):
    async def body():
        app = _SelectFolderApp("Selecione:", str(tmp_path))
        async with app.run_test() as pilot:
            tree = app.query_one(cli_module.DirectoryTree)
            tree.focus()
            await pilot.press("s")
        return app.return_value

    res = run_async(body)
    assert res is not None


def test_select_folder_with_clipboard(monkeypatch, tmp_path):
    import os
    valid_folder = str(tmp_path)
    monkeypatch.setattr(cli_module, "get_clipboard_folder", lambda: valid_folder)
    monkeypatch.setattr(cli_module, "select_option", lambda title, options: "clipboard")

    selected = cli_module.select_folder()
    assert selected == valid_folder


def test_status_app_sorts_processing_files_on_top():
    async def body():
        extractor = _FakeExtractor()
        extractor.threads_status = [
            {'file': 'Map001.json', 'status': 'waiting', 'msg': 'Na fila'},
            {'file': 'Map002.json', 'status': 'success', 'msg': 'Concluído'},
            {'file': 'Map003.json', 'status': 'process', 'msg': 'Traduzindo...'},
            {'file': 'Map004.json', 'status': 'waiting', 'msg': 'Na fila'},
        ]
        app = _StatusApp(extractor)
        async with app.run_test() as pilot:
            table = app.query_one(cli_module.DataTable)
            # Lê a primeira linha da tabela
            first_row_file = table.get_row_at(0)[0]
            await pilot.pause()
        return first_row_file

    first_file = run_async(body)
    assert first_file == "Map003.json"


