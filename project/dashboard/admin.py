from typing import Optional

from django.contrib import admin
from django.contrib.gis.db import models

# Register your models here.
from .models import (
    APIKey,
    Feed,
    OfflineErrorStatus,
    OKStatus,
    OutdatedErrorStatus,
    SchemaErrorStatus,
    SchemaValidationError,
    StaleErrorStatus,
)


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


class SchemaValidationErrorInline(ReadOnlyTabularAdmin):
    model = SchemaValidationError


class OKStatusInline(ReadOnlyTabularAdmin):
    model = OKStatus


class SchemaErrorStatusInline(ReadOnlyTabularAdmin):
    model = SchemaErrorStatus
    inline = [SchemaValidationErrorInline]


class OutdatedErrorStatusInline(ReadOnlyTabularAdmin):
    model = OutdatedErrorStatus


class StaleErrorStatusInline(ReadOnlyTabularAdmin):
    model = StaleErrorStatus


class OfflineErrorStatusInline(ReadOnlyTabularAdmin):
    model = OfflineErrorStatus


@admin.register(Feed)
class FeedAdmin(ReadOnlyAdmin):
    inlines = [
        APIKeyInline,
        OKStatusInline,
        OfflineErrorStatusInline,
        SchemaErrorStatusInline,
        OutdatedErrorStatusInline,
        StaleErrorStatusInline,
    ]


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    readonly_fields = ["feed"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
