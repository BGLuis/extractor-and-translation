from tabulate import tabulate
import sys
import os
import time

if os.name == 'nt':
    try:
        import keyboard
    except ImportError:
        print("ERRO: biblioteca 'keyboard' não instalada.")
        print("Execute: pip install keyboard")
        sys.exit(1)
else:
    try:
        import curses
    except ImportError:
        print("ERRO: biblioteca 'curses' não disponível.")
        sys.exit(1)

# Cores ANSI para terminal normal
ansi_colors = {
    'reset': '\033[0m',
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
}

# Cores para curses (apenas se disponível)
if os.name != 'nt':
    curses_colors = {
        'red': curses.COLOR_RED,
        'green': curses.COLOR_GREEN,
        'yellow': curses.COLOR_YELLOW,
        'blue': curses.COLOR_BLUE,
        'magenta': curses.COLOR_MAGENTA,
        'cyan': curses.COLOR_CYAN,
        'white': curses.COLOR_WHITE,
    }
else:
    curses_colors = {}  # Não usado no Windows

def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def print_colored_line(text, color='white'):
    color_code = ansi_colors.get(color, ansi_colors['reset'])
    print(f"{color_code}{text}{ansi_colors['reset']}")

def colored_string(text, color='white'):
    color_code = ansi_colors.get(color, ansi_colors['reset'])
    return f"{color_code}{text}{ansi_colors['reset']}"


def progress_bar(current, total, length=20, fill='█', empty='░', show_percent=True, show_count=True, color=None):
    if total == 0:
        percent = 0
    else:
        percent = current / total

    filled_length = int(length * percent)
    bar = fill * filled_length + empty * (length - filled_length)

    # Aplicar cor se especificada
    if color:
        bar = colored_string(bar, color)
    elif percent >= 1.0:
        bar = colored_string(bar, 'green')
    elif percent >= 0.7:
        bar = colored_string(bar, 'cyan')
    elif percent >= 0.3:
        bar = colored_string(bar, 'yellow')
    else:
        bar = colored_string(bar, 'red')

    # Montar string final
    result = bar

    if show_percent:
        percent_str = f" {percent:.0%}"
        result += percent_str

    if show_count:
        count_str = f" ({current}/{total})"
        result += count_str

    return result

def select_opition(Title, options, index=0):

    if isinstance(options, dict):
        keys = list(options.keys())
        values = options
    else:
        keys = options
        values = None

    if os.name == 'nt':
        return _select_option_windows(Title, keys, values, index)
    else:
        return _select_option_linux(Title, keys, values, index)


def _select_option_windows(title, keys, values, index):
    # keyboard está disponível apenas no Windows
    while True:
        clear_screen()
        print(title)
        for i, key in enumerate(keys):
            if i == index:
                print_colored_line(f"> {key}", 'cyan')
            else:
                print(f"  {key}")

        event = keyboard.read_event()  # type: ignore
        if event.event_type == keyboard.KEY_DOWN:  # type: ignore
            if event.name == 'down':
                index = (index + 1) % len(keys)
            elif event.name == 'up':
                index = (index - 1) % len(keys)
            elif event.name == 'enter':
                return values[keys[index]] if values else keys[index]
            elif event.name == 'esc':
                return "Exit"


def _select_option_linux(title, keys, values, index):
    def menu(stdscr):
        nonlocal index
        curses.curs_set(0)
        curses.start_color()

        try:
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)
        except curses.error:
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, title + "\n")

            for i, key in enumerate(keys):
                prefix = "> " if i == index else "  "
                attr = curses.color_pair(1) if i == index else curses.A_NORMAL
                stdscr.addstr(i + 1, 0, f"{prefix}{key}\n", attr)

            stdscr.refresh()
            key_event = stdscr.getch()

            if key_event == curses.KEY_DOWN:
                index = (index + 1) % len(keys)
            elif key_event == curses.KEY_UP:
                index = (index - 1) % len(keys)
            elif key_event in [curses.KEY_ENTER, 10, 13]:
                return values[keys[index]] if values else keys[index]
            elif key_event == 27:  # ESC
                return "Exit"

    return curses.wrapper(menu)

def instruction(description, color='green'):
    def wait_enter(stdscr):
        stdscr.clear()
        curses.use_default_colors()

        curses.init_pair(2, curses_colors.get(color, curses.COLOR_WHITE),-1)
        stdscr.addstr(0, 0, description + "\n", curses.color_pair(2))
        stdscr.addstr(2, 0, "Pressione Enter para continuar...")
        stdscr.refresh()
        while True:
            key = stdscr.getch()
            if key in [curses.KEY_ENTER, 10, 13]:
                break
    curses.wrapper(wait_enter)

def status_color(status):
    if status == 'success':
        return colored_string(status, 'green')
    elif status == 'erro':
        return colored_string(status, 'red')
    elif status == 'danger':
        return colored_string(status, 'red')
    elif status == 'waiting':
        return colored_string(status, 'yellow')
    elif status == 'process':
        return colored_string(status, 'cyan')
    else:
        return colored_string(status, 'white')

def show_status(threads_status):
    ignore_counts = {}
    while True:
        clear_screen()
        all_done = True
        table = []
        for status in threads_status:
            if status['status'] == 'ignore':
                file = status['file']
                if file not in ignore_counts:
                    ignore_counts[file] = 0
                ignore_counts[file] += 1
                if ignore_counts[file] > 4:
                    continue

            if status['status'] == 'success':
                file = status['file']
                if file not in ignore_counts:
                    ignore_counts[file] = 0
                ignore_counts[file] += 1
                if ignore_counts[file] > 10:
                    continue

            if 'current' in status and 'total' in status:
                progress = progress_bar(status['current'], status['total'], length=10)
                table.append([
                    status['file'],
                    status_color(status['status']),
                    status['msg'],
                    progress,
                ])
            else:
                table.append([status['file'], status_color(status['status']), status['msg']])

            if status['status'] not in ['erro', 'success', 'ignore']:
                all_done = False
            print(tabulate(table, headers=['File', 'Status', 'Message'], tablefmt='plain'))

        if all_done:
            break
        time.sleep(1)

def _lazy_import_pyqt():
    """Import PyQt5 apenas quando necessário"""
    try:
        from PyQt5.QtWidgets import QApplication, QFileDialog
        return QApplication, QFileDialog
    except ImportError:
        print_colored_line("ERRO: PyQt5 não instalado.", 'red')
        print_colored_line("Execute: pip install PyQt5", 'yellow')
        return None, None


def select_folder(title="Selecione uma pasta"):
    """
    Abre diálogo para seleção de pasta

    Args:
        title: Título da janela

    Returns:
        Caminho da pasta ou None se cancelado/erro
    """
    QApplication, QFileDialog = _lazy_import_pyqt()
    if not QApplication or not QFileDialog:
        return None

    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        folder = QFileDialog.getExistingDirectory(None, title)
        return folder if folder else None

    except Exception as e:
        print_colored_line(f"Erro ao abrir seletor de pasta: {e}", 'red')
        print_colored_line("Dica: Digite o caminho manualmente", 'yellow')
        return None
