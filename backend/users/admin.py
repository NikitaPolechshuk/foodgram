from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Админка для кастомной модели пользователя."""

    list_display = ('id',
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'is_staff',
                    'is_active',
                    'avatar',
                    'recipes_count',
                    'favorites_count',
                    'subscriptions_count',
                    'subscribers_count')

    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # Добавляем avatar в fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Аватар', {'fields': ('avatar',)}),
    )

    # Поля для создания пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name',
                       'password1', 'password2', 'avatar'),
        }),
    )

    def recipes_count(self, obj):
        """Количество рецептов пользователя."""
        return obj.recipes.count()
    recipes_count.short_description = 'Рецепты'

    def favorites_count(self, obj):
        """Количество избранных рецептов."""
        return obj.favorites.count()
    favorites_count.short_description = 'Избранное'

    def subscriptions_count(self, obj):
        """Количество подписок пользователя (на кого подписан)."""
        return obj.subscriptions.count()
    subscriptions_count.short_description = 'Подписки'

    def subscribers_count(self, obj):
        """Количество подписчиков пользователя (кто подписан на него)."""
        return obj.subscribers.count()
    subscribers_count.short_description = 'Подписчики'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для модели подписок."""

    list_display = (
        'id',
        'subscriber_username',
        'author_username',
        'created'
    )

    list_display_links = ('id', 'subscriber_username')
    list_filter = ('created',)
    search_fields = (
        'subscriber__username',
        'subscriber__email',
        'author__username',
        'author__email',
    )
    readonly_fields = ('created',)
    date_hierarchy = 'created'

    def subscriber_username(self, obj):
        return obj.subscriber.username
    subscriber_username.short_description = 'Подписчик'

    def author_username(self, obj):
        return obj.author.username
    author_username.short_description = 'Автор'
