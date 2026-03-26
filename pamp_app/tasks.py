from __future__ import annotations

import logging
import os

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from telegram import Bot

from .models import Notification
from .services import TrainingReminderService

logger = logging.getLogger(__name__)


def _get_bot() -> Bot:
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN is not configured')
    return Bot(token=token)


def _format_training_message(notification: Notification) -> str:
    occurrence = notification.occurrence
    session = occurrence.training_session
    local_start = occurrence.starts_at.astimezone(session.get_zoneinfo())
    return (
        'Reminder: you have a training session on '
        f'{local_start.strftime("%Y-%m-%d")} at {local_start.strftime("%H:%M")} '
        f'({session.timezone}).'
    )


@shared_task
def refresh_training_notifications() -> None:
    TrainingReminderService().sync_all_linked_users()


@shared_task
def dispatch_due_notifications() -> None:
    now = timezone.now()
    notifications = list(
        Notification.objects.select_related(
            'telegram_link',
            'occurrence',
            'occurrence__training_session',
        )
        .filter(
            status=Notification.Status.PENDING,
            scheduled_for__lte=now,
            telegram_link__is_active=True,
        )
        .order_by('scheduled_for')[:100]
    )
    if not notifications:
        return

    bot = _get_bot()
    for notification in notifications:
        chat_id = notification.telegram_link.telegram_user_id
        if not chat_id:
            continue

        try:
            with transaction.atomic():
                locked = Notification.objects.select_for_update().get(pk=notification.pk)
                if locked.status != Notification.Status.PENDING:
                    continue
                bot.send_message(chat_id=chat_id, text=_format_training_message(locked))
                locked.status = Notification.Status.SENT
                locked.sent_at = timezone.now()
                locked.last_error = ''
                locked.save(update_fields=['status', 'sent_at', 'last_error', 'updated_at'])
        except Exception as exc:
            logger.warning('Telegram notification delivery failed for notification %s', notification.pk)
            Notification.objects.filter(pk=notification.pk).update(
                status=Notification.Status.FAILED,
                last_error=str(exc),
                updated_at=timezone.now(),
            )
