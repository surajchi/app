import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.administration.constants import AuditAction
from apps.administration.models import AdminAuditLog
from apps.markets.models import DataProviderStatus
from apps.news.models import NewsArticle
from apps.notifications.models import Notification
from apps.rbac.services import assign_role, user_role_names
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _superuser():
    user = UserFactory()
    user.is_superuser = True
    user.is_staff = True
    user.save()
    return user


def _article(title="Headline", status="published", breaking=False) -> NewsArticle:
    return NewsArticle.objects.create(
        source="test",
        source_url=f"https://example.com/{title}".replace(" ", "-"),
        url_hash=title.replace(" ", "-"),
        simhash=0,
        title=title,
        body="body",
        published_at=timezone.now(),
        status=status,
        is_breaking=breaking,
    )


# --- permissions ------------------------------------------------------------


def test_overview_requires_auth(client):
    assert client.get("/api/v1/admin/overview/").status_code == 401


def test_overview_forbidden_for_plain_user(client):
    client.force_authenticate(UserFactory())
    assert client.get("/api/v1/admin/overview/").status_code == 403


def test_overview_ok_for_superuser(client):
    client.force_authenticate(_superuser())
    resp = client.get("/api/v1/admin/overview/")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "users" in data and "notifications" in data and "markets" in data
    assert data["users"]["total"] >= 1


def test_moderator_can_view_news_but_not_manage_users(client):
    mod = UserFactory()
    assign_role(mod, "moderator")
    client.force_authenticate(mod)
    assert client.get("/api/v1/admin/news/").status_code == 200

    target = UserFactory()
    assert (
        client.patch(
            f"/api/v1/admin/users/{target.id}/", {"is_active": False}, format="json"
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/admin/users/{target.id}/roles/", {"role": "premium"}, format="json"
        ).status_code
        == 403
    )


# --- user management --------------------------------------------------------


def test_user_list_and_search(client):
    client.force_authenticate(_superuser())
    UserFactory(email="alice@example.com")
    UserFactory(email="bob@example.com")
    all_users = client.get("/api/v1/admin/users/").json()["data"]
    assert len(all_users) >= 3
    filtered = client.get("/api/v1/admin/users/?search=alice").json()["data"]
    assert [u["email"] for u in filtered] == ["alice@example.com"]


def test_user_update_records_audit(client):
    admin = _superuser()
    client.force_authenticate(admin)
    target = UserFactory()
    resp = client.patch(
        f"/api/v1/admin/users/{target.id}/",
        {"status": "suspended", "is_active": False},
        format="json",
    )
    assert resp.status_code == 200
    target.refresh_from_db()
    assert target.is_active is False and target.status == "suspended"
    assert AdminAuditLog.objects.filter(
        action=AuditAction.USER_UPDATED, target_id=str(target.id)
    ).exists()


def test_assign_and_remove_role(client):
    admin = _superuser()
    client.force_authenticate(admin)
    target = UserFactory()

    resp = client.post(
        f"/api/v1/admin/users/{target.id}/roles/", {"role": "premium"}, format="json"
    )
    assert resp.status_code == 201
    assert "premium" in user_role_names(target)

    resp = client.delete(f"/api/v1/admin/users/{target.id}/roles/premium/")
    assert resp.status_code == 200
    assert "premium" not in user_role_names(target)
    assert AdminAuditLog.objects.filter(action=AuditAction.ROLE_ASSIGNED).exists()
    assert AdminAuditLog.objects.filter(action=AuditAction.ROLE_REMOVED).exists()


def test_assign_unknown_role_rejected(client):
    client.force_authenticate(_superuser())
    target = UserFactory()
    resp = client.post(f"/api/v1/admin/users/{target.id}/roles/", {"role": "wizard"}, format="json")
    assert resp.status_code == 400


def test_roles_list(client):
    client.force_authenticate(_superuser())
    data = client.get("/api/v1/admin/roles/").json()["data"]
    names = {r["name"] for r in data}
    assert "super_admin" in names
    super_admin = next(r for r in data if r["name"] == "super_admin")
    assert "users.manage" in super_admin["permissions"]


# --- news moderation --------------------------------------------------------


def test_news_moderation_updates_and_audits(client):
    client.force_authenticate(_superuser())
    art = _article()
    resp = client.patch(
        f"/api/v1/admin/news/{art.id}/",
        {"status": "rejected", "is_breaking": True},
        format="json",
    )
    assert resp.status_code == 200
    art.refresh_from_db()
    assert art.status == "rejected" and art.is_breaking is True
    assert AdminAuditLog.objects.filter(
        action=AuditAction.NEWS_MODERATED, target_id=str(art.id)
    ).exists()


def test_news_status_filter(client):
    client.force_authenticate(_superuser())
    _article(title="Pub", status="published")
    _article(title="Rej", status="rejected")
    data = client.get("/api/v1/admin/news/?status=rejected").json()["data"]
    assert [a["title"] for a in data] == ["Rej"]


# --- providers --------------------------------------------------------------


def test_providers_list(client):
    client.force_authenticate(_superuser())
    DataProviderStatus.objects.create(provider="synthetic", domain="market")
    data = client.get("/api/v1/admin/providers/").json()["data"]
    assert any(p["provider"] == "synthetic" for p in data)


# --- broadcast --------------------------------------------------------------


def test_broadcast_notifies_active_users(client):
    admin = _superuser()
    UserFactory()
    UserFactory()
    client.force_authenticate(admin)
    resp = client.post(
        "/api/v1/admin/broadcast/",
        {"title": "Maintenance tonight", "body": "Heads up."},
        format="json",
    )
    assert resp.status_code == 202
    recipients = resp.json()["data"]["recipients"]
    assert recipients == 3  # admin + 2
    assert Notification.objects.filter(title="Maintenance tonight").count() == 3
    assert AdminAuditLog.objects.filter(action=AuditAction.BROADCAST_SENT).exists()


def test_broadcast_by_role_segments(client):
    admin = _superuser()
    premium_user = UserFactory()
    assign_role(premium_user, "premium")
    UserFactory()  # free user, should not receive
    client.force_authenticate(admin)
    resp = client.post(
        "/api/v1/admin/broadcast/",
        {"title": "Premium perk", "role": "premium"},
        format="json",
    )
    assert resp.status_code == 202
    assert resp.json()["data"]["recipients"] == 1
    assert Notification.objects.filter(title="Premium perk").count() == 1


def test_broadcast_forbidden_without_settings_manage(client):
    mod = UserFactory()
    assign_role(mod, "moderator")
    client.force_authenticate(mod)
    resp = client.post("/api/v1/admin/broadcast/", {"title": "x"}, format="json")
    assert resp.status_code == 403


# --- audit ------------------------------------------------------------------


def test_audit_list(client):
    admin = _superuser()
    client.force_authenticate(admin)
    target = UserFactory()
    client.patch(f"/api/v1/admin/users/{target.id}/", {"is_active": False}, format="json")
    data = client.get("/api/v1/admin/audit/").json()["data"]
    assert len(data) >= 1
    assert data[0]["action"] == AuditAction.USER_UPDATED
