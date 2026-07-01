from unittest.mock import patch

import pyotp
import pytest
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from apps.authentication import tokens
from apps.authentication.models import OAuthAccount, TwoFactor
from apps.authentication.oauth import OAuthError, OAuthUserInfo
from apps.users.models import User
from apps.users.tests.factories import DEFAULT_TEST_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

VERIFY_EMAIL = "/api/v1/auth/verify-email/"
RESEND = "/api/v1/auth/resend-verification/"
FORGOT = "/api/v1/auth/forgot-password/"
RESET = "/api/v1/auth/reset-password/"
OTP_REQUEST = "/api/v1/auth/otp/request/"
OTP_VERIFY = "/api/v1/auth/otp/verify/"
TFA_SETUP = "/api/v1/auth/2fa/setup/"
TFA_VERIFY = "/api/v1/auth/2fa/verify/"
TFA_DISABLE = "/api/v1/auth/2fa/disable/"
TFA_LOGIN = "/api/v1/auth/2fa/login/"
LOGIN = "/api/v1/auth/login/"
GOOGLE = "/api/v1/auth/oauth/google/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


# --- email verification -----------------------------------------------------


def test_verify_email_with_valid_token(client):
    user = UserFactory()
    assert user.email_verified_at is None
    token = tokens.make_email_verification_token(user)
    resp = client.post(VERIFY_EMAIL, {"token": token}, format="json")
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.email_verified_at is not None


def test_verify_email_with_bad_token(client):
    resp = client.post(VERIFY_EMAIL, {"token": "garbage"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["success"] is False


def test_resend_verification_always_ok(client):
    UserFactory(email="rv@example.com")
    assert client.post(RESEND, {"email": "rv@example.com"}, format="json").status_code == 200
    assert client.post(RESEND, {"email": "nobody@example.com"}, format="json").status_code == 200


# --- password reset ---------------------------------------------------------


def test_forgot_password_does_not_leak(client):
    UserFactory(email="fp@example.com")
    assert client.post(FORGOT, {"email": "fp@example.com"}, format="json").status_code == 200
    assert client.post(FORGOT, {"email": "ghost@example.com"}, format="json").status_code == 200


def test_reset_password_flow(client):
    user = UserFactory(email="reset@example.com")
    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    token = default_token_generator.make_token(user)
    resp = client.post(
        RESET, {"uid": uid, "token": token, "new_password": "BrandNew!234"}, format="json"
    )
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.check_password("BrandNew!234")


def test_reset_password_invalid_token(client):
    user = UserFactory()
    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    resp = client.post(
        RESET, {"uid": uid, "token": "bad-token", "new_password": "BrandNew!234"}, format="json"
    )
    assert resp.status_code == 400


# --- OTP login --------------------------------------------------------------


def test_otp_login_flow(client):
    UserFactory(email="otp@example.com")
    with patch("apps.authentication.otp.generate_numeric_code", return_value="123456"):
        assert (
            client.post(OTP_REQUEST, {"email": "otp@example.com"}, format="json").status_code == 200
        )
    resp = client.post(OTP_VERIFY, {"email": "otp@example.com", "code": "123456"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["data"]["access"]


def test_otp_verify_wrong_code(client):
    UserFactory(email="otp2@example.com")
    with patch("apps.authentication.otp.generate_numeric_code", return_value="123456"):
        client.post(OTP_REQUEST, {"email": "otp2@example.com"}, format="json")
    resp = client.post(OTP_VERIFY, {"email": "otp2@example.com", "code": "000000"}, format="json")
    assert resp.status_code == 400


# --- 2FA --------------------------------------------------------------------


def _enable_2fa(client, user) -> str:
    client.force_authenticate(user)
    secret = client.post(TFA_SETUP, {}, format="json").json()["data"]["secret"]
    code = pyotp.TOTP(secret).now()
    resp = client.post(TFA_VERIFY, {"code": code}, format="json")
    assert resp.status_code == 200
    assert len(resp.json()["data"]["recovery_codes"]) == 8
    client.force_authenticate(None)
    return secret


def test_2fa_enable(client):
    user = UserFactory(email="tfa@example.com")
    _enable_2fa(client, user)
    user.refresh_from_db()
    assert user.is_2fa_enabled is True
    assert TwoFactor.objects.get(user=user).is_enabled is True


def test_login_with_2fa_returns_challenge_then_completes(client):
    user = UserFactory(email="tfa2@example.com")
    secret = _enable_2fa(client, user)

    login = client.post(
        LOGIN, {"email": "tfa2@example.com", "password": DEFAULT_TEST_PASSWORD}, format="json"
    )
    assert login.status_code == 200
    body = login.json()["data"]
    assert body["challenge"] == "2fa"

    completed = client.post(
        TFA_LOGIN,
        {"challenge_token": body["challenge_token"], "code": pyotp.TOTP(secret).now()},
        format="json",
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["access"]


def test_2fa_login_wrong_code(client):
    user = UserFactory(email="tfa3@example.com")
    _enable_2fa(client, user)
    login = client.post(
        LOGIN, {"email": "tfa3@example.com", "password": DEFAULT_TEST_PASSWORD}, format="json"
    )
    token = login.json()["data"]["challenge_token"]
    resp = client.post(TFA_LOGIN, {"challenge_token": token, "code": "000000"}, format="json")
    assert resp.status_code == 401


def test_2fa_disable(client):
    user = UserFactory(email="tfa4@example.com")
    secret = _enable_2fa(client, user)
    client.force_authenticate(user)
    resp = client.post(TFA_DISABLE, {"code": pyotp.TOTP(secret).now()}, format="json")
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.is_2fa_enabled is False


# --- OAuth ------------------------------------------------------------------


def test_oauth_google_creates_user_and_tokens(client):
    info = OAuthUserInfo(
        provider="google", uid="g-123", email="goog@example.com", name="Goog User", raw={}
    )
    with patch("apps.authentication.oauth.verify_google_token", return_value=info):
        resp = client.post(GOOGLE, {"id_token": "fake"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["data"]["user"]["email"] == "goog@example.com"
    assert User.objects.filter(email="goog@example.com").exists()
    assert OAuthAccount.objects.filter(provider="google", provider_uid="g-123").exists()


def test_oauth_google_links_existing_email(client):
    existing = UserFactory(email="link@example.com")
    info = OAuthUserInfo(provider="google", uid="g-999", email="link@example.com", name="", raw={})
    with patch("apps.authentication.oauth.verify_google_token", return_value=info):
        resp = client.post(GOOGLE, {"id_token": "fake"}, format="json")
    assert resp.status_code == 200
    assert OAuthAccount.objects.get(provider_uid="g-999").user_id == existing.id


def test_oauth_invalid_token_returns_400(client):
    with patch(
        "apps.authentication.oauth.verify_google_token",
        side_effect=OAuthError("Invalid Google token."),
    ):
        resp = client.post(GOOGLE, {"id_token": "bad"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["success"] is False
