import os

from gpt_ftl.print_colored import print_action_start, format_value, print_batch_action


def main(config):
    print_action_start("Stripping comments...")

    paths = []
    for [dirname, _, filenames] in os.walk(config.root):
        paths += [
            os.path.join(dirname, filename)
            for filename in filenames
            if filename.endswith(".ftl")
        ]

    for i, path in enumerate(paths):
        print_batch_action(
            f"Stripping comments from {format_value(path)}...", i + 1, len(paths)
        )
        with open(path, "r") as f:
            content = strip_comments(f.read())

        with open(path, "w") as f:
            f.write(content)


def strip_comments(content):
    new_content = ""

    lines = content.splitlines()
    for i, line in enumerate(lines):
        if is_comment(line):
            continue
        elif line == "":
            last_non_empty_line_idx = i - 1
            while lines[last_non_empty_line_idx] == "" and last_non_empty_line_idx > 0:
                last_non_empty_line_idx -= 1
            if is_comment(lines[last_non_empty_line_idx]):
                continue

        new_content += line + "\n"

    return new_content


def is_comment(line):
    return line.startswith("#")