from __future__ import annotations

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import TemplateDoesNotExist
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from .models import Notification, Post, Profile, TrainingSession
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    GoogleLoginSerializer,
    LoginSerializer,
    PostSerializer,
    ProfileSerializer,
    RegisterSerializer,
    TrainingSessionSerializer,
    UserSerializer,
)
from .services import (
    EmailVerificationError,
    EmailVerificationService,
    TelegramLinkAlreadyConfirmed,
    TelegramLinkExpired,
    TelegramLinkNotFound,
    TelegramLinkService,
    TrainingReminderService,
    TokenPair,
    TokenService,
    blacklist_refresh_token,
    clear_auth_cookies,
    set_auth_cookies,
)

telegram_link_service = TelegramLinkService()
training_reminder_service = TrainingReminderService()


class AuthRateThrottle(AnonRateThrottle):
    scope = 'auth'


class TelegramConfirmRateThrottle(AnonRateThrottle):
    scope = 'telegram_confirm'


class CookieAuthMixin:
    @staticmethod
    def set_auth_cookies(response: Response, token_pair: TokenPair) -> Response:
        return set_auth_cookies(response, token_pair)

    @staticmethod
    def clear_auth_cookies(response: Response) -> Response:
        return clear_auth_cookies(response)


def google_callback(_request: HttpRequest) -> JsonResponse:
    return JsonResponse({'message': 'Authentication successful'})


@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_cookie(request: Request) -> Response:
    return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name='dispatch')
class GoogleLoginView(CookieAuthMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request: Request) -> Response:
        serializer = GoogleLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token_pair = TokenService.issue_for_user(user)
        response = Response({'user': UserSerializer(user).data}, status=status.HTTP_200_OK)
        return self.set_auth_cookies(response, token_pair)


@method_decorator(csrf_protect, name='dispatch')
class RefreshSessionView(CookieAuthMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        refresh_cookie = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not refresh_cookie:
            return Response({'detail': 'Refresh cookie is missing.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token_pair = TokenService.issue_from_refresh(refresh_cookie)
        except Exception:
            response = Response({'detail': 'Refresh token is invalid.'}, status=status.HTTP_401_UNAUTHORIZED)
            return self.clear_auth_cookies(response)

        response = Response(status=status.HTTP_204_NO_CONTENT)
        return self.set_auth_cookies(response, token_pair)


@method_decorator(csrf_protect, name='dispatch')
class LogoutView(CookieAuthMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        blacklist_refresh_token(request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE))
        response = Response(status=status.HTTP_204_NO_CONTENT)
        return self.clear_auth_cookies(response)


def index(request: HttpRequest) -> HttpResponse:
    try:
        return render(request, 'index.html')
    except TemplateDoesNotExist:
        return redirect(settings.FRONTEND_URL)


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Profile]:
        return Profile.objects.select_related('user').filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request: Request) -> Response:
        profile, _created = Profile.objects.get_or_create(user=request.user)
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        serializer = self.get_serializer(profile, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('profile', 'profile__user').prefetch_related('images', 'videos').order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'training_type', 'profile__user__username']
    ordering_fields = ['created_at', 'updated_at', 'views', 'title', 'training_type']
    ordering = ['-created_at']

    def get_queryset(self) -> QuerySet[Post]:
        queryset = Post.objects.select_related('profile', 'profile__user').prefetch_related('images', 'videos').order_by('-created_at')
        scope = self.request.query_params.get('scope')
        mine = self.request.query_params.get('mine')
        exclude_mine = self.request.query_params.get('exclude_mine')

        if scope == 'mine' or mine == 'true':
            return queryset.filter(profile__user=self.request.user)
        if scope == 'all' or exclude_mine == 'true':
            return queryset.exclude(profile__user=self.request.user)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(name='scope', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Resource scope.', enum=['all', 'mine']),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Search by username, title, description, or training type.'),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Ordering field, for example "-created_at" or "views".'),
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description='Page number for paginated results.'),
        ]
    )
    def list(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer: PostSerializer) -> None:
        profile, _created = Profile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)


class TrainingSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'time', 'recurrence']
    ordering = ['date']

    def get_queryset(self) -> QuerySet[TrainingSession]:
        return TrainingSession.objects.select_related('profile', 'profile__user').filter(profile__user=self.request.user)

    def perform_create(self, serializer: TrainingSessionSerializer) -> None:
        profile, _created = Profile.objects.get_or_create(user=self.request.user)
        session = serializer.save(profile=profile)
        training_reminder_service.sync_training_session(session)

    def perform_update(self, serializer: TrainingSessionSerializer) -> None:
        session = serializer.save()
        training_reminder_service.sync_training_session(session)

    def perform_destroy(self, instance: TrainingSession) -> None:
        training_reminder_service.clear_training_session(instance)
        instance.delete()


class MyTrainingSessionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        sessions = TrainingSession.objects.select_related('profile', 'profile__user').filter(profile__user=request.user).order_by('date')
        serializer = TrainingSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def register(request: Request) -> Response:
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    EmailAddress.objects.update_or_create(
        user=user,
        email=user.email,
        defaults={'primary': True, 'verified': False},
    )
    profile, _created = Profile.objects.get_or_create(user=user)
    EmailVerificationService.send_verification_email(user, request._request)
    return Response(
        {
            'detail': 'Verification email sent. Open the link in your inbox to activate the account.',
            'user': UserSerializer(profile.user).data,
        },
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request: Request) -> HttpResponse:
    token = request.query_params.get('token', '')
    try:
        EmailVerificationService.verify_token(token)
    except EmailVerificationError:
        return redirect(settings.EMAIL_VERIFICATION_FAILURE_URL)
    return redirect(settings.EMAIL_VERIFICATION_SUCCESS_URL)


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def login_view(request: Request) -> Response:
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    registered_user = User.objects.filter(Q(username=username) | Q(email__iexact=username)).first()
    if registered_user is not None and not registered_user.is_active and registered_user.check_password(password):
        return Response(
            {'detail': 'Verify your email before logging in.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    user = authenticate(username=username, password=password)

    if user is None:
        return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    token_pair = TokenService.issue_for_user(user)
    response = Response({'user': UserSerializer(user).data}, status=status.HTTP_200_OK)
    return CookieAuthMixin.set_auth_cookies(response, token_pair)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def me_profile(request: Request) -> Response:
    profile, _created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    serializer = ProfileSerializer(profile, data=request.data, partial=request.method == 'PATCH')
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me_posts(request: Request) -> Response:
    posts = Post.objects.select_related('profile', 'profile__user').prefetch_related('images', 'videos').filter(profile__user=request.user)
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


class MyTelegramLinkView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(telegram_link_service.get_status(request.user), status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        try:
            payload = telegram_link_service.request_link(request.user)
        except TelegramLinkAlreadyConfirmed:
            return Response({'detail': 'Telegram already linked.'}, status=status.HTTP_409_CONFLICT)
        return Response(payload, status=status.HTTP_200_OK)


class LinkTelegramConfirmView(APIView):
    permission_classes = [HasAPIKey]
    throttle_classes = [TelegramConfirmRateThrottle]

    def post(self, request: Request) -> Response:
        code = request.data.get('code')
        telegram_user_id = request.data.get('telegram_user_id')

        if not code or not telegram_user_id:
            return Response({'detail': 'Both code and telegram_user_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            link = telegram_link_service.confirm_link(code=code, telegram_user_id=telegram_user_id)
        except TelegramLinkNotFound:
            return Response({'detail': 'Invalid code.'}, status=status.HTTP_404_NOT_FOUND)
        except TelegramLinkExpired:
            return Response({'detail': 'Code has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Telegram linked successfully.'}, status=status.HTTP_200_OK)


class BotTelegramStatusView(APIView):
    permission_classes = [HasAPIKey]

    def get(self, request: Request) -> Response:
        telegram_user_id = request.query_params.get('telegram_user_id')
        if not telegram_user_id:
            return Response({'detail': 'telegram_user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        link = telegram_link_service.get_link_by_telegram_user_id(telegram_user_id)
        if link is None:
            return Response({'linked': False, 'status': 'not_linked'}, status=status.HTTP_200_OK)

        telegram_link_service.touch_interaction(telegram_user_id)
        return Response(
            {
                'linked': True,
                'status': 'linked',
                'user': UserSerializer(link.user).data,
            },
            status=status.HTTP_200_OK,
        )


class BotTrainingSessionsView(APIView):
    permission_classes = [HasAPIKey]

    def get(self, request: Request) -> Response:
        telegram_user_id = request.query_params.get('telegram_user_id')
        if not telegram_user_id:
            return Response({'detail': 'telegram_user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        link = telegram_link_service.get_link_by_telegram_user_id(telegram_user_id)
        if link is None:
            return Response({'detail': 'Telegram user is not linked.'}, status=status.HTTP_404_NOT_FOUND)

        telegram_link_service.touch_interaction(telegram_user_id)
        occurrences = training_reminder_service.get_upcoming_sessions_for_link(link)[:20]
        payload = [
            {
                'training_session_id': occurrence.training_session_id,
                'date': occurrence.starts_at.astimezone(occurrence.training_session.get_zoneinfo()).date().isoformat(),
                'time': occurrence.starts_at.astimezone(occurrence.training_session.get_zoneinfo()).strftime('%H:%M:%S'),
                'timezone': occurrence.training_session.timezone,
                'starts_at': occurrence.starts_at.isoformat(),
            }
            for occurrence in occurrences
        ]
        return Response(payload, status=status.HTTP_200_OK)


class BotNotificationsView(APIView):
    permission_classes = [HasAPIKey]

    def get(self, request: Request) -> Response:
        telegram_user_id = request.query_params.get('telegram_user_id')
        if not telegram_user_id:
            return Response({'detail': 'telegram_user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        link = telegram_link_service.get_link_by_telegram_user_id(telegram_user_id)
        if link is None:
            return Response({'detail': 'Telegram user is not linked.'}, status=status.HTTP_404_NOT_FOUND)

        notifications = (
            Notification.objects.filter(
                telegram_link=link,
                status=Notification.Status.PENDING,
                scheduled_for__gte=timezone.now(),
            )
            .select_related('occurrence', 'occurrence__training_session')
            .order_by('scheduled_for')[:20]
        )
        telegram_link_service.touch_interaction(telegram_user_id)
        payload = [
            {
                'id': notification.id,
                'scheduled_for': notification.scheduled_for.isoformat(),
                'status': notification.status,
                'kind': notification.kind,
            }
            for notification in notifications
        ]
        return Response(payload, status=status.HTTP_200_OK)
