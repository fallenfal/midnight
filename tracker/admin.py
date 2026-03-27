from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import DailyList, ExpirationEntry, Product, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "is_master", "is_staff", "is_active")
    list_filter = ("is_master", "is_staff", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (("Midnight", {"fields": ("is_master",)}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Midnight", {"fields": ("is_master",)}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


class ExpirationEntryInline(admin.TabularInline):
    model = ExpirationEntry
    extra = 0


@admin.register(DailyList)
class DailyListAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "created_by")
    inlines = [ExpirationEntryInline]
