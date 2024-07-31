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
    "role": "You are a translator.",
    "assignment": "In the content you are given, each value is assigned to a variable with =, do not alter the "
    "variable names or the = sign.",
    "multi_lang": 'Separate each language you translate to by adding a line of "START OF TRANSLATION FOR {LANG_CODE}" '
    "before it where {LANG_CODE} is the language code you are given in the prompt.",
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
        all_system_messages["assignment"],
    ]

    if len(languages) > 1:
        system_messages_base.append(all_system_messages["multi_lang"])

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
                client.chat.completions.create(model=model, messages=messages)
                .choices[0]
                .message.content
            )
            print(translation)
