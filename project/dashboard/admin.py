from typing import Optional

from django.contrib import admin
from django.contrib.gis.db import models

# Register your models here.
from .models import APIKey, Feed, FeedData, FeedStatus


class ReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = []

    def get_readonly_fields(self, request, obj: Optional[models.Model] = None):
        assert obj is not None
        print(self.model._meta.get_fields())
        return list(self.readonly_fields) + [
            field.name
            for field in self.model._meta.get_fields()
            if not field.is_relation or isinstance(field, models.ForeignKey)
        ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyTabularAdmin(admin.TabularInline):
    readonly_fields = []

    def get_readonly_fields(self, request, obj: Optional[models.Model] = None):
        assert obj is not None
        return list(self.readonly_fields) + [
            field.name
            for field in self.model._meta.get_fields()
            if not field.is_relation or isinstance(field, models.ForeignKey)
        ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyStackedAdmin(admin.StackedInline):
    readonly_fields = []

    def get_readonly_fields(self, request, obj: Optional[models.Model] = None):
        assert obj is not None
        return list(self.readonly_fields) + [
            field.name
            for field in self.model._meta.get_fields()
            if not field.is_relation or isinstance(field, models.ForeignKey)
        ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class APIKeyInline(admin.StackedInline):
    model = APIKey
    readonly_fields = ["feed"]
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class FeedDataAdminInline(ReadOnlyStackedAdmin):
    model = FeedData


class FeedStatusAdminInline(ReadOnlyTabularAdmin):
    model = FeedStatus


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    readonly_fields = ["feed"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Feed)
class FeedAdmin(ReadOnlyAdmin):
    inlines = [APIKeyInline, FeedStatusAdminInline, FeedDataAdminInline]
