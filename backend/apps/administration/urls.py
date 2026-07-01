"""Admin console routes, mounted at /api/v1/admin/."""

from __future__ import annotations

from django.urls import path

from apps.administration.views import (
    AdminNewsDetailView,
    AdminNewsListView,
    AdminOverviewView,
    AdminUserDetailView,
    AdminUserListView,
    AdminUserRolesView,
    AuditLogListView,
    BroadcastView,
    ProviderStatusListView,
    RoleListView,
)

urlpatterns = [
    path("overview/", AdminOverviewView.as_view(), name="admin-overview"),
    path("users/", AdminUserListView.as_view(), name="admin-users"),
    path("users/<uuid:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path(
        "users/<uuid:user_id>/roles/",
        AdminUserRolesView.as_view(),
        name="admin-user-roles",
    ),
    path(
        "users/<uuid:user_id>/roles/<str:role>/",
        AdminUserRolesView.as_view(),
        name="admin-user-role-remove",
    ),
    path("roles/", RoleListView.as_view(), name="admin-roles"),
    path("news/", AdminNewsListView.as_view(), name="admin-news"),
    path("news/<uuid:pk>/", AdminNewsDetailView.as_view(), name="admin-news-detail"),
    path("providers/", ProviderStatusListView.as_view(), name="admin-providers"),
    path("broadcast/", BroadcastView.as_view(), name="admin-broadcast"),
    path("audit/", AuditLogListView.as_view(), name="admin-audit"),
]
