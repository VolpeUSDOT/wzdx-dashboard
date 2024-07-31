from django import forms

from .models import Feed

FEED_CHOICES = [("", "Find a feed!")] + [
    (feed.feedname, feed.issuingorganization) for feed in Feed.objects.all()
]


class SearchForm(forms.Form):
    template_name = "components/search.html"

    feed_to_find = forms.ChoiceField(
        choices=FEED_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "usa-input",
                "type": "search",
                "name": "search",
                "placeholder": "Find a feed!",
            }
        ),
        label="Search",
    )
