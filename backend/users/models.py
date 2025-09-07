from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

import foodgram.constants as constants


class CustomUser(AbstractUser):
    """Кастомная модель пользователя с аватаркой."""

    email = models.EmailField(
        'email address',
        unique=True,
        max_length=254,
        validators=[validate_email],
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
        }
    )

    first_name = models.CharField(
        'Имя',
        max_length=constants.USER_NAME_MAX_LENGTH,
        blank=False)
    last_name = models.CharField(
        'Фамилия',
        max_length=constants.USER_NAME_MAX_LENGTH,
        blank=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    avatar = models.ImageField(
        upload_to=constants.AVATARS_DIR,
        blank=True,
        null=True,
        verbose_name='Аватарка',
        help_text='Загрузите изображение для аватара'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']
        indexes = [  # Добавляем индексы
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def clean(self):
        """Валидация и нормализация email."""
        super().clean()
        self.email = self.email.strip().lower()

    def save(self, *args, **kwargs):
        """Выполняем проверки перед сохранением."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для подписок на пользователей."""

    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )
    created = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscription'
            )
        ]
        indexes = [  # Добавляем индексы для часто используемых запросов
            models.Index(fields=['subscriber', 'author']),
            models.Index(fields=['subscriber']),
            models.Index(fields=['author']),
            models.Index(fields=['created']),
        ]

    def clean(self):
        """Проверка, что пользователь не пытается подписаться на себя."""
        super().clean()

        if self.subscriber == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def save(self, *args, **kwargs):
        """Выполняем проверки перед сохранением."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.subscriber.username} подписан на {self.author.username}'
