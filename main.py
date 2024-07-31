import os

from dotenv import load_dotenv
from openai import OpenAI
from os import environ


load_dotenv()
base_lang = environ.get("BASE_LANG")
model = environ.get("MODEL")
root = environ.get("FTL_ROOT_PATH")

client = OpenAI()

all_system_messages = {
    "role": "You are a translator.",
    "assignment": "In the content you are given, each value is assigned to a variable with =, do not alter the "
    "variable names or the = sign.",
    "multi_lang": 'Separate each language you translate to by adding a line of "START OF TRANSLATION FOR {'
    'LANG_CODE}" before it where {LANG_CODE} is the language code you are given in the prompt.',
}


def files(lang):
    return [
        filename
        for filename in os.listdir(os.path.join(root, lang))
        if filename.endswith(".ftl")
    ]


if __name__ == "__main__":
    base_files = files(base_lang)
    languages = [
        lang
        for lang in os.listdir(root)
        if os.path.isdir(os.path.join(root, lang)) and lang != base_lang
    ]

    system_messages = [all_system_messages["role"], all_system_messages["assignment"]]

    if len(languages) > 1:
        system_messages.append(all_system_messages["multi_lang"])

    messages = [{"role": "system", "content": content} for content in system_messages]

    user_message_start = f"Translate the following content to {languages}:\n"

    for file in base_files:
        with open(os.path.join(root, base_lang, file), "r") as f:
            content = f.read()

            messages.append({"role": "user", "content": user_message_start + content})

            translation = (
                client.chat.completions.create(model=model, messages=messages)
                .choices[0]
                .message.content
            )
            print(translation)
