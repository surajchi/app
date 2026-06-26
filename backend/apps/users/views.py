"""Authenticated user self-management: GET / PATCH / DELETE /users/me."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.models import User
from apps.users.serializers import UserSerializer, UserUpdateSerializer


@extend_schema(tags=["users"])
class MeView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        partial = bool(kwargs.get("partial", False))
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Re-serialize with the full representation (incl. roles).
        return Response(UserSerializer(instance).data)

    def perform_destroy(self, instance: User) -> None:
        # Soft delete: deactivate + mark deleted. JWT auth rejects inactive users,
        # so existing tokens stop working immediately.
        instance.soft_delete()
