import os

from rich.console import Console
from rich.text import Text

from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.widgets import DataTable, DirectoryTree, Footer, OptionList, Static
from textual.widgets.option_list import Option

from src.i18n import LANGUAGES, Translator
from src.services.SettingsStore import SettingsStore

STYLE_MAP = {
    'reset': 'default', 'red': 'red', 'green': 'green', 'yellow': 'yellow',
    'blue': 'blue', 'magenta': 'magenta', 'cyan': 'cyan', 'white': 'white',
}

_console = Console()
_settings = SettingsStore()
_i18n = Translator(_settings.get('ui_language'))


def colored_string(text, color='white'):
    return Text(text, style=STYLE_MAP.get(color, 'white'))


def print_colored_line(text, color='white'):
    _console.print(colored_string(text, color))


def clear_screen():
    _console.clear()


def status_color(status):
    return {
        'success': 'green', 'erro': 'red', 'danger': 'red',
        'waiting': 'yellow', 'process': 'cyan',
    }.get(status, 'white')


class _LanguagePaletteMixin:
    """Expõe comandos de troca de idioma no Command Palette (ctrl+p) nativo do Textual."""

    def get_system_commands(self, screen):
        yield from super().get_system_commands(screen)
        for code, name in LANGUAGES.items():
            if code != _i18n.language:
                yield SystemCommand(
                    f"{_i18n.tr('label_ui_language')} {name}", name,
                    lambda code=code: self._change_ui_language(code),
                )

    def _change_ui_language(self, code):
        _i18n.set_language(code)
        _settings.set('ui_language', code)
        self._apply_language()

    def _apply_language(self):
        """Sobrescrito nas subclasses para atualizar os textos já renderizados na tela atual."""


class _SelectOptionApp(_LanguagePaletteMixin, App):
    BINDINGS = [Binding("escape", "cancel", _i18n.tr('cli_binding_quit'))]
    CSS = "OptionList { height: 1fr; } #prompt-title { padding: 1 2; }"

    def __init__(self, title, options, index=0):
        super().__init__()
        self._title_source = title
        self._options_source = options
        self.initial_index = index
        self.keys, self.values = self._resolve_options()

    def _resolve_options(self):
        options = self._options_source() if callable(self._options_source) else self._options_source
        if isinstance(options, dict):
            return list(options.keys()), options
        return list(options), None

    def _resolve_title(self):
        return self._title_source() if callable(self._title_source) else self._title_source

    def compose(self) -> ComposeResult:
        yield Static(self._resolve_title(), id="prompt-title")
        yield OptionList(*[Option(str(k)) for k in self.keys])
        yield Footer()

    def on_mount(self) -> None:
        option_list = self.query_one(OptionList)
        if 0 <= self.initial_index < len(self.keys):
            option_list.highlighted = self.initial_index
        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_key = self.keys[event.option_index]
        self.exit(self.values[selected_key] if self.values is not None else selected_key)

    def action_cancel(self) -> None:
        self.exit("Exit")

    def _apply_language(self):
        option_list = self.query_one(OptionList)
        highlighted = option_list.highlighted
        self.keys, self.values = self._resolve_options()
        self.query_one("#prompt-title", Static).update(self._resolve_title())
        option_list.clear_options()
        option_list.add_options([Option(str(k)) for k in self.keys])
        if highlighted is not None and highlighted < len(self.keys):
            option_list.highlighted = highlighted
        self.bind("escape", "cancel", description=_i18n.tr('cli_binding_quit'))
        self.refresh_bindings()


def select_option(title, options, index=0):
    """Aceita título/opções fixos ou callables sem argumento (retraduzidos ao trocar
    o idioma pela paleta de comandos). ``options`` pode ser um dict (mostra as
    chaves, retorna o valor) ou uma lista (retorna o item)."""
    initial_options = options() if callable(options) else options
    keys = list(initial_options.keys()) if isinstance(initial_options, dict) else list(initial_options)

    if not keys:
        return "Exit"

    result = _SelectOptionApp(title, options, index).run()
    if result is None:
        return "Exit"
    return result


