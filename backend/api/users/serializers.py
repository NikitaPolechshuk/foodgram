import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from users.models import Subscription

User = get_user_model()


class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'avatar': {'required': False}
        }


class UserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(author=obj).exists()

    def get_avatar(self, obj):
        request = self.context.get('request')
        if not obj.avatar:
            return None
        return (request.build_absolute_uri(obj.avatar.url)
                if request else obj.avatar.url)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        """Проверяем, что это валидный base64"""
        if value and not value.startswith('data:image/'):
            raise serializers.ValidationError(
                'Неверный формат изображения. Ожидается base64 encoded image.')
        return value

    def update(self, instance, validated_data):
        avatar_data = validated_data.get('avatar')

        if avatar_data is None or avatar_data == '':
            # Удаляем аватарку
            if instance.avatar:
                instance.avatar.delete()
                instance.avatar = None
        else:
            # Создаем новую аватарку из base64
            format, imgstr = avatar_data.split(';base64,')
            ext = format.split('/')[-1]

            # Генерируем имя файла
            filename = f'avatar_{instance.id}.{ext}'

            # Декодируем и сохраняем
            data = ContentFile(base64.b64decode(imgstr), name=filename)
            instance.avatar = data

        instance.save()
        return instance

    def to_representation(self, instance):
        """Возвращаем только поле avatar в ответе."""
        request = self.context.get('request')
        avatar_url = None
        if instance.avatar:
            avatar_url = (request.build_absolute_uri(instance.avatar.url)
                          if request else instance.avatar.url)

        return {
            'avatar': avatar_url
        }


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для операций с подписками."""

    class Meta:
        model = Subscription
        fields = ('subscriber', 'author')
        read_only_fields = ('subscriber',)

    def validate(self, attrs):
        """Валидация данных подписки."""
        author = attrs.get('author')
        subscriber = self.context['request'].user

        # Нельзя подписаться на себя
        if subscriber == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')

        # Проверяем, не подписан ли уже
        if Subscription.objects.filter(subscriber=subscriber,
                                       author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.')

        attrs['subscriber'] = subscriber
        return attrs
