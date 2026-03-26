from __future__ import annotations

from typing import Protocol

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.http import HttpRequest

UserModel = get_user_model()


class SocialAccountLike(Protocol):
    extra_data: dict[str, object]


class SocialLoginLike(Protocol):
    account: SocialAccountLike

    def connect(self, request: HttpRequest, user: User) -> None: ...


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLoginLike) -> None:
        if getattr(request.user, 'is_authenticated', False):
            return

        email = str(sociallogin.account.extra_data.get('email') or '').lower()
        if not email:
            return

        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            return

        sociallogin.connect(request, user)
