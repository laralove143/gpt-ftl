import os
from threading import Thread

import colorama
from dotenv import load_dotenv
from openai import OpenAI
from os import environ

from ftl_file import get_base_files, get_file, get_path
from print_colored import (
    print_action_start,
    print_action_done,
    print_batch_action,
    format_value,
    format_dict,
    format_list,
)


def main():
    colorama.init(autoreset=True)

    print_action_start(format_value("Welcome to GPT FTL!"))

    print_action_start("Loading configuration...")
    load_dotenv()
    base_lang = environ.get("BASE_LANG")
    model = environ.get("MODEL")
    root = environ.get("FTL_ROOT_PATH")
    print_action_done(
        f"Configuration loaded:\n{format_dict({
            "Base language": base_lang,
            "Model": model,
            "FTL Root Path": root,
        })}"
    )

    client = OpenAI()

    print_action_start("Getting files to translate...")
    base_files = get_base_files(root, base_lang)
    print_action_done(
        f"Files to translate:\n{format_list([file.name for file in base_files])}"
    )

    print_action_start("Getting target languages...")
    langs = [lang for lang in os.listdir(root) if lang != base_lang]
    print_action_done(f"Target languages:\n{format_list(langs)}")

    threads = []
    for file_idx, base_file in enumerate(base_files):
        for lang_idx, lang in enumerate(langs):
            path = get_path(root, lang, base_file.name)
            file = get_file(path, lang)

            thread = Thread(
                target=file.write_translation, args=(base_file, root, client, model)
            )

            print_batch_action(
                f"Translating {format_value(base_file.name)} to {format_value(lang)} in parallel...",
                len(threads) + 1,
                len(base_files) * len(langs),
            )
            thread.start()
            threads.append(thread)

    for i, thread in enumerate(threads):
        thread.join()
        file_str = "files" if i + 1 > 1 else "file"
        print_batch_action(f"Translated {i + 1} {file_str}...", i + 1, len(threads))


if __name__ == "__main__":
    main()
