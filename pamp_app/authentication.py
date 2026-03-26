from __future__ import annotations

from typing import Protocol

from django.contrib.auth.models import User
from django.http import HttpRequest

from .models import Profile

class UserLike(Protocol):
    email: str
    id: int

    def check_password(self, raw_password: str) -> bool: ...


class EmailAuthBackend:
    """Authenticate users by e-mail address."""

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: str,
    ) -> User | None:
        email = (username or kwargs.get('email') or '').strip().lower()

        if not email or not password:
            return None

        try:
            user = User.objects.get(email=email)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        return user if user.check_password(password) else None

    def get_user(self, user_id: int) -> User | None:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def create_profile(backend: object, user: User, *_args: object, **_kwargs: object) -> None:
    """Create a user profile for social authentication flows."""
    Profile.objects.get_or_create(user=user)
