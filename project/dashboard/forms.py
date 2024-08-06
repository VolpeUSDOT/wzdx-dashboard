from django import forms

from .models import Feed


class SearchForm(forms.Form):
    template_name = "dashboard/search_feeds.html"

    search_feed = forms.ModelChoiceField(
        empty_label="Find a feed!",
        queryset=Feed.objects,
        widget=forms.Select(
            attrs={
                "class": "usa-input",
                "type": "search",
                "name": "search",
            }
        ),
    )
