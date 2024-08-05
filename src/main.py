import os

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

    for base_file in base_files:
        for lang in os.listdir(root):
            path = get_path(root, lang, base_file.name)
            file = get_file(path, lang)

            translation = file.get_translation(base_file, client, model)

            if not translation:
                continue

            with open(path, "a") as translation_file:
                translation_file.write(translation.get_ftl())


if __name__ == "__main__":
    main()
