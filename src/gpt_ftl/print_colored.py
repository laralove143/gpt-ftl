from threading import Lock

from colorama import Style, Fore


lock = Lock()


def format_value(s):
    return Style.BRIGHT + s + Style.NORMAL


def format_list(l):
    return "\n".join([f"- {format_value(elem)}" for elem in l])


def format_footer(s):
    return Style.DIM + s + Style.NORMAL


def footer():
    return format_footer(
        "Made with ❤️ by Lara Kayaalp. \nIf you enjoy using this tool, consider supporting me at "
        "https://sponsor.lara.lv."
    )


def print_warning(s):
    print_with_lock(Fore.YELLOW + s)


def print_error(s):
    print_with_lock(Fore.RED + s)


def print_action_start(s):
    print_with_lock(Fore.BLUE + s)


def print_action_done(s):
    print_with_lock(Fore.GREEN + s)


def print_batch_action(s, i, length):
    print_with_lock(Fore.BLUE + s + Style.DIM + f" ({i}/{length})")


def print_with_lock(s):
    with lock:
        print(s)
