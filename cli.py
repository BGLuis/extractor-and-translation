from tabulate import tabulate
import sys
import os
import time

# Configurações de Plataforma
IS_WINDOWS = os.name == 'nt'

if IS_WINDOWS:
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

# Cores ANSI
ANSI_COLORS = {
    'reset': '\033[0m',
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
}

def clear_screen():
    os.system('cls' if IS_WINDOWS else 'clear')

def colored_string(text, color='white'):
    code = ANSI_COLORS.get(color, ANSI_COLORS['reset'])
    return f"{code}{text}{ANSI_COLORS['reset']}"

def print_colored_line(text, color='white'):
    print(colored_string(text, color))

def progress_bar(current, total, length=20, fill='█', empty='░', show_percent=True, show_count=True, color=None):
    if total == 0:
        percent = 0
    else:
        percent = current / total

    filled_length = int(length * percent)
    bar = fill * filled_length + empty * (length - filled_length)

    if not color:
        if percent >= 1.0: color = 'green'
        elif percent >= 0.7: color = 'cyan'
        elif percent >= 0.3: color = 'yellow'
        else: color = 'red'

    result = colored_string(bar, color)

    if show_percent:
        result += f" {percent:.0%}"
    if show_count:
        result += f" ({current}/{total})"

    return result

def select_option(title, options, index=0):
    if isinstance(options, dict):
        keys = list(options.keys())
        values = options
    else:
        keys = options
        values = None

    if IS_WINDOWS:
        return _select_option_windows(title, keys, values, index)
    else:
        return _select_option_linux(title, keys, values, index)

# Alias para compatibilidade, caso algum arquivo externo ainda use o nome antigo
select_opition = select_option

def _select_option_windows(title, keys, values, index):
    while True:
        clear_screen()
        print(title)
        for i, key in enumerate(keys):
            if i == index:
                print_colored_line(f"> {key}", 'cyan')
            else:
                print(f"  {key}")

        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'down':
                index = (index + 1) % len(keys)
            elif event.name == 'up':
                index = (index - 1) % len(keys)
            elif event.name == 'enter':
                return values[keys[index]] if values else keys[index]
            elif event.name == 'esc':
                return "Exit"
            time.sleep(0.05)

def _select_option_linux(title, keys, values, index):
    def menu(stdscr):
        nonlocal index
        curses.curs_set(0)
        curses.start_color()
        try:
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)
        except curses.error:
            # Fallback para terminais que não suportam transparência (-1)
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
            elif key_event == 27: # ESC
                return "Exit"

    return curses.wrapper(menu)

def instruction(description, color='green'):
    if IS_WINDOWS:
        print_colored_line(description, color)
        input("Pressione Enter para continuar...")
    else:
        def wait_enter(stdscr):
            stdscr.clear()
            curses.use_default_colors()
            # Mapeamento aproximado de cores
            c_code = getattr(curses, f"COLOR_{color.upper()}", curses.COLOR_WHITE)
            curses.init_pair(2, c_code, -1)
            
            stdscr.addstr(0, 0, description + "\n", curses.color_pair(2))
            stdscr.addstr(2, 0, "Pressione Enter para continuar...")
            stdscr.refresh()
            while True:
                key = stdscr.getch()
                if key in [curses.KEY_ENTER, 10, 13]:
                    break
        curses.wrapper(wait_enter)

def status_color(status):
    map_color = {
        'success': 'green',
        'erro': 'red',
        'danger': 'red',
        'waiting': 'yellow',
        'process': 'cyan',
    }
    return colored_string(status, map_color.get(status, 'white'))

def show_status(threads_status):
    ignore_counts = {}
    
    # Ocultar cursor no Linux para evitar "piscada" visual
    if not IS_WINDOWS:
        print("\033[?25l", end="")

    try:
        while True:
            clear_screen()
            all_done = True
            table = []
            
            for status in threads_status:
                s_code = status.get('status', '')
                file = status.get('file', '')
                
                # Ocultar itens concluídos após um tempo
                if s_code in ['ignore', 'success']:
                    ignore_counts[file] = ignore_counts.get(file, 0) + 1
                    limit = 4 if s_code == 'ignore' else 10
                    if ignore_counts[file] > limit:
                        continue
                
                msg = status.get('msg', '')
                colored_s = status_color(s_code)
                
                if 'current' in status and 'total' in status:
                    prog = progress_bar(status['current'], status['total'], length=10)
                    table.append([file, colored_s, msg, prog])
                else:
                    table.append([file, colored_s, msg])

                if s_code not in ['erro', 'success', 'ignore']:
                    all_done = False
            
            headers = ['File', 'Status', 'Message', 'Progress']
            print(tabulate(table, headers=headers, tablefmt='plain'))

            if all_done:
                break
            time.sleep(1)
    finally:
        # Restaurar cursor
        if not IS_WINDOWS:
            print("\033[?25h", end="")

def select_folder(title="Selecione uma pasta"):
    """
    Usa tkinter (biblioteca padrão) para selecionar pasta.
    Se não disponível (ex: headless), pede input manual.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Inicializa Tkinter root mas esconde a janela principal
        root = tk.Tk()
        root.withdraw()
        
        # Tenta colocar a janela no topo
        root.attributes('-topmost', True)
        
        folder = filedialog.askdirectory(title=title)
        root.destroy()
        
        return folder if folder else None
    except Exception as e:
        # Fallback para input manual em caso de erro (ex: falta de display X11)
        print_colored_line(f"Seletor gráfico indisponível: {e}", 'yellow')
        print_colored_line("Digite o caminho absoluto da pasta:", 'cyan')
        path = input("> ").strip()
        return path if path and os.path.exists(path) else None