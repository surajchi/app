from django.contrib import admin

from apps.rbac.models import Permission, Role, UserRole


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_system", "description")
    list_filter = ("is_system",)
    search_fields = ("name",)
    filter_horizontal = ("permissions",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "granted_by", "granted_at")
    search_fields = ("user__email", "role__name")
    list_select_related = ("user", "role", "granted_by")
    autocomplete_fields = ("user", "role", "granted_by")
