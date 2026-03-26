from __future__ import annotations

from datetime import timedelta
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Notification, TelegramLink, TrainingSession, TrainingSessionOccurrence
from .storage import S3MediaStorage
from .tasks import dispatch_due_notifications


class TelegramBotFlowTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='coach', email='coach@example.com', password='secret123')
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)
        self.bot_client = APIClient()
        _, self.bot_api_key = APIKey.objects.create_key(name='bot')
        self.bot_client.credentials(HTTP_AUTHORIZATION=f'Api-Key {self.bot_api_key}')

    def test_link_confirm_and_training_notification_flow(self) -> None:
        link_response = self.api_client.post('/api/v1/me/telegram-link/')
        self.assertEqual(link_response.status_code, 200)
        code = link_response.data['code']

        confirm_response = self.bot_client.post(
            '/api/v1/bot/telegram-link/confirm/',
            {'code': code, 'telegram_user_id': '123456'},
            format='json',
        )
        self.assertEqual(confirm_response.status_code, 200)

        telegram_link = TelegramLink.objects.get(user=self.user)
        self.assertEqual(telegram_link.telegram_user_id, '123456')
        self.assertTrue(telegram_link.is_active)

        session_time = timezone.localtime(timezone.now() + timedelta(hours=2))
        create_session_response = self.api_client.post(
            '/api/v1/training-sessions/',
            {
                'date': session_time.date().isoformat(),
                'time': session_time.strftime('%H:%M:%S'),
                'timezone': 'Europe/Lisbon',
                'recurrence': 'once',
            },
            format='json',
        )
        self.assertEqual(create_session_response.status_code, 201)

        self.assertEqual(TrainingSession.objects.count(), 1)
        self.assertEqual(TrainingSessionOccurrence.objects.count(), 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.telegram_link, telegram_link)
        self.assertEqual(notification.status, Notification.Status.PENDING)

        bot_sessions_response = self.bot_client.get(
            '/api/v1/bot/training-sessions/upcoming/',
            {'telegram_user_id': '123456'},
        )
        self.assertEqual(bot_sessions_response.status_code, 200)
        self.assertEqual(len(bot_sessions_response.json()), 1)

    @patch('pamp_app.tasks.Bot.send_message')
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test-token'})
    def test_dispatch_due_notifications_marks_notification_sent(self, send_message_mock) -> None:
        telegram_link = TelegramLink.objects.create(
            user=self.user,
            telegram_user_id='123456',
            is_active=True,
            linked_at=timezone.now(),
        )
        session_time = timezone.localtime(timezone.now() + timedelta(minutes=5))
        session = TrainingSession.objects.create(
            profile=self.user.profile,
            date=session_time.date(),
            time=session_time.time().replace(microsecond=0),
            timezone='Europe/Lisbon',
            recurrence='once',
        )
        occurrence = TrainingSessionOccurrence.objects.create(
            training_session=session,
            source_date=session.date,
            starts_at=timezone.now() - timedelta(minutes=1),
        )
        notification = Notification.objects.create(
            telegram_link=telegram_link,
            occurrence=occurrence,
            scheduled_for=timezone.now() - timedelta(minutes=1),
        )

        dispatch_due_notifications()

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.Status.SENT)
        self.assertIsNotNone(notification.sent_at)
        send_message_mock.assert_called_once()


class S3MediaStorageTests(TestCase):
    @override_settings(MEDIA_URL='http://localhost:9000/media/', AWS_QUERYSTRING_AUTH=False)
    def test_absolute_media_url_is_used_for_public_media_links(self) -> None:
        storage = S3MediaStorage()

        self.assertEqual(
            storage.url('post_images/2026/03/26/check.jpg'),
            'http://localhost:9000/media/post_images/2026/03/26/check.jpg',
        )
        self.assertEqual(
            storage.url('media/post_images/2026/03/26/check.jpg'),
            'http://localhost:9000/media/post_images/2026/03/26/check.jpg',
        )


class AuthSecurityTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='athlete',
            email='athlete@example.com',
            password='secret12345',
        )
        self.client = APIClient(enforce_csrf_checks=True)

    def _issue_csrf(self) -> str:
        response = self.client.get('/api/v1/csrf/')
        self.assertEqual(response.status_code, 204)
        csrf_token = response.cookies['csrftoken'].value
        self.client.credentials(HTTP_X_CSRFTOKEN=csrf_token)
        return csrf_token

    def test_login_requires_csrf(self) -> None:
        response = self.client.post(
            '/api/v1/login/',
            {'username': 'athlete', 'password': 'secret12345'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_login_with_csrf_sets_auth_cookies(self) -> None:
        self._issue_csrf()

        response = self.client.post(
            '/api/v1/login/',
            {'username': 'athlete', 'password': 'secret12345'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('my-app-auth', response.cookies)
        self.assertIn('my-refresh-token', response.cookies)

    def test_refresh_rotates_and_blacklists_previous_token(self) -> None:
        self._issue_csrf()
        login_response = self.client.post(
            '/api/v1/login/',
            {'username': 'athlete', 'password': 'secret12345'},
            format='json',
        )
        original_refresh = login_response.cookies['my-refresh-token'].value

        refresh_response = self.client.post('/api/v1/auth/session/refresh/')

        self.assertEqual(refresh_response.status_code, 204)
        rotated_refresh = refresh_response.cookies['my-refresh-token'].value
        self.assertNotEqual(rotated_refresh, original_refresh)

        with self.assertRaises(Exception):
            RefreshToken(original_refresh).check_blacklist()

    def test_logout_blacklists_refresh_cookie(self) -> None:
        self._issue_csrf()
        login_response = self.client.post(
            '/api/v1/login/',
            {'username': 'athlete', 'password': 'secret12345'},
            format='json',
        )
        refresh_token = login_response.cookies['my-refresh-token'].value

        logout_response = self.client.post('/api/v1/auth/session/logout/')

        self.assertEqual(logout_response.status_code, 204)
        with self.assertRaises(Exception):
            RefreshToken(refresh_token).check_blacklist()

    def test_register_requires_email_verification_before_login(self) -> None:
        self._issue_csrf()

        register_response = self.client.post(
            '/api/v1/register/',
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'secret12345',
                'password2': 'secret12345',
            },
            format='json',
        )

        self.assertEqual(register_response.status_code, 202)
        created_user = User.objects.get(username='newuser')
        self.assertFalse(created_user.is_active)
        self.assertEqual(len(mail.outbox), 1)

        verify_link = next(
            line for line in mail.outbox[0].body.splitlines() if line.startswith('http')
        )
        verify_response = self.client.get(verify_link)

        self.assertEqual(verify_response.status_code, 302)
        created_user.refresh_from_db()
        self.assertTrue(created_user.is_active)

    def test_login_rejects_inactive_user(self) -> None:
        inactive_user = User.objects.create_user(
            username='pending-user',
            email='pending@example.com',
            password='secret12345',
            is_active=False,
        )
        self.assertFalse(inactive_user.is_active)
        self._issue_csrf()

        response = self.client.post(
            '/api/v1/login/',
            {'username': 'pending-user', 'password': 'secret12345'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'Verify your email before logging in.')


@override_settings(EXTERNAL_MEDIA_ALLOWED_HOSTS=('cdn.example.com',))
class PostMediaValidationTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='media-user',
            email='media@example.com',
            password='secret12345',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_rejects_invalid_uploaded_image_type(self) -> None:
        invalid_file = SimpleUploadedFile('malware.txt', b'not-an-image', content_type='text/plain')

        response = self.client.post(
            '/api/v1/posts/',
            {
                'title': 'Bad upload',
                'training_type': 'test',
                'description': 'invalid image',
                'images': invalid_file,
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported image file extension', str(response.data))

    def test_rejects_non_allowlisted_external_media_url(self) -> None:
        response = self.client.post(
            '/api/v1/posts/',
            {
                'title': 'Bad url',
                'training_type': 'test',
                'description': 'invalid url',
                'image_urls': 'https://localhost/internal.png',
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('hostname is not in the allowlist', str(response.data))
