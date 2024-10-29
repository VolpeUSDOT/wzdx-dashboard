from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

# Create your models here.


class DocsContent(models.Model):
    title = models.CharField(
        max_length=100, unique=True, help_text="You can enter up to 100 characters"
    )
    intro = models.TextField(blank=True)
    content = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    ordering = models.PositiveIntegerField(unique=True)
    last_editted = models.DateTimeField(auto_now=True, editable=False)
    parent_content = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )  # type: models.ForeignKey[DocsContent] # type: ignore

    def clean(self):
        if self.parent_content and self.parent_content.pk == self.pk:
            raise ValidationError(_("Cannot set parent to self."))

    class Meta:
        verbose_name_plural = "docs content"
        ordering = ["ordering"]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(DocsContent, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def check_slug_equal(self, string: str):
        return self.slug == string

    def get_absolute_url(self):
        return reverse("docs-view", kwargs={"slug": self.slug})

    def children(self):
        return DocsContent.objects.filter(parent_content=self)

    def all_children_slugs(self):
        return [self.slug] + [
            children_slug
            for children_slugs in self.children()
            for children_slug in children_slugs.all_children_slugs()
        ]

    def all_parent_slugs(self):
        return [
            slug
            for slug in self.parent_content.all_parent_slugs()
            if self.parent_content
        ]
