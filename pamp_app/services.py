from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Notification,
    Post,
    PostImage,
    PostVideo,
    TelegramLink,
    TelegramLinkToken,
    TrainingSession,
    TrainingSessionOccurrence,
)


@dataclass(frozen=True)
class TokenPair:
    access: str
    refresh: str


class TokenService:
    @staticmethod
    def issue_for_user(user: User) -> TokenPair:
        refresh = RefreshToken.for_user(user)
        return TokenPair(access=str(refresh.access_token), refresh=str(refresh))

    @staticmethod
    def issue_from_refresh(refresh_token: str) -> TokenPair:
        refresh = RefreshToken(refresh_token)
        try:
            refresh.blacklist()
        except AttributeError:
            pass
        return TokenPair(access=str(refresh.access_token), refresh=str(refresh))


def set_auth_cookies(response: HttpResponse, token_pair: TokenPair) -> HttpResponse:
    max_age_access = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
    max_age_refresh = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
    response.set_cookie(
        settings.JWT_AUTH_COOKIE,
        token_pair.access,
        max_age=max_age_access,
        httponly=True,
        secure=settings.JWT_AUTH_SECURE,
        samesite=settings.JWT_AUTH_SAMESITE,
        path='/',
    )
    response.set_cookie(
        settings.JWT_AUTH_REFRESH_COOKIE,
        token_pair.refresh,
        max_age=max_age_refresh,
        httponly=True,
        secure=settings.JWT_AUTH_SECURE,
        samesite=settings.JWT_AUTH_SAMESITE,
        path='/',
    )
    return response


def clear_auth_cookies(response: HttpResponse) -> HttpResponse:
    response.delete_cookie(settings.JWT_AUTH_COOKIE, path='/', samesite=settings.JWT_AUTH_SAMESITE)
    response.delete_cookie(settings.JWT_AUTH_REFRESH_COOKIE, path='/', samesite=settings.JWT_AUTH_SAMESITE)
    return response


def blacklist_refresh_token(refresh_token: str | None) -> None:
    if not refresh_token:
        return

    try:
        RefreshToken(refresh_token).blacklist()
    except Exception:
        pass


class TelegramLinkError(Exception):
    pass


class TelegramLinkAlreadyConfirmed(TelegramLinkError):
    pass


class TelegramLinkNotFound(TelegramLinkError):
    pass


class TelegramLinkExpired(TelegramLinkError):
    pass


class PostMediaValidationError(Exception):
    pass


class TelegramLinkService:
    TOKEN_TTL_MINUTES = 15

    @staticmethod
    def _hash_code(raw_code: str) -> str:
        return hashlib.sha256(raw_code.encode('utf-8')).hexdigest()

    def request_link(self, user: User) -> dict[str, object]:
        link, _created = TelegramLink.objects.get_or_create(user=user)

        if link.is_linked:
            raise TelegramLinkAlreadyConfirmed('Telegram already linked.')

        TelegramLinkToken.objects.filter(user=user, used_at__isnull=True).delete()

        raw_code = secrets.token_urlsafe(24)
        token = TelegramLinkToken.objects.create(
            user=user,
            code_hash=self._hash_code(raw_code),
            expires_at=timezone.now() + timedelta(minutes=self.TOKEN_TTL_MINUTES),
        )
        return {
            'code': raw_code,
            'expires_at': token.expires_at,
        }

    def get_status(self, user: User) -> dict[str, object]:
        try:
            link = TelegramLink.objects.get(user=user)
        except TelegramLink.DoesNotExist:
            return {'linked': False, 'status': 'no_link'}

        active_token = (
            TelegramLinkToken.objects.filter(user=user, used_at__isnull=True, expires_at__gt=timezone.now())
            .order_by('-created_at')
            .first()
        )

        if link.is_linked:
            return {'linked': True, 'status': 'linked'}
        if active_token is None:
            return {'linked': False, 'status': 'expired'}
        return {'linked': False, 'status': 'pending', 'expires_at': active_token.expires_at}

    @transaction.atomic
    def confirm_link(self, code: str, telegram_user_id: str) -> TelegramLink:
        try:
            token = TelegramLinkToken.objects.select_for_update().select_related('user').get(
                code_hash=self._hash_code(code),
                used_at__isnull=True,
            )
        except TelegramLinkToken.DoesNotExist as exc:
            raise TelegramLinkNotFound('Invalid linking code.') from exc

        if token.is_expired():
            raise TelegramLinkExpired('Linking code has expired.')

        now = timezone.now()
        TelegramLink.objects.select_for_update().filter(
            telegram_user_id=telegram_user_id
        ).exclude(user=token.user).update(
            telegram_user_id=None,
            linked_at=None,
            is_active=False,
        )

        link, _created = TelegramLink.objects.select_for_update().get_or_create(user=token.user)
        link.telegram_user_id = telegram_user_id
        link.linked_at = now
        link.last_interaction_at = now
        link.is_active = True
        link.save(update_fields=['telegram_user_id', 'linked_at', 'last_interaction_at', 'is_active'])

        token.used_at = now
        token.save(update_fields=['used_at'])

        TrainingReminderService().sync_user_notifications(token.user)
        return link

    def get_link_by_telegram_user_id(self, telegram_user_id: str) -> TelegramLink | None:
        return (
            TelegramLink.objects.select_related('user')
            .filter(telegram_user_id=telegram_user_id, is_active=True)
            .first()
        )

    def touch_interaction(self, telegram_user_id: str) -> None:
        TelegramLink.objects.filter(telegram_user_id=telegram_user_id, is_active=True).update(
            last_interaction_at=timezone.now()
        )


