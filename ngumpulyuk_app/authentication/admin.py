from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-created_at",)
    list_display = (
        "email",
        "full_name",
        "username",
        "auth_provider",
        "is_verified",
        "is_active",
        "is_staff",
        "last_login",
        "created_at",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "is_verified", "auth_provider")
    search_fields = ("email", "full_name", "username")
    readonly_fields = ("last_login", "created_at", "updated_at", "id")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profil",
            {
                "fields": (
                    "full_name",
                    "username",
                    "phone",
                    "bio",
                    "profile_picture",
                    "location",
                    "date_of_birth",
                    "gender",
                ),
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "auth_provider",
                    "is_verified",
                    "onboarding_completed",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Waktu", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "password1", "password2"),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is None:
            return self.add_fieldsets
        return self.fieldsets
