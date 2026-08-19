import json

from sqladmin import ModelView
from sqladmin.fields import JSONField
from wtforms.widgets import TextArea


class LargeTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("rows", 24)
        kwargs.setdefault("style", "font-family: monospace;")
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
