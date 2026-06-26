import pytest

from apps.rbac import services
from apps.rbac.constants import (
    ALL_PERMISSION_CODES,
    ROLE_ADMIN,
    ROLE_FREE,
    ROLE_SUPER_ADMIN,
)
from apps.rbac.models import Permission, Role
from apps.users.models import User
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_default_roles_and_permissions_are_seeded():
    for name in (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_FREE):
        assert Role.objects.filter(name=name, is_system=True).exists()
    assert Permission.objects.count() == len(ALL_PERMISSION_CODES)


def test_super_admin_role_has_all_permissions():
    role = Role.objects.get(name=ROLE_SUPER_ADMIN)
    assert role.permissions.count() == len(ALL_PERMISSION_CODES)


def test_assign_role_and_checks():
    user = UserFactory()
    services.assign_role(user, ROLE_ADMIN)
    assert services.user_has_role(user, ROLE_ADMIN)
    assert not services.user_has_role(user, ROLE_SUPER_ADMIN)
    assert services.user_has_permission(user, "news.publish")
    assert not services.user_has_permission(user, "settings.manage")
    assert ROLE_ADMIN in services.user_role_names(user)


def test_assign_role_is_idempotent():
    user = UserFactory()
    services.assign_role(user, ROLE_FREE)
    services.assign_role(user, ROLE_FREE)
    assert user.user_roles.filter(role__name=ROLE_FREE).count() == 1


def test_superuser_passes_all_permission_checks():
    admin = User.objects.create_superuser(email="su@example.com", password="x", full_name="SU")
    assert services.user_has_permission(admin, "settings.manage")
    assert services.user_has_role(admin, ROLE_ADMIN)  # superuser short-circuits


def test_anonymous_has_no_permissions():
    assert services.user_has_permission(None, "news.view") is False
    assert services.user_role_names(None) == []
