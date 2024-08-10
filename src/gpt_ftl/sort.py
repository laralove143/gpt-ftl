from fluent.syntax import parse
from fluent.syntax.ast import Message

from gpt_ftl.ftl_file import get_paths
from gpt_ftl.parser import MessageParser
from gpt_ftl.print_colored import (
    print_action_start,
    print_batch_action,
    format_value,
    print_error,
)


def sort_messages(content, separate):
    body = parse(content).body
    new_content = ""

    message_parsers = []
    for elem in body:
        if not isinstance(elem, Message):
            print_error("Only message comments are supported when sorting messages.")
            exit(1)

        message_parsers.append(MessageParser(ftl_content=content, ftl_message=elem))

    message_parsers_sorted = sorted(message_parsers, key=lambda p: p.identifier)

    for parser in message_parsers_sorted:
        new_content += parser.get_ftl() + "\n"
        if separate:
            new_content += "\n"

    if new_content.endswith("\n\n"):
        new_content = new_content[:-1]

    return new_content


def main(config):
    print_action_start("Sorting messages...")

    paths = get_paths(config.root)

    for i, path in enumerate(paths):
        print_batch_action(
            f"Sorting messages in {format_value(path)}...", i + 1, len(paths)
        )

        with open(path, "r") as f:
            content = sort_messages(f.read(), config.separate)

        with open(path, "w") as f:
            f.write(content)
