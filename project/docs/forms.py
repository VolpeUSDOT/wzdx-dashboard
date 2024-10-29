from django.forms import ModelForm, Select, Textarea, TextInput
from django.utils.translation import gettext_lazy as _

from .models import DocsContent


class DocsContentForm(ModelForm):
    class Meta:
        model = DocsContent
        fields = ["title", "intro", "content", "ordering", "parent_content"]
        widgets = {
            "title": TextInput(
                attrs={
                    "class": "usa-input usa-character-count__field",
                    "aria-describedby": "title-char-count",
                }
            ),
            "intro": Textarea(attrs={"class": "usa-textarea", "rows": "", "cols": ""}),
            "content": Textarea(
                attrs={"class": "usa-textarea", "rows": "", "cols": ""}
            ),
            "ordering": TextInput(attrs={"class": "usa-input", "type": "number"}),
            "parent_content": Select(attrs={"class": "usa-select"}),
        }
        labels = {
            "title": _("Title"),
            "intro": _("Intro"),
            "content": _("Content"),
            "ordering": _("Ordering"),
            "parent_content": _("Parent Link"),
        }