class TrainingReminderService:
    OCCURRENCE_HORIZON_DAYS = 30

    @staticmethod
    def _parse_days_of_week(session: TrainingSession) -> set[int]:
        if session.recurrence != TrainingSession.Recurrence.WEEKLY:
            return set()
        if not session.days_of_week:
            return {session.date.weekday()}

        result: set[int] = set()
        for raw_part in session.days_of_week.split(','):
            part = raw_part.strip().lower()
            if not part:
                continue
            if part.isdigit():
                value = int(part)
                if 0 <= value <= 6:
                    result.add(value)
                continue

            name_map = {
                'mon': 0,
                'monday': 0,
                'tue': 1,
                'tuesday': 1,
                'wed': 2,
                'wednesday': 2,
                'thu': 3,
                'thursday': 3,
                'fri': 4,
                'friday': 4,
                'sat': 5,
                'saturday': 5,
                'sun': 6,
                'sunday': 6,
            }
            if part in name_map:
                result.add(name_map[part])

        return result or {session.date.weekday()}

    @staticmethod
    def _localized_start(session: TrainingSession, session_date: date) -> datetime:
        local_zone = session.get_zoneinfo()
        naive = datetime.combine(session_date, session.time if isinstance(session.time, time) else session.time)
        localized = naive.replace(tzinfo=local_zone)
        return localized.astimezone(dt_timezone.utc)

    def _build_occurrences(self, session: TrainingSession, *, horizon_days: int | None = None) -> list[TrainingSessionOccurrence]:
        now = timezone.now()
        horizon = now + timedelta(days=horizon_days or self.OCCURRENCE_HORIZON_DAYS)
        occurrences: list[TrainingSessionOccurrence] = []

        if session.recurrence == TrainingSession.Recurrence.ONCE:
            starts_at = self._localized_start(session, session.date)
            if starts_at >= now and starts_at <= horizon:
                occurrences.append(
                    TrainingSessionOccurrence(
                        training_session=session,
                        starts_at=starts_at,
                        source_date=session.date,
                    )
                )
            return occurrences

        weekdays = self._parse_days_of_week(session)
        try:
            session_zone = ZoneInfo(session.timezone)
        except ZoneInfoNotFoundError:
            session_zone = dt_timezone.utc

        cursor = max(session.date, now.astimezone(session_zone).date())
        end_date = horizon.astimezone(session_zone).date()

        while cursor <= end_date:
            if cursor.weekday() in weekdays:
                starts_at = self._localized_start(session, cursor)
                if starts_at >= now:
                    occurrences.append(
                        TrainingSessionOccurrence(
                            training_session=session,
                            starts_at=starts_at,
                            source_date=cursor,
                        )
                    )
            cursor += timedelta(days=1)

        return occurrences

    @transaction.atomic
    def sync_training_session(self, session: TrainingSession) -> None:
        now = timezone.now()
        session.occurrences.filter(starts_at__gte=now).delete()

        occurrences = self._build_occurrences(session)
        if occurrences:
            TrainingSessionOccurrence.objects.bulk_create(occurrences, ignore_conflicts=True)

        self._sync_notifications_for_session(session)

    @transaction.atomic
    def sync_user_notifications(self, user: User) -> None:
        sessions = (
            TrainingSession.objects.select_related('profile', 'profile__user')
            .filter(profile__user=user)
            .order_by('date', 'time')
        )
        for session in sessions:
            self.sync_training_session(session)

    @transaction.atomic
    def clear_training_session(self, session: TrainingSession) -> None:
        Notification.objects.filter(occurrence__training_session=session).delete()
        session.occurrences.all().delete()

    def _sync_notifications_for_session(self, session: TrainingSession) -> None:
        link = (
            TelegramLink.objects.filter(user=session.profile.user, is_active=True)
            .exclude(telegram_user_id__isnull=True)
            .exclude(telegram_user_id='')
            .first()
        )
        if link is None:
            Notification.objects.filter(occurrence__training_session=session).delete()
            return

        now = timezone.now()
        occurrences = session.occurrences.filter(starts_at__gte=now)
        Notification.objects.filter(
            occurrence__training_session=session,
            telegram_link=link,
            status=Notification.Status.PENDING,
            scheduled_for__gte=now,
        ).exclude(occurrence__in=occurrences).delete()

        existing_occurrence_ids = set(
            Notification.objects.filter(
                occurrence__training_session=session,
                telegram_link=link,
                kind=Notification.Kind.TRAINING_REMINDER,
            ).values_list('occurrence_id', flat=True)
        )

        new_notifications = []
        for occurrence in occurrences:
            if occurrence.id in existing_occurrence_ids:
                continue
            new_notifications.append(
                Notification(
                    telegram_link=link,
                    occurrence=occurrence,
                    scheduled_for=occurrence.starts_at,
                    payload={
                        'date': occurrence.starts_at.date().isoformat(),
                        'time': occurrence.starts_at.astimezone(session.get_zoneinfo()).strftime('%H:%M'),
                        'timezone': session.timezone,
                    },
                )
            )

        if new_notifications:
            Notification.objects.bulk_create(new_notifications, ignore_conflicts=True)

    def sync_all_linked_users(self) -> None:
        users = User.objects.filter(telegramlink__is_active=True).distinct()
        for user in users.iterator():
            self.sync_user_notifications(user)

    def get_upcoming_sessions_for_link(self, telegram_link: TelegramLink) -> QuerySet[TrainingSessionOccurrence]:
        return (
            TrainingSessionOccurrence.objects.select_related('training_session', 'training_session__profile', 'training_session__profile__user')
            .filter(training_session__profile__user=telegram_link.user, starts_at__gte=timezone.now())
            .order_by('starts_at')
        )


