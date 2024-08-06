from django.db import models
from django.urls import reverse
from django.utils.text import slugify

# Create your models here.


class DocsContent(models.Model):
    title = models.CharField(max_length=100, unique=True)
    intro = models.TextField(blank=True)
    content = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    ordering = models.PositiveIntegerField(unique=True)

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
