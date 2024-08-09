import importlib.resources
import os.path
from argparse import ArgumentParser

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

        self.set_args()

    def __getitem__(self, item):
        return self.toml[item]

    def __setitem__(self, key, value):
        self.toml[key] = value

        with open("config.toml", "wb") as f:
            tomli_w.dump(self.toml, f)

    def set_args(self):
        parser = ArgumentParser(
            description="Generate Fluent Translation List files using OpenAI's GPT",
            epilog="Made with ❤️ by Lara Kayaalp",
        )

        parser.add_argument(
            "root",
            help="absolute path to the root directory of the FTL files, every subdirectory must be a directory with a "
            "language code, the files in the subdirectories must be FTL files",
        )

        parser.add_argument(
            "base_lang",
            help="language to translate from, must match a directory in the FTL root path",
        )

        parser.add_argument(
            "--api-key, -k",
            default=os.getenv("OPENAI_API_KEY"),
            help="OpenAI API key, can be obtained from https://platform.openai.com/api-keys, the key must have model "
            "capabilities allowed (default: environment variable OPENAI_API_KEY)",
            dest="api_key",
        )

        parser.add_argument(
            "--model, -m",
            default="gpt-4o",
            help="model to use for translation, models can be found at https://platform.openai.com/docs/models, the model "
            "must support JSON mode, pricing for models can be found at https://openai.com/api/pricing "
            "(default: %(default)s)",
            dest="model",
        )

        parser.parse_args(namespace=self)

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
