import json
import os

from parser import Parser, MessageParser
from system_messages import get_system_messages_for_body

from fluent.syntax import parse
from fluent.syntax.ast import Message


class FtlFile:
    def __init__(self, file, lang):
        self.name = os.path.basename(file.name)
        self.content = file.read()
        self.lang = lang

        self.message_identifiers = []
        for message in parse(self.content).body:
            if not isinstance(message, Message):
                continue

            self.message_identifiers.append(message.id.name)

    def get_translation(self, base_file, client, model):
        translate_messages = base_file.messages_to_translate(self.message_identifiers)
        if not translate_messages:
            return None

        translate_content = "\n".join(
            message.get_ftl() for message in translate_messages
        )

        messages = get_system_messages_for_body(base_file.body)

        messages.append(
            {
                "role": "user",
                "content": f"Translate the following text to {self.lang}:\n{translate_content}",
            }
        )

        translation = json.loads(
            client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            .choices[0]
            .message.content
        )

        return Parser(translation)


class BaseFtlFile(FtlFile):
    def __init__(self, file, lang):
        super().__init__(file, lang)

        self.body = parse(self.content).body
        self.messages = []

        for message in self.body:
            if not isinstance(message, Message):
                continue

            self.messages.append(
                MessageParser(
                    ftl_content=self.content,
                    ftl_message=message,
                )
            )

    def messages_to_translate(self, identifiers):
        return [
            message
            for message in self.messages
            if message.identifier not in identifiers
        ]


class FtlMessage:
    def __init__(self, value, comments):
        self.value = value
        self.comments = comments


def get_base_files(root, base_lang):
    files = []

    for filename in os.listdir(os.path.join(root, base_lang)):
        if filename.endswith(".ftl"):
            with open(os.path.join(root, base_lang, filename), "r") as f:
                files.append(BaseFtlFile(f, base_lang))

    return files


def get_file(path, lang):
    try:
        with open(path, "r") as f:
            file = FtlFile(f, lang)
    except FileNotFoundError:
        with open(path, "w+") as f:
            file = FtlFile(f, lang)

    return file


def get_path(root, lang, filename):
    return os.path.join(root, lang, filename)
