from __future__ import annotations

from typing import Protocol

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.http import HttpResponse

from .services import TokenService, set_auth_cookies

class StrategyLike(Protocol):
    request: HttpRequest

    def redirect(self, url: str) -> HttpResponse: ...


def generate_jwt_tokens(
    strategy: StrategyLike,
    details: object,
    user: User,
    *_args: object,
    **_kwargs: object,
) -> HttpResponse:
    token_pair = TokenService.issue_for_user(user)
    next_url = strategy.request.GET.get('next') or settings.FRONTEND_URL or '/'
    response = strategy.redirect(next_url)
    return set_auth_cookies(response, token_pair)
