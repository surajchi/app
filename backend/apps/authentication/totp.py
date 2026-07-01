"""TOTP (2FA) and recovery-code helpers built on pyotp."""

from __future__ import annotations

import secrets

import pyotp
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password

RECOVERY_CODE_COUNT = 8


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, account_name: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=account_name, issuer_name=settings.TWO_FACTOR_ISSUER
    )


def verify_totp(secret: str, code: str) -> bool:
    # valid_window=1 tolerates ~30s clock drift on either side.
    return pyotp.TOTP(secret).verify(str(code).strip(), valid_window=1)


def generate_recovery_codes(count: int = RECOVERY_CODE_COUNT) -> list[str]:
    return [f"{secrets.token_hex(4)}-{secrets.token_hex(4)}" for _ in range(count)]


def hash_recovery_codes(codes: list[str]) -> list[str]:
    return [make_password(code) for code in codes]


def consume_recovery_code(code: str, hashed_codes: list[str]) -> list[str] | None:
    """Return the remaining hashes if ``code`` matches one, else None."""
    for index, hashed in enumerate(hashed_codes):
        if check_password(code, hashed):
            return hashed_codes[:index] + hashed_codes[index + 1 :]
    return None
