from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from api.users.serializers import (
    UserSerializer,
    UserCreateSerializer,
    AvatarSerializer,
    SubscriptionSerializer,)
from api.recipes.serializers import RecipeMinifiedSerializer
from users.models import Subscription
from recipes.models import Recipe

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователям."""

    pagination_class = LimitOffsetPagination
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        # Регистрация доступна всем
        if self.action == 'create':
            return [permissions.AllowAny()]

        # Просмотр конкретного пользователя доступен всем
        if self.action == 'retrieve':  # Эндпоинт /api/users/{id}/
            return [permissions.AllowAny()]

        # Просмотр списка пользователей доступен всем
        if self.action == 'list':  # Эндпоинт /api/users/
            return [permissions.AllowAny()]

        # Все остальные действия только авторизованным
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(
            serializer.validated_data['new_password'])
        self.request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put'],
            permission_classes=[permissions.IsAuthenticated])
    def put_avatar(self, request):
        """Обновление или установка аватарки."""
        # Проверяем наличие поля avatar в запросе
        if 'avatar' not in request.data:
            return Response(
                {'avatar': ['Это поле обязательно.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'],
            permission_classes=[permissions.IsAuthenticated])
    def delete_avatar(self, request):
        """Удаление аватарки."""
        serializer = AvatarSerializer(
            request.user,
            data={'avatar': None},
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с подписками."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Возвращает queryset пользователей,
        на которых подписан текущий пользователь.
        """
        return User.objects.filter(
            subscribers__subscriber=self.request.user
        ).prefetch_related('subscribers', 'subscriptions')

    def list(self, request):
        """Список моих подписок. GET /api/users/subscriptions/"""
        # Получаем пагинированный queryset
        page = self.paginate_queryset(self.get_queryset())

        if page is not None:
            users_with_recipes = []
            for user in page:
                user_data = UserSerializer(user,
                                           context={'request': request}).data
                user_data['recipes'] = self.get_user_recipes(user, request)
                user_data['recipes_count'] = self.get_user_recipes_count(user)
                users_with_recipes.append(user_data)

            return self.get_paginated_response(users_with_recipes)

        return Response(users_with_recipes)

    def manage_subscription(self, request, pk=None):
        """Управление подпиской: POST - подписаться, DELETE - отписаться."""
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            return self._subscribe(request, author)
        elif request.method == 'DELETE':
            return self._unsubscribe(request, author)

    def _subscribe(self, request, author):
        """Подписаться на пользователя."""
        serializer = SubscriptionSerializer(
            data={'author': author.id},
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            author_data = UserSerializer(
                author,
                context={'request': request}
            ).data
            author_data['recipes'] = self.get_user_recipes(author, request)
            author_data['recipes_count'] = self.get_user_recipes_count(author)
            return Response(author_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _unsubscribe(self, request, author):
        """Отписаться от пользователя."""
        try:
            subscription = Subscription.objects.get(
                subscriber=request.user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_user_recipes(self, user, request):
        # Получаем параметр recipes_limit из запроса
        recipes_limit = request.query_params.get('recipes_limit')

        # Получаем рецепты пользователя
        recipes = Recipe.objects.filter(author=user)

        # Если передан limit, применяем его
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        # Сериализуем рецепты
        serializer = RecipeMinifiedSerializer(
            recipes,
            many=True,
            context={'request': request}
        )
        return serializer.data

    def get_user_recipes_count(self, user):
        """Количество рецептов пользователя."""
        return Recipe.objects.filter(author=user).count()
