from tabulate import tabulate
from PyQt5.QtWidgets import QApplication, QFileDialog
import sys
import os
import time
import curses

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

# Cores para curses
curses_colors = {
    'red': curses.COLOR_RED,
    'green': curses.COLOR_GREEN,
    'yellow': curses.COLOR_YELLOW,
    'blue': curses.COLOR_BLUE,
    'magenta': curses.COLOR_MAGENTA,
    'cyan': curses.COLOR_CYAN,
    'white': curses.COLOR_WHITE,
}

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

def select_opition(Title, options, index=0):
    import curses

    if isinstance(options, dict):
        keys = list(options.keys())
    else:
        keys = options

    def menu(stdscr):
        nonlocal index
        curses.curs_set(0)
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, Title + "\n")
            for i, key in enumerate(keys):
                if i == index:
                    stdscr.addstr(i + 1, 0, f"> {key}\n", curses.color_pair(1))
                else:
                    stdscr.addstr(i + 1, 0, f"  {key}\n")
            stdscr.refresh()
            key_event = stdscr.getch()
            if key_event == curses.KEY_DOWN:
                index = (index + 1) % len(keys)
            elif key_event == curses.KEY_UP:
                index = (index - 1) % len(keys)
            elif key_event in [curses.KEY_ENTER, 10, 13]:
                if isinstance(options, dict):
                    return options[keys[index]]
                else:
                    return keys[index]
            elif key_event == 27:  # ESC
                return "Exit"

    def wrapper(stdscr):
        curses.start_color()
        try:
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)
        except curses.error:
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        return menu(stdscr)

    return curses.wrapper(wrapper)

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
            table.append([status['file'], status_color(status['status']), status['msg']])
            if status['status'] not in ['erro', 'success', 'ignore']:
                all_done = False
        print(tabulate(table, headers=['File', 'Status', 'Message'], tablefmt='plain'))
        if all_done:
            break
        time.sleep(1)

def select_folder(title="Selecione uma pasta"):
    app = QApplication(sys.argv)
    folder = QFileDialog.getExistingDirectory(None, title)
    if folder:
        return folder
    return None
