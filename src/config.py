import tomli
import tomli_w
from fluent.syntax.ast import (
    ResourceComment,
    GroupComment,
    Comment,
    Message,
    Placeable,
    SelectExpression,
)


class Config:
    def __init__(self):

        with open("config.toml", "rb") as f:
            toml = tomli.load(f)

        self.toml = toml

    def __getitem__(self, item):
        try:
            return self.toml[item]
        except KeyError:
            return

    def __setitem__(self, key, value):
        try:
            self.toml[key] = value
        except KeyError:
            return

        with open("config.toml", "wb") as f:
            tomli_w.dump(self.toml, f)

    def get_messages(self, body, lang, translate_content):
        prompts = self["prompts"]

        system_messages = [
            prompts["role"],
            prompts["assignment"],
        ]

        custom_prompts = prompts["custom"]
        if custom_prompts:
            system_messages += custom_prompts

        if any(isinstance(elem, ResourceComment) for elem in body):
            system_messages.append(prompts["triple_hash_comment"])
        if any(isinstance(elem, GroupComment) for elem in body):
            system_messages.append(prompts["double_hash_comment"])
        if any(isinstance(elem, Comment) for elem in body):
            system_messages.append(prompts["single_hash_comment"])

        for message in body:
            if not isinstance(message, Message):
                continue

            for elem in message.value.elements:
                if not isinstance(elem, Placeable):
                    continue

                system_messages.append(prompts["placeable"])

                if isinstance(elem.expression, SelectExpression):
                    system_messages.append(prompts["selection"])
                    break

        user_message = prompts["user"].format(
            lang=lang, translate_content=translate_content
        )

        return [
            {"role": "system", "content": content} for content in system_messages
        ] + [{"role": "user", "content": user_message}]
