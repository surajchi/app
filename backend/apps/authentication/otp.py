"""One-time-passcode issue/verify (hashed at rest, attempt-limited)."""

from __future__ import annotations

import secrets
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from apps.authentication.models import OTPCode

if TYPE_CHECKING:
    from apps.users.models import User


def generate_numeric_code(length: int) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def issue_otp(
    target: str,
    purpose: str,
    user: User | None = None,
    channel: str = str(OTPCode.Channel.EMAIL),
) -> str:
    """Create an OTP and return the plaintext code (to be delivered)."""
    code = generate_numeric_code(settings.OTP_LENGTH)
    OTPCode.objects.create(
        user=user,
        target=target.lower().strip(),
        channel=channel,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(seconds=settings.OTP_TTL_SECONDS),
    )
    return code


def verify_otp(target: str, purpose: str, code: str) -> OTPCode | None:
    """Return the consumed OTPCode on success, else None."""
    otp = (
        OTPCode.objects.filter(
            target=target.lower().strip(),
            purpose=purpose,
            consumed_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )
    if otp is None:
        return None

    otp.attempts += 1
    otp.save(update_fields=["attempts"])
    if otp.attempts > settings.OTP_MAX_ATTEMPTS:
        return None
    if not check_password(str(code).strip(), otp.code_hash):
        return None

    otp.consumed_at = timezone.now()
    otp.save(update_fields=["consumed_at"])
    return otp
