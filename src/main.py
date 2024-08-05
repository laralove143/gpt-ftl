import os

from ftl_file import FtlFile
from db import Db

from dotenv import load_dotenv
from openai import OpenAI
from os import environ


def main():
    load_dotenv()
    base_lang = environ.get("BASE_LANG")
    model = environ.get("MODEL")
    root = environ.get("FTL_ROOT_PATH")

    client = OpenAI()
    db = Db()

    base_files = [
        filename
        for filename in os.listdir(os.path.join(root, base_lang))
        if filename.endswith(".ftl")
    ]

    languages = [
        lang
        for lang in os.listdir(root)
        if os.path.isdir(os.path.join(root, lang)) and lang != base_lang
    ]

    for file in base_files:
        with open(os.path.join(root, base_lang, file), "r") as f:
            ftl_file = FtlFile(f)
            ftl_file.exclude_cached(db)

            translations = ftl_file.get_translations(client, model, languages)

            for translation in translations:
                with open(
                    os.path.join(root, translation.language, os.path.basename(f.name)),
                    "w",
                ) as translation_file:
                    translation_file.write(translation.get_ftl())

            db.insert_ftl_file(ftl_file)


if __name__ == "__main__":
    main()
