import json
import os

from fluent.syntax import parse
from fluent.syntax.ast import Message

from gpt_ftl.parser import MessageParser, Parser
from gpt_ftl.print_colored import print_warning, format_value, format_list


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

    def write_translation(self, base_file, client, config):
        translate_messages = base_file.messages_to_translate(self.message_identifiers)
        if not translate_messages:
            print_warning(
                f"Skipping {format_value(base_file.name)} for {format_value(self.lang)}. All messages are already "
                "translated."
            )
            return
        if translate_messages != base_file.messages:
            print_warning(
                f"Skipping already translated messages in {format_value(base_file.name)} "
                f"for {format_value(self.lang)}:\n{format_list([message.identifier for message in translate_messages])}"
            )

        translate_content = "\n".join(
            message.get_ftl() for message in translate_messages
        )

        messages = config.get_messages(base_file.body, self.lang, translate_content)
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            response_format={"type": "json_object"},
        )

        translation = json.loads(response.choices[0].message.content)
        parser = Parser(translation)

        with open(os.path.join(config.root, self.lang, self.name), "a") as f:
            f.write(parser.get_ftl())


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


def get_paths(root):
    paths = []
    for [dirname, _, filenames] in os.walk(root):
        paths += [
            os.path.join(dirname, filename)
            for filename in filenames
            if filename.endswith(".ftl")
        ]

    return paths


def get_base_file_paths(root, base_lang):
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
