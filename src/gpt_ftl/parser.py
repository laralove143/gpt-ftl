from fluent.syntax.ast import SelectExpression, Placeable


class Parser:
    def __init__(self, json):
        self.messages = [MessageParser(message) for message in json.items()]

    def get_ftl(self):
        return "\n".join(message.get_ftl() for message in self.messages) + "\n"


class MessageParser:
    def __init__(self, json=None, ftl_content=None, ftl_message=None):
        self.identifier = None
        self.value = None
        self.comments = None
        self.ftl_message = None

        if json:
            self.init_from_json(json)
        if ftl_content:
            self.init_from_ftl(ftl_content, ftl_message)

    def init_from_json(self, json):
        self.identifier = json[0]

        json_val = json[1]

        if isinstance(json_val, str):
            self.value = json_val

        if isinstance(json_val, list):
            self.value = SelectionParser(json_val).get_ftl()

    def init_from_ftl(self, content, message):
        self.identifier = message.id.name
        self.value = content[message.value.span.start : message.value.span.end]
        self.comments = message.comment.content if message.comment else None
        self.ftl_message = message

    def contains_nested_selection(self):
        for i, elem in enumerate(self.ftl_message.value.elements):
            if i == 0:
                continue

            if isinstance(elem, Placeable) and isinstance(
                elem.expression, SelectExpression
            ):
                return True

    def get_ftl(self):
        ftl = ""

        if self.comments:
            ftl += "\n".join("# " + line for line in self.comments.split("\n")) + "\n"

        ftl += f"{self.identifier} = {self.value}"

        return ftl


class SelectionParser:
    def __init__(self, json):
        self.variable = json[0]["variable"]
        self.variants = [VariantParser(variant) for variant in json]
        self.collapse()

    def collapse(self):
        default_translation = self.default().translation

        for i, variant in enumerate(self.variants.copy()):
            if variant.is_default:
                continue

            if variant.translation == default_translation:
                self.variants.pop(i)

    def default(self):
        return next(variant for variant in self.variants if variant.is_default)

    def get_ftl(self):
        if len(self.variants) == 1:
            return self.variants[0].translation

        ftl = f"{{ {self.variable} ->\n"

        for variant in self.variants:
            ftl += f"    {variant.get_ftl()}\n"

        ftl += "}"

        return ftl


class VariantParser:
    def __init__(self, val):
        self.variant = val["variant"]
        self.translation = val["translation"]
        self.is_default = val["is_default"]

    def get_ftl(self):
        ftl = ""
        if self.is_default:
            ftl += "*"

        ftl += f"[{self.variant}] {self.translation}"
        return ftl
