from django.contrib import admin

# Register your models here.
from .models import APIKey, Feed, FeedError

admin.site.register(Feed)
admin.site.register(FeedError)
admin.site.register(APIKey)
