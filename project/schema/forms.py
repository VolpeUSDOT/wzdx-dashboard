from django import forms
from django.utils.translation import gettext_lazy as _
from shared.schema_check import VERSION_TO_SCHEMA


class SchemaForm(forms.Form):
    version = forms.ChoiceField(
        choices=((key, f"WZDx {key}") for key in VERSION_TO_SCHEMA.keys()),
        label=_("WZDx Version"),
        required=True,
    )
    feed_data = forms.CharField(
        label=_("Feed Data"), widget=forms.Textarea, required=True
    )

    version.widget.attrs.update({"class": "usa-select"})
    feed_data.widget.attrs.update({"class": "usa-textarea font-family-mono"})