class PostMediaService:
    IMAGE_FIELDS = {'images', 'image_urls', 'existing_images'}
    VIDEO_FIELDS = {'videos', 'video_urls', 'existing_videos'}

    @staticmethod
    def _get_list_value(container: Any, key: str) -> list[Any]:
        if hasattr(container, 'getlist'):
            return list(container.getlist(key))
        value = container.get(key)
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    @classmethod
    def _has_any_input(cls, request: Request, field_names: set[str]) -> bool:
        data_keys = set(getattr(request.data, 'keys', lambda: [])())
        file_keys = set(getattr(request.FILES, 'keys', lambda: [])())
        return bool(field_names & (data_keys | file_keys))

    @staticmethod
    def _validate_single_source(file_values: list[Any], url_values: list[Any], kind: str) -> None:
        if any(file_values) and any(url_values):
            raise PostMediaValidationError(f'Provide either {kind} files or {kind} URLs per item, not both.')

    @classmethod
    @transaction.atomic
    def sync(cls, post: Post, request: Request) -> None:
        image_files = cls._get_list_value(request.FILES, 'images')
        image_urls = [value for value in cls._get_list_value(request.data, 'image_urls') if value]
        video_files = cls._get_list_value(request.FILES, 'videos')
        video_urls = [value for value in cls._get_list_value(request.data, 'video_urls') if value]

        existing_image_ids = {
            int(value)
            for value in cls._get_list_value(request.data, 'existing_images')
            if str(value).isdigit()
        }
        existing_video_ids = {
            int(value)
            for value in cls._get_list_value(request.data, 'existing_videos')
            if str(value).isdigit()
        }

        image_update_requested = cls._has_any_input(request, cls.IMAGE_FIELDS)
        video_update_requested = cls._has_any_input(request, cls.VIDEO_FIELDS)

        cls._validate_single_source(image_files, image_urls, 'image')
        cls._validate_single_source(video_files, video_urls, 'video')

        if image_update_requested:
            retained_images = post.images.filter(id__in=existing_image_ids)
            if existing_image_ids and retained_images.count() != len(existing_image_ids):
                raise PostMediaValidationError('existing_images contains items that do not belong to this post.')
            post.images.exclude(id__in=existing_image_ids).delete()
            for image_file in image_files:
                PostImage.objects.create(post=post, image=image_file)
            for image_url in image_urls:
                PostImage.objects.create(post=post, image_url=image_url)

        if video_update_requested:
            retained_videos = post.videos.filter(id__in=existing_video_ids)
            if existing_video_ids and retained_videos.count() != len(existing_video_ids):
                raise PostMediaValidationError('existing_videos contains items that do not belong to this post.')
            post.videos.exclude(id__in=existing_video_ids).delete()
            for video_file in video_files:
                PostVideo.objects.create(post=post, video=video_file)
            for video_url in video_urls:
                PostVideo.objects.create(post=post, video_url=video_url)
