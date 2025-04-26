from django import forms

from .models import Feed


# Use function to prevent it from running until needed...
def get_feed_choices():
    return [("", "Find a feed!")] + [
        (feedname, f"{state + ' - ' if state else ''}{issuingorganization}")
        for (feedname, state, issuingorganization) in Feed.objects.values_list(
            "feedname", "state", "issuingorganization"
        )
    ]


class SearchForm(forms.Form):
    template_name = "dashboard/components/search_feeds.html"

    search_feed = forms.ChoiceField(
        choices=get_feed_choices,
        widget=forms.Select(
            attrs={
                "class": "usa-select",
                "type": "search",
                "name": "search",
            }
        ),
    )