class _InstructionApp(_LanguagePaletteMixin, App):
    BINDINGS = [Binding("enter", "confirm", _i18n.tr('cli_binding_continue'))]
    CSS = "#instruction-text { padding: 1 2; }"

    def __init__(self, description, color):
        super().__init__()
        self._description_source = description
        self.color = color

    def _resolve_description(self):
        return self._description_source() if callable(self._description_source) else self._description_source

    def compose(self) -> ComposeResult:
        yield Static(colored_string(self._resolve_description(), self.color), id="instruction-text")
        yield Footer()

    def action_confirm(self) -> None:
        self.exit()

    def _apply_language(self):
        self.query_one("#instruction-text", Static).update(colored_string(self._resolve_description(), self.color))
        self.bind("enter", "confirm", description=_i18n.tr('cli_binding_continue'))
        self.refresh_bindings()


def instruction(description, color='green'):
    """``description`` aceita um valor fixo ou um callable sem argumento (retraduzido
    ao trocar o idioma pela paleta de comandos)."""
    _InstructionApp(description, color).run()


class _SelectFolderApp(_LanguagePaletteMixin, App):
    BINDINGS = [
        Binding("escape", "cancel", _i18n.tr('cli_binding_cancel')),
        Binding("s", "confirm", _i18n.tr('cli_binding_select_folder')),
    ]

    def __init__(self, title, start_path):
        super().__init__()
        self._title_source = title
        self.start_path = start_path

    def _resolve_title(self):
        return self._title_source() if callable(self._title_source) else self._title_source

    def compose(self) -> ComposeResult:
        yield Static(self._resolve_title(), id="folder-title")
        yield DirectoryTree(self.start_path)
        yield Footer()

    def action_confirm(self) -> None:
        node = self.query_one(DirectoryTree).cursor_node
        if node is not None and node.data is not None and node.data.path.is_dir():
            self.exit(str(node.data.path))

    def action_cancel(self) -> None:
        self.exit(None)

    def _apply_language(self):
        self.query_one("#folder-title", Static).update(self._resolve_title())
        self.bind("escape", "cancel", description=_i18n.tr('cli_binding_cancel'))
        self.bind("s", "confirm", description=_i18n.tr('cli_binding_select_folder'))
        self.refresh_bindings()


def select_folder(title=None):
    """``title`` aceita um valor fixo ou um callable sem argumento (retraduzido ao
    trocar o idioma pela paleta de comandos)."""
    return _SelectFolderApp(title or (lambda: _i18n.tr('cli_default_select_folder_title')), os.getcwd()).run()


class _StatusApp(_LanguagePaletteMixin, App):
    def __init__(self, extractor):
        super().__init__()
        self.extractor = extractor

    def compose(self) -> ComposeResult:
        table = DataTable()
        self._add_columns(table)
        yield table
        yield Footer()

    def _add_columns(self, table):
        table.add_columns(
            _i18n.tr('cli_table_file'), _i18n.tr('cli_table_status'),
            _i18n.tr('cli_table_message'), _i18n.tr('cli_table_progress'),
        )

    def on_mount(self) -> None:
        self.extractor.add_observer(self._on_extractor_event)
        self._refresh(self.extractor.threads_status)

    def _on_extractor_event(self, event_name, data) -> None:
        if event_name == 'status_update':
            self.call_from_thread(self._refresh, data)

    def _refresh(self, status_list) -> None:
        table = self.query_one(DataTable)
        table.clear()
        all_done = True
        for status in status_list:
            s_code = status.get('status', '')
            file_name = os.path.basename(status.get('file', ''))
            msg = status.get('msg', '')
            progress = ''
            if 'current' in status and 'total' in status:
                progress = f"{status['current']}/{status['total']}"
            table.add_row(file_name, Text(s_code, style=status_color(s_code)), msg, progress)
            if s_code not in ('erro', 'success', 'ignore'):
                all_done = False

        if status_list and all_done:
            self.exit()

    def _apply_language(self):
        table = self.query_one(DataTable)
        status_list = list(self.extractor.threads_status)
        table.clear(columns=True)
        self._add_columns(table)
        self._refresh(status_list)


def show_status(extractor):
    _StatusApp(extractor).run()
