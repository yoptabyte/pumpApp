from __future__ import annotations

from typing import cast

from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialApp, SocialLogin, SocialToken
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Post, PostImage, PostVideo, Profile, TrainingSession
from .services import PostMediaService, PostMediaValidationError



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label='Confirm password')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})

        username = cast(str, attrs.get('username'))
        email = cast(str, attrs.get('email'))

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'A user with this username already exists.'})

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})

        return attrs

    def create(self, validated_data: dict[str, object]) -> User:
        return User.objects.create_user(
            username=cast(str, validated_data['username']),
            email=cast(str, validated_data['email']),
            password=cast(str, validated_data['password']),
            is_active=False,
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'username', 'avatar']

    def update(self, instance: Profile, validated_data: dict[str, object]) -> Profile:
        if 'avatar' in validated_data:
            avatar = validated_data['avatar']
            if instance.avatar and (not avatar or avatar != instance.avatar):
                instance.avatar.delete(save=False)
            instance.avatar = cast(object | None, avatar) or None
        instance.save(update_fields=['avatar'] if 'avatar' in validated_data else None)
        return instance


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'image_url']

    def validate(self, data: dict[str, object]) -> dict[str, object]:
        if not data.get('image') and not data.get('image_url'):
            raise serializers.ValidationError('Either image file or image URL must be provided.')
        return data


class PostVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVideo
        fields = ['id', 'video', 'video_url']

    def validate(self, data: dict[str, object]) -> dict[str, object]:
        if not data.get('video') and not data.get('video_url'):
            raise serializers.ValidationError('Either video file or video URL must be provided.')
        return data


class TrainingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingSession
        fields = ['id', 'date', 'time', 'timezone', 'recurrence', 'days_of_week', 'profile']
        read_only_fields = ('profile',)


class PostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)
    videos = PostVideoSerializer(many=True, read_only=True)
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'images',
            'videos',
            'training_type',
            'description',
            'views',
            'created_at',
            'updated_at',
            'profile',
        ]
        read_only_fields = ['views', 'created_at', 'updated_at', 'profile']

    def create(self, validated_data: dict[str, object]) -> Post:
        request = self.context['request']
        profile = cast(Profile, validated_data.pop('profile'))
        post = Post.objects.create(profile=profile, **validated_data)
        try:
            PostMediaService.sync(post, request)
        except PostMediaValidationError as exc:
            raise serializers.ValidationError({'media': str(exc)}) from exc
        return post

    def update(self, instance: Post, validated_data: dict[str, object]) -> Post:
        request = self.context['request']
        instance.title = cast(str, validated_data.get('title', instance.title))
        instance.training_type = cast(str, validated_data.get('training_type', instance.training_type))
        instance.description = cast(str, validated_data.get('description', instance.description))
        instance.save()
        try:
            PostMediaService.sync(instance, request)
        except PostMediaValidationError as exc:
            raise serializers.ValidationError({'media': str(exc)}) from exc
        return instance

    def to_representation(self, instance: Post) -> dict[str, object]:
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.is_authenticated and instance.profile.user_id == request.user.id:
            representation.pop('profile', None)
        return representation


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True, allow_blank=False)

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        request = self.context['request']
        id_token = cast(str, attrs.get('id_token'))
        adapter = GoogleOAuth2Adapter(request)

        try:
            app = SocialApp.objects.get(provider=adapter.provider_id)
        except SocialApp.DoesNotExist as exc:
            raise serializers.ValidationError('SocialApp for Google provider is not configured.') from exc

        token = SocialToken(app=app, token=id_token)

        try:
            login = adapter.complete_login(request, app, token, response={'id_token': id_token})
            login.token = token
            login.state = SocialLogin.state_from_request(request)
            complete_social_login(request, login)
            if not login.user.pk:
                login.user.save()
            if not login.is_existing:
                login.save(request, connect=True)
        except Exception as exc:
            raise serializers.ValidationError({'detail': 'Failed to login with Google.'}) from exc

        attrs['user'] = login.user
        return attrs
