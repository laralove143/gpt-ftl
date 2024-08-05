import os
from threading import Thread

from dotenv import load_dotenv
from openai import OpenAI
from os import environ

from src.ftl_file import get_base_files, get_file, get_path


def main():
    load_dotenv()
    base_lang = environ.get("BASE_LANG")
    model = environ.get("MODEL")
    root = environ.get("FTL_ROOT_PATH")

    client = OpenAI()

    base_files = get_base_files(root, base_lang)

    threads = []
    for base_file in base_files:
        for lang in os.listdir(root):
            if lang == base_lang:
                continue

            path = get_path(root, lang, base_file.name)
            file = get_file(path, lang)

            thread = Thread(
                target=file.write_translation, args=(base_file, root, client, model)
            )
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
