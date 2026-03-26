from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    avatar = models.ImageField(
        null=True,
        blank=True,
        upload_to='user_avatars/%Y/%m/%d/',
    )

    def __str__(self) -> str:
        return f'Profile of {self.user.username}'


class Post(models.Model):
    title = models.CharField(max_length=200)
    training_type = models.CharField(max_length=100)
    description = models.TextField()
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='posts')

    def __str__(self) -> str:
        return self.title


class PostImage(models.Model):
    post = models.ForeignKey('Post', related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images/%Y/%m/%d/', null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(Q(image__isnull=False) & Q(image_url__isnull=True))
                | (Q(image__isnull=True) & Q(image_url__isnull=False)),
                name='post_image_requires_exactly_one_source',
            )
        ]

    def __str__(self) -> str:
        return f'PostImage #{self.pk} for post {self.post_id}'


class PostVideo(models.Model):
    post = models.ForeignKey('Post', related_name='videos', on_delete=models.CASCADE)
    video = models.FileField(upload_to='post_videos/%Y/%m/%d/', null=True, blank=True)
    video_url = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(Q(video__isnull=False) & Q(video_url__isnull=True))
                | (Q(video__isnull=True) & Q(video_url__isnull=False)),
                name='post_video_requires_exactly_one_source',
            )
        ]

    def __str__(self) -> str:
        return f'PostVideo #{self.pk} for post {self.post_id}'


class TrainingSession(models.Model):
    class Recurrence(models.TextChoices):
        ONCE = 'once', 'Once'
        WEEKLY = 'weekly', 'Weekly'

    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='training_sessions')
    date = models.DateField()
    time = models.TimeField()
    timezone = models.CharField(max_length=64, default=settings.DEFAULT_USER_TIMEZONE)
    recurrence = models.CharField(max_length=20, choices=Recurrence.choices, default=Recurrence.ONCE)
    days_of_week = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.profile.user.username} - {self.date} at {self.time}'

    def get_zoneinfo(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError:
            return ZoneInfo('UTC')


class TelegramLink(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_user_id = models.CharField(max_length=50, null=True, blank=True, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    linked_at = models.DateTimeField(null=True, blank=True)
    last_interaction_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'TelegramLink for {self.user_id}'

    @property
    def is_linked(self) -> bool:
        return bool(self.telegram_user_id and self.is_active)


class TelegramLinkToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telegram_link_tokens')
    code_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'expires_at']),
        ]

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at


class TrainingSessionOccurrence(models.Model):
    training_session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name='occurrences',
    )
    starts_at = models.DateTimeField(db_index=True)
    source_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['training_session', 'starts_at'],
                name='unique_training_session_occurrence',
            ),
        ]
        ordering = ['starts_at']

    def __str__(self) -> str:
        return f'Occurrence for session {self.training_session_id} at {self.starts_at}'


class Notification(models.Model):
    class Channel(models.TextChoices):
        TELEGRAM = 'telegram', 'Telegram'

    class Kind(models.TextChoices):
        TRAINING_REMINDER = 'training_reminder', 'Training Reminder'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    telegram_link = models.ForeignKey(
        TelegramLink,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    occurrence = models.ForeignKey(
        TrainingSessionOccurrence,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.TELEGRAM)
    kind = models.CharField(max_length=50, choices=Kind.choices, default=Kind.TRAINING_REMINDER)
    scheduled_for = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['telegram_link', 'occurrence', 'kind'],
                name='unique_notification_per_occurrence_kind',
            ),
        ]
        ordering = ['scheduled_for']

    def __str__(self) -> str:
        return f'{self.kind} for occurrence {self.occurrence_id}'
