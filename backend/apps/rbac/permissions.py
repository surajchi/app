"""DRF permission classes backed by RBAC.

Usage on a view:
    class FlagView(APIView):
        permission_classes = [IsAuthenticated, HasPermission]
        required_permission = "feature_flags.manage"
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.rbac.services import user_has_permission, user_has_role


class HasPermission(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        code = getattr(view, "required_permission", None)
        if code is None:
            return True
        return user_has_permission(request.user, code)


class HasAnyRole(BasePermission):
    message = "Your role does not allow this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        roles = getattr(view, "required_roles", None)
        if not roles:
            return True
        return user_has_role(request.user, *roles)
