from fluent.syntax.ast import (
    ResourceComment,
    GroupComment,
    Comment,
    Message,
    Placeable,
    SelectExpression,
)

system_messages = {
    "role": "You are a translator designed to output in JSON.",
    "assignment": "You are given a file in Fluent format which has variable name and source pairs separated by =. Each \
    variable name is the JSON key, and the value of that key is the translation of source. Do not translate the keys.",
    "selection": "If the source you are given translates to different text based on a variable, shown with the syntax \
    { variable -> [variant] source_text }, the JSON value you output must be a list of JSON objects with 4 keys: \
    variable, variant, translation, is_default. variable key's value must be the variable name in the source, do not \
    change this. variant key's value must be the variant in the source, do not change this. translation key's value \
    must be the translation for that variant, only translate this. is_default key's value must be true for the \
    translation that is the default translation. There must be one and only one default value.",
    "single_hash_comment": "In the content you are given, there might be comment lines starting with # above a value, \
    these lines describe the value it precedes, use this description to output better translations for the value.",
    "double_hash_comment": "In the content you are given, lines starting with ## describe the section of the content \
    until the next lines starting with ## or the end of content. Use this description to output better translations of \
    the section the line describes.",
    "triple_hash_comment": "In the content you are given, lines starting with ### describe the entire content. Use \
    this description to output better translations of the entire content.",
    "placeable": "Text wrapped in { and } is a placeable, do not alter the text inside the placeable.",
}


def get_system_messages_for_body(body):
    messages = [
        system_messages["role"],
        system_messages["assignment"],
    ]

    if any(isinstance(elem, ResourceComment) for elem in body):
        messages.append(system_messages["triple_hash_comment"])
    if any(isinstance(elem, GroupComment) for elem in body):
        messages.append(system_messages["double_hash_comment"])
    if any(isinstance(elem, Comment) for elem in body):
        messages.append(system_messages["single_hash_comment"])

    for message in body:
        if not isinstance(message, Message):
            continue

        for elem in message.value.elements:
            if not isinstance(elem, Placeable):
                continue

            messages.append(system_messages["placeable"])

            if isinstance(elem.expression, SelectExpression):
                messages.append(system_messages["selection"])
                break

    return [{"role": "system", "content": content} for content in messages]
