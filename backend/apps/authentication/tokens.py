"""Signed, expiring tokens for email verification and the 2FA login challenge."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core import signing

if TYPE_CHECKING:
    from apps.users.models import User

EMAIL_VERIFY_SALT = "finpulse.email-verify"
TWOFA_CHALLENGE_SALT = "finpulse.2fa-challenge"


def make_email_verification_token(user: User) -> str:
    return signing.dumps({"uid": str(user.id), "email": user.email}, salt=EMAIL_VERIFY_SALT)


def read_email_verification_token(token: str, max_age: int) -> dict[str, Any]:
    return signing.loads(token, salt=EMAIL_VERIFY_SALT, max_age=max_age)


def make_2fa_challenge_token(user: User) -> str:
    return signing.dumps({"uid": str(user.id)}, salt=TWOFA_CHALLENGE_SALT)


def read_2fa_challenge_token(token: str, max_age: int) -> dict[str, Any]:
    return signing.loads(token, salt=TWOFA_CHALLENGE_SALT, max_age=max_age)
