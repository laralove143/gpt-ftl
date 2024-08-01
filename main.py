import json
import os
import sqlite3

import fluent.syntax.ast
from fluent.syntax import parse
from dotenv import load_dotenv
from fluent.syntax.ast import (
    ResourceComment,
    GroupComment,
    Comment,
    Placeable,
    SelectExpression,
)
from openai import OpenAI
from os import environ


all_system_messages = {
    "role": "You are a translator designed to output in JSON.",
    "multi_lang": "The top level keys in your JSON are the language codes of the languages you are translating to.",
    "assignment": "You are given a file in Fluent format which has variable name and source pairs separated by =. Each \
    variable name is the JSON key, and the value of that key is the translation of source. Do not translate the keys.",
    "selection": "If the source you are given translates to different text based on a variable, shown with the syntax \
    { variable -> [variant] source_text }, the JSON value you output must be a list of JSON objects with 4 keys: \
    variable, variant, translation, is_default. variable key's value must be the variable name in the source, do not \
    change this. variant key's value must be the variant in the source, do not change this. translation key's value \
    must be the translation for that variant, only translate this. is_default key's value must be true for the \
    translation that is the default translation. There must be one and only one default value.",
    "single_hash_comment": "In the content you are given, there might be comment lines starting with # above a value, "
    "this line provides you context about the value it precedes, use this context to output better translations.",
    "double_hash_comment": "In the content you are given, lines starting with ## describe the section of the content "
    "until the next lines starting with ## or the end of content. Use this description to "
    "output better translations of the section the line describes. ",
    "triple_hash_comment": "In the content you are given, lines starting with ### describe the entire content. Use "
    "this description to output better translations of the entire content.",
    "placeable": "Text wrapped in { and } is a placeable, do not alter the text inside the placeable.",
}


class FtlFile:
    def __init__(self, file):
        self.body = parse(file.read()).body
        self.content = file.read()

    def get_translations(self, client, model, system_messages, languages):
        if any(isinstance(elem, ResourceComment) for elem in self.body):
            system_messages.append(all_system_messages["triple_hash_comment"])
        if any(isinstance(elem, GroupComment) for elem in self.body):
            system_messages.append(all_system_messages["double_hash_comment"])
        if any(isinstance(elem, Comment) for elem in self.body):
            system_messages.append(all_system_messages["single_hash_comment"])

        for message in self.body:
            if not isinstance(message, fluent.syntax.ast.Message):
                continue
            for elem in message.value.elements:
                if not isinstance(elem, Placeable):
                    continue
                system_messages.append(all_system_messages["placeable"])
                if isinstance(elem.expression, SelectExpression):
                    system_messages.append(all_system_messages["selection"])
                    break

        messages = [
            {"role": "system", "content": content} for content in system_messages
        ]

        messages.append(
            {
                "role": "user",
                "content": f"Translate the following text to {', '.join(languages)}:\n{self.content}",
            }
        )

        translations = json.loads(
            client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            .choices[0]
            .message.content
        )

        return [Translation(translation) for translation in translations.items()]


class Translation:
    def __init__(self, translation):
        self.language = translation[0]
        self.messages = [Message(message) for message in translation[1].items()]

    def get_ftl(self):
        return "\n".join(message.message() for message in self.messages) + "\n"


class Message:
    def __init__(self, message):
        self.identifier = message[0]

        val = message[1]

        if isinstance(val, str):
            self.value = val

        if isinstance(val, list):
            self.value = Selection(val).value()

    def message(self):
        return f"{self.identifier} = {self.value}"


class Selection:
    def __init__(self, val):
        self.variable = val[0]["variable"]
        self.variants = [Variant(variant) for variant in val]

        for i, variant in enumerate(self.variants.copy()):
            if variant.is_default:
                continue

            if variant.translation == self.default().translation:
                self.variants.pop(i)

    def default(self):
        return next(variant for variant in self.variants if variant.is_default)

    def value(self):
        if len(self.variants) == 1:
            return self.variants[0].translation

        value = f"{{ {self.variable} ->\n"

        for variant in self.variants:
            value += "    "

            if variant.is_default:
                value += "*"

            value += f"[{variant.variant}] {variant.translation}\n"

        value += "}"

        return value


class Variant:
    def __init__(self, val):
        self.variant = val["variant"]
        self.translation = val["translation"]
        self.is_default = val["is_default"]


class Db:
    def __init__(self):
        self.conn = sqlite3.connect("cache.sqlite")
        self.c = self.conn.cursor()
        self.c.execute(
            "CREATE TABLE IF NOT EXISTS translated_messages (identifier TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.conn.commit()


def main():
    load_dotenv()
    base_lang = environ.get("BASE_LANG")
    model = environ.get("MODEL")
    root = environ.get("FTL_ROOT_PATH")

    client = OpenAI()

    system_messages = [
        all_system_messages["role"],
        all_system_messages["multi_lang"],
        all_system_messages["assignment"],
    ]

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

            translations = ftl_file.get_translations(
                client, model, system_messages.copy(), languages
            )

            for translation in translations:
                with open(
                    os.path.join(root, translation.language, os.path.basename(f.name)),
                    "w",
                ) as translation_file:
                    translation_file.write(translation.get_ftl())


if __name__ == "__main__":
    main()
