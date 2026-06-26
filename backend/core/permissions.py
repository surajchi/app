"""Reusable DRF permission classes. RBAC/plan gating is added in Phase 2."""
from __future__ import annotations

from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(BasePermission):
    """Object-level permission: the object's owner field must match request.user.

    Views may override the attribute name via ``owner_field`` (default: ``user``).
    """

    owner_field = "user"

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        field = getattr(view, "owner_field", self.owner_field)
        return getattr(obj, field, None) == request.user


class IsOwnerOrReadOnly(IsOwner):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return super().has_object_permission(request, view, obj)
