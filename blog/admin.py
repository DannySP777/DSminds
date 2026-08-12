from django.contrib import admin

from .models import Feedback, Page, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "body")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "updated_at")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at")
    actions = ["mark_as_read"]

    @admin.action(description="Marcar como leído")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
