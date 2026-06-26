"""Canonical role/permission codes seeded by the data migration."""

from __future__ import annotations

# Default role names.
ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_MODERATOR = "moderator"
ROLE_PREMIUM = "premium"
ROLE_FREE = "free"
ROLE_GUEST = "guest"

DEFAULT_ROLE = ROLE_FREE

# Permission catalog: (code, human name).
PERMISSIONS: list[tuple[str, str]] = [
    ("users.view", "View users"),
    ("users.manage", "Create/update/suspend users"),
    ("users.impersonate", "Impersonate users"),
    ("roles.manage", "Manage roles & permissions"),
    ("profiles.view_any", "View any user profile"),
    ("news.view", "View news (incl. unpublished)"),
    ("news.publish", "Publish news"),
    ("news.moderate", "Moderate / reject news"),
    ("markets.manage", "Manage market instruments & data"),
    ("ai.manage", "Manage AI models"),
    ("ai.train", "Trigger AI training jobs"),
    ("alerts.manage_any", "Manage any user's alerts"),
    ("subscriptions.manage", "Manage subscription plans"),
    ("payments.view", "View payments"),
    ("payments.refund", "Issue refunds"),
    ("feature_flags.manage", "Manage feature flags"),
    ("settings.manage", "Manage system settings"),
    ("audit.view", "View audit logs"),
    ("analytics.view", "View analytics"),
]

ALL_PERMISSION_CODES = [code for code, _ in PERMISSIONS]

# Role → permission codes. super_admin implicitly gets everything.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    ROLE_SUPER_ADMIN: ALL_PERMISSION_CODES,
    ROLE_ADMIN: [
        "users.view",
        "users.manage",
        "profiles.view_any",
        "news.view",
        "news.publish",
        "news.moderate",
        "markets.manage",
        "ai.manage",
        "alerts.manage_any",
        "subscriptions.manage",
        "payments.view",
        "payments.refund",
        "feature_flags.manage",
        "audit.view",
        "analytics.view",
    ],
    ROLE_MODERATOR: [
        "users.view",
        "profiles.view_any",
        "news.view",
        "news.moderate",
        "news.publish",
    ],
    ROLE_PREMIUM: [],
    ROLE_FREE: [],
    ROLE_GUEST: [],
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    ROLE_SUPER_ADMIN: "Full platform access.",
    ROLE_ADMIN: "Operational administration.",
    ROLE_MODERATOR: "Content moderation.",
    ROLE_PREMIUM: "Paid subscriber tier.",
    ROLE_FREE: "Default free tier.",
    ROLE_GUEST: "Unauthenticated/limited access.",
}
