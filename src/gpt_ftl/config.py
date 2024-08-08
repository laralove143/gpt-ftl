import importlib.resources
import os.path

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

from gpt_ftl.print_colored import print_action_done, format_value, print_error


class Config:
    def __init__(self):
        default = importlib.resources.open_text("gpt_ftl", "config.toml").read()

        if os.name == "nt":
            config_path = os.path.join(os.getenv("APPDATA"), "gpt_ftl/config.toml")
        else:
            config_path = os.path.expanduser("~/.config/gpt_ftl/config.toml")

        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, "w") as f:
                f.write(default)

            print_action_done(
                f"Created default configuration file at {format_value(config_path)}. Edit it to change or add prompts."
            )

        with open(config_path, "rb") as f:
            toml = tomli.load(f)

        self.toml = toml

    def __getitem__(self, item):
        return self.toml[item]

    def __setitem__(self, key, value):
        self.toml[key] = value

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


def get_env(key):
    val = os.getenv(key)

    if not val:
        print_error(f"Please set the environment variable: {format_value(key)}.")
        exit(1)

    return val
