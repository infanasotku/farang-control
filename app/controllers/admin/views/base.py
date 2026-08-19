import json

from sqladmin import ModelView
from sqladmin.fields import JSONField
from wtforms.widgets import TextArea


class LargeTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("rows", 24)
        kwargs.setdefault("spellcheck", "false")
        kwargs.setdefault("autocomplete", "off")
        kwargs.setdefault("data-json-editor", "true")
        kwargs.setdefault(
            "style",
            "font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; "
            "min-height: 32rem; resize: vertical; tab-size: 2; white-space: pre;",
        )
        return super().__call__(field, **kwargs)


class PrettyJSONField(JSONField):
    widget = LargeTextAreaWidget()

    def _value(self) -> str:
        data = {}

        if self.raw_data:
            data = json.loads(self.raw_data[0])

        if self.data:
            data = self.data

        return json.dumps(data, ensure_ascii=False, indent=2)


class AdminModelView(ModelView):
    can_export = False
    create_template = "admin/create.html"
    details_template = "admin/details.html"
    edit_template = "admin/edit.html"
