from tabulate import tabulate
import os
import time
import keyboard


colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }

def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def print_colored_line(text, color='white'):
    color_code = colors.get(color, colors['reset'])
    print(f"{color_code}{text}{colors['reset']}")

def colored_string(text, color='white'):
    color_code = colors.get(color, colors['reset'])
    return f"{color_code}{text}{colors['reset']}"

def select_opition(Title, options, index=0):
    if isinstance(options, dict):
        keys = list(options.keys())
    else:
        keys = options

    while True:
        clear_screen()
        print(Title)
        for i, key in enumerate(keys):
            if i == index:
                print_colored_line(key, 'cyan')
            else:
                print(key)

        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'down':
                index = (index + 1) % len(keys)
            elif event.name == 'up':
                index = (index - 1) % len(keys)
            elif event.name == 'enter':
                if isinstance(options, dict):
                    return options[keys[index]]
                else:
                    return keys[index]
            elif event.name == 'esc':
                return "Exit"

def instruction(description, color='green'):
    print_colored_line(description, color)
    while True:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN and event.name == 'enter':
            break

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