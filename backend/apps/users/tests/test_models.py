import pytest
from django.contrib.auth import get_user_model

from apps.users.models import User
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_create_user_normalizes_and_lowercases_email():
    user = User.objects.create_user(email="John.Doe@EXAMPLE.com", password="x", full_name="John")
    assert user.email == "john.doe@example.com"
    assert user.check_password("x")
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.status == User.Status.ACTIVE


def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="x", full_name="No Email")


def test_create_superuser_sets_flags():
    admin = User.objects.create_superuser(
        email="admin@example.com", password="x", full_name="Admin"
    )
    assert admin.is_staff is True
    assert admin.is_superuser is True


def test_get_user_model_returns_custom_user():
    assert get_user_model() is User


def test_str_returns_email():
    user = UserFactory(email="str@example.com")
    assert str(user) == "str@example.com"


def test_email_verified_property():
    user = UserFactory()
    assert user.email_verified is False


def test_soft_delete_deactivates_user():
    user = UserFactory()
    user.soft_delete()
    user.refresh_from_db()
    assert user.is_active is False
    assert user.status == User.Status.DELETED
    assert user.deleted_at is not None
