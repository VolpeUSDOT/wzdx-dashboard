from django.db import models

# Create your models here.


class MarkdownContent(models.Model):
    title = models.CharField(max_length=100)
    intro = models.TextField(blank=True)
    content = models.TextField()
    slug = models.SlugField(blank=True, unique=True)

    class Meta:
        verbose_name_plural = "Markdown content"

    def __str__(self):
        return self.title

    def check_slug_equal(self, string: str):
        return self.slug == string
