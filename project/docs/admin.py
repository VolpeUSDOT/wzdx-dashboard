from django.contrib import admin

from .models import MarkdownContent

# Register your models here.


class MarkdownContentAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["title"]}


admin.site.register(MarkdownContent, MarkdownContentAdmin)
