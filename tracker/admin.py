from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import DailyList, ExpirationEntry, Location, Product, User


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "location", "email", "is_approved", "is_master", "is_staff", "is_active")
    list_filter = ("location", "is_approved", "is_master", "is_staff", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Midnight", {"fields": ("location", "is_approved", "is_master")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Midnight", {"fields": ("location", "is_approved", "is_master")}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "created_at")
    list_filter = ("location",)
    search_fields = ("name",)


class ExpirationEntryInline(admin.TabularInline):
    model = ExpirationEntry
    extra = 0


@admin.register(DailyList)
class DailyListAdmin(admin.ModelAdmin):
    list_display = ("id", "location", "created_at", "created_by")
    list_filter = ("location",)
    inlines = [ExpirationEntryInline]
