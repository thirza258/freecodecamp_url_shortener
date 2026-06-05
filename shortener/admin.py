from django.contrib import admin
from django.db.models import Count

from .models import ClickEvent, ShortURL

admin.site.site_header = "Nevatal URL Shortener Admin"
admin.site.site_title = "Nevatal Admin"
admin.site.index_title = "Short link management"


class ClickEventInline(admin.TabularInline):
    model = ClickEvent
    extra = 0
    fields = ("timestamp", "ip_address", "user_agent", "referer")
    readonly_fields = ("timestamp", "ip_address", "user_agent", "referer")
    can_delete = False
    show_change_link = True


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = (
        "short_code",
        "owner",
        "original_url",
        "is_active",
        "click_count",
        "analytics_count",
        "last_accessed_at",
        "created_at",
    )
    search_fields = ("short_code", "original_url", "owner__username")
    list_filter = ("is_active", "created_at", "last_accessed_at", "owner")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "last_accessed_at", "click_count", "analytics_count", "analytics_summary")
    inlines = (ClickEventInline,)
    date_hierarchy = "created_at"
    actions = ("mark_active", "mark_inactive")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(analytics_count=Count("click_events"))

    @admin.display(ordering="analytics_count", description="Analytics")
    def analytics_count(self, obj):
        return getattr(obj, "analytics_count", 0)

    @admin.display(description="Analytics summary")
    def analytics_summary(self, obj):
        if not obj.pk:
            return "Save this link to see analytics."
        last_accessed = obj.last_accessed_at.isoformat() if obj.last_accessed_at else "never"
        return f"{obj.click_count} clicks recorded, {getattr(obj, 'analytics_count', 0)} events stored, last accessed {last_accessed}."

    @admin.action(description="Mark selected links active")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected links inactive")
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("short_url", "timestamp", "ip_address")
    search_fields = ("short_url__short_code", "user_agent", "referer", "ip_address")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)
    readonly_fields = ("short_url", "timestamp", "user_agent", "referer", "ip_address")
