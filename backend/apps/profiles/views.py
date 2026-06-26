from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.profiles.models import Profile
from apps.profiles.serializers import ProfileSerializer


@extend_schema(tags=["profile"])
class ProfileView(generics.RetrieveUpdateAPIView):
    """Read or update the authenticated user's profile (GET / PATCH / PUT)."""

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> Profile:
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile
