"""RBAC query helpers. Superusers implicitly pass all checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.rbac.models import Permission, Role, UserRole

if TYPE_CHECKING:
    from apps.users.models import User


def assign_role(user: User, role_name: str, granted_by: User | None = None) -> Role:
    role = Role.objects.get(name=role_name)
    UserRole.objects.get_or_create(user=user, role=role, defaults={"granted_by": granted_by})
    return role


def remove_role(user: User, role_name: str) -> None:
    UserRole.objects.filter(user=user, role__name=role_name).delete()


def user_role_names(user: User | None) -> list[str]:
    if not user or not user.is_authenticated:
        return []
    return list(
        Role.objects.filter(user_assignments__user=user)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )


def user_permission_codes(user: User | None) -> set[str]:
    if not user or not user.is_authenticated:
        return set()
    if user.is_superuser:
        return set(Permission.objects.values_list("code", flat=True))
    return set(
        Permission.objects.filter(roles__user_assignments__user=user)
        .values_list("code", flat=True)
        .distinct()
    )


def user_has_permission(user: User | None, code: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return Permission.objects.filter(code=code, roles__user_assignments__user=user).exists()


def user_has_role(user: User | None, *role_names: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return UserRole.objects.filter(user=user, role__name__in=role_names).exists()
