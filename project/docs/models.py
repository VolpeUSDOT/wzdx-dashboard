from django.db import models

# Create your models here.


class MarkdownContent(models.Model):
    title = models.CharField(max_length=100)
    intro = models.TextField(blank=True)
    content = models.TextField()
    slug = models.SlugField(blank=True, unique=True)
    id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )

    class Meta:
        verbose_name_plural = "Doc pages"
        ordering = ["id"]

    def __str__(self):
        return f"{self.id}-{self.title}"

    def check_slug_equal(self, string: str):
        return self.slug == string
