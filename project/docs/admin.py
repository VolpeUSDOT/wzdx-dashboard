from django.contrib import admin

from .models import DocsContent

# Register your models here.


class DocsContentAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["title"]}


admin.site.register(DocsContent, DocsContentAdmin)
