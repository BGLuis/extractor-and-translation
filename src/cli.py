import os

from rich.console import Console
from rich.text import Text

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, DirectoryTree, Footer, OptionList, Static
from textual.widgets.option_list import Option

STYLE_MAP = {
    'reset': 'default', 'red': 'red', 'green': 'green', 'yellow': 'yellow',
    'blue': 'blue', 'magenta': 'magenta', 'cyan': 'cyan', 'white': 'white',
}

_console = Console()


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


class _SelectOptionApp(App):
    BINDINGS = [Binding("escape", "cancel", "Sair")]
    CSS = "OptionList { height: 1fr; } #prompt-title { padding: 1 2; }"

    def __init__(self, title, keys, index=0):
        super().__init__()
        self.title_text = title
        self.keys = keys
        self.initial_index = index

    def compose(self) -> ComposeResult:
        yield Static(self.title_text, id="prompt-title")
        yield OptionList(*[Option(str(k)) for k in self.keys])
        yield Footer()

    def on_mount(self) -> None:
        option_list = self.query_one(OptionList)
        if 0 <= self.initial_index < len(self.keys):
            option_list.highlighted = self.initial_index
        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.exit(self.keys[event.option_index])

    def action_cancel(self) -> None:
        self.exit("Exit")


def select_option(title, options, index=0):
    """Aceita um dict (mostra as chaves, retorna o valor) ou uma lista (retorna o item)."""
    if isinstance(options, dict):
        keys = list(options.keys())
        values = options
    else:
        keys = list(options)
        values = None

    if not keys:
        return "Exit"

    result = _SelectOptionApp(title, keys, index).run()
    if result is None or result == "Exit":
        return "Exit"
    return values[result] if values is not None else result


class _InstructionApp(App):
    BINDINGS = [Binding("enter", "confirm", "Continuar")]
    CSS = "#instruction-text { padding: 1 2; }"

    def __init__(self, description, color):
        super().__init__()
        self.description = description
        self.color = color

    def compose(self) -> ComposeResult:
        yield Static(colored_string(self.description, self.color), id="instruction-text")
        yield Footer()

    def action_confirm(self) -> None:
        self.exit()


def instruction(description, color='green'):
    _InstructionApp(description, color).run()


class _SelectFolderApp(App):
    BINDINGS = [
        Binding("escape", "cancel", "Cancelar"),
        Binding("s", "confirm", "Selecionar esta pasta"),
    ]

    def __init__(self, title, start_path):
        super().__init__()
        self.title_text = title
        self.start_path = start_path

    def compose(self) -> ComposeResult:
        yield Static(self.title_text)
        yield DirectoryTree(self.start_path)
        yield Footer()

    def action_confirm(self) -> None:
        node = self.query_one(DirectoryTree).cursor_node
        if node is not None and node.data is not None and node.data.path.is_dir():
            self.exit(str(node.data.path))

    def action_cancel(self) -> None:
        self.exit(None)


def select_folder(title="Selecione uma pasta"):
    return _SelectFolderApp(title, os.getcwd()).run()


class _StatusApp(App):
    def __init__(self, extractor):
        super().__init__()
        self.extractor = extractor

    def compose(self) -> ComposeResult:
        table = DataTable()
        table.add_columns("Arquivo", "Status", "Mensagem", "Progresso")
        yield table
        yield Footer()

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


def show_status(extractor):
    _StatusApp(extractor).run()
