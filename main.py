import os

from dotenv import load_dotenv
from openai import OpenAI
from os import environ


load_dotenv()
base_lang = environ.get("BASE_LANG")
keep_comments = environ.get("KEEP_COMMENTS")
model = environ.get("MODEL")
root = environ.get("FTL_ROOT_PATH")

client = OpenAI()

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
    "keep_comments": "Lines starting with #, ## or ### are comments, use them to improve your translation as "
    "instructed above but also translate them and include them in your output.",
    "strip_comments": "Lines starting with #, ## or ### are comments, use them to improve your translation as "
    "instructed above and do not include them in your output.",
    "placeable": "Text wrapped in { and } is a placeable, do not alter the text inside the placeable.",
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

    system_messages_base = [
        all_system_messages["role"],
        all_system_messages["multi_lang"],
        all_system_messages["assignment"],
        all_system_messages["selection"],
    ]

    if keep_comments == "true":
        system_messages_base.append(all_system_messages["keep_comments"])
    else:
        system_messages_base.append(all_system_messages["strip_comments"])

    user_message_start = f"Translate the following content to {languages}:\n"

    for file in base_files:
        with open(os.path.join(root, base_lang, file), "r") as f:
            content = f.read()

            system_messages = system_messages_base.copy()

            if "### " in content:
                system_messages.append(all_system_messages["triple_hash_comment"])
            if "## " in content:
                system_messages.append(all_system_messages["double_hash_comment"])
            if "# " in content:
                system_messages.append(all_system_messages["single_hash_comment"])

            if "{" in content:
                system_messages.append(all_system_messages["placeable"])

            messages = [
                {"role": "system", "content": content} for content in system_messages
            ]

            messages.append({"role": "user", "content": user_message_start + content})

            translation = (
                client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
                .choices[0]
                .message.content
            )
            print(translation)
