"""Transactional auth emails. Uses the configured EMAIL_BACKEND (console in dev)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail

if TYPE_CHECKING:
    from apps.users.models import User


def send_verification_email(user: User, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    send_mail(
        subject="Verify your FinPulse email",
        message=f"Welcome to FinPulse! Confirm your email:\n\n{link}\n",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user: User, uid: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
    send_mail(
        subject="Reset your FinPulse password",
        message=(
            f"Reset your password using this link:\n\n{link}\n\n"
            "If you didn't request this, ignore it."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_otp_email(target: str, code: str) -> None:
    send_mail(
        subject="Your FinPulse login code",
        message=f"Your one-time login code is {code}. It expires in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[target],
    )
