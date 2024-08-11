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

from gpt_ftl.print_colored import print_action_done, format_value, footer


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
            epilog=footer(),
        )
        subparsers = parser.add_subparsers(dest="subcommand", required=True)

        translate_parser = subparsers.add_parser(
            "translate", help="Translate FTL files"
        )

        add_root_argument(translate_parser)

        translate_parser.add_argument(
            "base_lang",
            help="language to translate from, must match a directory in the FTL root path",
        )

        translate_parser.add_argument(
            "--api-key",
            "-k",
            default=os.getenv("OPENAI_API_KEY"),
            help="OpenAI API key, can be obtained from https://platform.openai.com/api-keys, the key must have model "
            "capabilities allowed (default: environment variable OPENAI_API_KEY)",
            dest="api_key",
        )

        translate_parser.add_argument(
            "--model",
            "-m",
            default="gpt-4o",
            help="model to use for translation, models can be found at https://platform.openai.com/docs/models, the model "
            "must support JSON mode, pricing for models can be found at https://openai.com/api/pricing "
            "(default: %(default)s)",
            dest="model",
        )

        strip_comments_parser = subparsers.add_parser(
            "strip-comments",
            help="Strip comments from FTL files, useful for removing comments added to provide context to GPT",
        )

        add_root_argument(strip_comments_parser)

        sort_parser = subparsers.add_parser(
            "sort",
            help="Sort messages in FTL files alphabetically, useful because translations returned by GPT aren't "
            "guaranteed to match the ordering of the original messages",
        )

        add_root_argument(sort_parser)

        sort_parser.add_argument(
            "--separate-by-newline",
            "-s",
            action="store_true",
            help="separate messages with newline (default: off)",
            dest="separate",
        )

        parser.parse_args(namespace=self)

    def get_messages(self, body, lang, translate_content):
        prompts = self["prompts"]

        system_messages = {prompts["role"], prompts["assignment"]}

        if prompts["custom"]:
            system_messages.update(prompts["custom"])

        for elem in body:
            if isinstance(elem, ResourceComment):
                system_messages.add(prompts["triple_hash_comment"])
            if isinstance(elem, GroupComment):
                system_messages.add(prompts["double_hash_comment"])
            if isinstance(elem, Comment):
                system_messages.add(prompts["single_hash_comment"])

            if isinstance(elem, Message):
                if elem.comment:
                    system_messages.add(prompts["single_hash_comment"])

                for message_elem in elem.value.elements:
                    if not isinstance(message_elem, Placeable):
                        continue

                    system_messages.add(prompts["placeable"])

                    if isinstance(message_elem.expression, SelectExpression):
                        system_messages.add(prompts["selection"])

        user_message = prompts["user"].format(
            lang=lang, translate_content=translate_content
        )

        return [
            {"role": "system", "content": content} for content in system_messages
        ] + [{"role": "user", "content": user_message}]


def add_root_argument(parser):
    parser.add_argument(
        "root",
        help="absolute path to the root directory of the FTL files, every subdirectory must be a directory with a "
        "language code, the files in the subdirectories must be FTL files",
    )
