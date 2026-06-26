from rest_framework import serializers

from apps.profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "avatar_url",
            "country",
            "timezone",
            "base_currency",
            "language",
            "bio",
            "experience_level",
            "risk_appetite",
            "updated_at",
        )
        read_only_fields = ("updated_at",)

    def validate_base_currency(self, value: str) -> str:
        return value.upper()

    def validate_country(self, value: str) -> str:
        return value.upper()
