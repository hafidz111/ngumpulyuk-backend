from django.conf import settings
from django.contrib.auth import authenticate
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework.exceptions import AuthenticationFailed

from ngumpulyuk_app.authentication.models import User


class Google:
    @staticmethod
    def validate(access_token):
        try:
            id_info = id_token.verify_oauth2_token(access_token, requests.Request())
            if "accounts.google.com" in id_info["iss"]:
                return id_info
        except Exception:
            pass
        return "Token is invalid or has expired"


def _unique_username(base: str) -> str:
    base = (base or "user")[:40]
    candidate = base
    n = 0
    while User.objects.filter(username=candidate).exists():
        n += 1
        candidate = f"{base}{n}"[:50]
    return candidate


def login_social_user(email, password):
    user = authenticate(email=email, password=password)
    user_tokens = user.tokens()
    return {
        "email": user.email,
        "full_name": user.get_full_name,
        "access_token": str(user_tokens.get("access")),
        "refresh_token": str(user_tokens.get("refresh")),
    }


def register_social_user(provider, email, full_name):
    qs = User.objects.filter(email=email)
    if qs.exists():
        if provider == qs[0].auth_provider:
            return login_social_user(email, settings.SOCIAL_AUTH_PASSWORD)
        raise AuthenticationFailed(detail=f"please continue your login with {qs[0].auth_provider}")
    local = email.split("@")[0]
    username = _unique_username(local)
    register_user = User.objects.create_user(
        email=email,
        full_name=full_name or "User",
        username=username,
        password=settings.SOCIAL_AUTH_PASSWORD,
    )
    register_user.auth_provider = provider
    register_user.is_verified = True
    register_user.save()
    return login_social_user(email=register_user.email, password=settings.SOCIAL_AUTH_PASSWORD)
