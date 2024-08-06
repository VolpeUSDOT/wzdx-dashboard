from django.forms import ModelForm, Textarea, TextInput
from django.utils.translation import gettext_lazy as _

from .models import DocsContent


class DocsContentForm(ModelForm):
    class Meta:
        model = DocsContent
        fields = ["title", "intro", "content", "ordering"]
        widgets = {
            "title": TextInput(attrs={"class": "usa-input"}),
            "intro": Textarea(attrs={"class": "usa-textarea", "rows": "", "cols": ""}),
            "content": Textarea(
                attrs={"class": "usa-textarea", "rows": "", "cols": ""}
            ),
            "ordering": TextInput(attrs={"class": "usa-input", "type": "number"}),
        }
        labels = {
            "title": _("Title"),
            "intro": _("Intro"),
            "content": _("Content"),
            "ordering": _("Ordering"),
        }
