import json

from parser import Parser
from system_messages import get_system_messages_for_body

from fluent.syntax import parse
from fluent.syntax.ast import Message


class FtlFile:
    def __init__(self, file):
        self.content = file.read()
        self.body = parse(self.content).body

    def exclude_cached(self, db):
        messages = db.get_messages()

        for message in messages:
            self.content = self.content.replace(message[0], "")

        self.body = parse(self.content).body

    def get_translations(self, client, model, languages):
        if not any(isinstance(elem, Message) for elem in self.body):
            return []

        messages = get_system_messages_for_body(self.body)

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

        return [Parser(translation) for translation in translations.items()]
