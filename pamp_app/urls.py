from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'profiles', views.ProfileViewSet, basename='profile')
router.register(r'posts', views.PostViewSet, basename='posts')
router.register(r'training-sessions', views.TrainingSessionViewSet, basename='training-session')

urlpatterns = [
    path('csrf/', views.csrf_cookie, name='csrf-cookie'),
    path('me/', views.me_profile, name='me-profile'),
    path('me/posts/', views.me_posts, name='me-posts'),
    path('me/training-sessions/', views.MyTrainingSessionsView.as_view(), name='me-training-sessions'),
    path('me/telegram-link/', views.MyTelegramLinkView.as_view(), name='me-telegram-link'),
    path('bot/telegram-link/confirm/', views.LinkTelegramConfirmView.as_view(), name='telegram-link-confirm'),
    path('bot/me/', views.BotTelegramStatusView.as_view(), name='bot-telegram-status'),
    path('bot/training-sessions/upcoming/', views.BotTrainingSessionsView.as_view(), name='bot-training-sessions'),
    path('bot/notifications/upcoming/', views.BotNotificationsView.as_view(), name='bot-notifications'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('auth/session/refresh/', views.RefreshSessionView.as_view(), name='auth-session-refresh'),
    path('auth/session/logout/', views.LogoutView.as_view(), name='auth-session-logout'),
]

urlpatterns += router.urls
