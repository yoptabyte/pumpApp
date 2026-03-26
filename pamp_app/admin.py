from django.contrib import admin
from .models import Notification, Post, Profile, TelegramLink, TelegramLinkToken, TrainingSession, TrainingSessionOccurrence

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'avatar']
    list_filter = ['user']
    search_fields = ['user__username']
    raw_id_fields = ['user']
    ordering = ['user']
    show_facets = admin.ShowFacets.ALWAYS

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['profile', 'title','training_type','description','created_at', 'views']
    list_filter = ['training_type', 'created_at']
    search_fields = ['title', 'description', 'profile__user__username']
    raw_id_fields = ['profile']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    show_facets = admin.ShowFacets.ALWAYS


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['profile', 'date', 'time', 'timezone', 'recurrence']
    list_filter = ['recurrence', 'timezone']
    search_fields = ['profile__user__username']
    raw_id_fields = ['profile']
    ordering = ['date', 'time']


@admin.register(TelegramLink)
class TelegramLinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'telegram_user_id', 'is_active', 'linked_at', 'last_interaction_at']
    list_filter = ['is_active']
    search_fields = ['user__username', 'user__email', 'telegram_user_id']
    raw_id_fields = ['user']


@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'expires_at', 'used_at', 'created_at']
    list_filter = ['expires_at', 'used_at']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
    ordering = ['-created_at']


@admin.register(TrainingSessionOccurrence)
class TrainingSessionOccurrenceAdmin(admin.ModelAdmin):
    list_display = ['training_session', 'source_date', 'starts_at', 'created_at']
    search_fields = ['training_session__profile__user__username']
    raw_id_fields = ['training_session']
    ordering = ['starts_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['telegram_link', 'kind', 'status', 'scheduled_for', 'sent_at']
    list_filter = ['status', 'kind', 'channel']
    search_fields = ['telegram_link__user__username', 'telegram_link__telegram_user_id']
    raw_id_fields = ['telegram_link', 'occurrence']
    ordering = ['scheduled_for']
