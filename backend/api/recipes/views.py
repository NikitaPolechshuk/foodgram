from api.recipes.serializers import (IngredientSerializer,
                                     RecipeCreateUpdateSerializer,
                                     RecipeListSerializer,
                                     RecipeMinifiedSerializer, TagSerializer)
from api.utils import shopping_list

from django.http import HttpResponse
from django.shortcuts import redirect
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..filters import RecipeFilter
from ..permissions import RecipePermission


def recipe_short_link_redirect(request, short_link):
    """Редирект по короткой ссылке на страницу рецепта."""
    recipe = Recipe.objects.filter(short_link=short_link).first()
    if recipe:
        return redirect(f'/recipes/{recipe.id}')
    return redirect('/')


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с тегами.
    Только чтение, так как теги создаются через админку.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]  # Доступно всем
    pagination_class = None  # Отключаем пагинацию для тегов


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = [RecipePermission]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Применяем фильтры
        queryset = RecipeFilter.filter_recipes(queryset, self.request)

        return queryset.select_related('author').prefetch_related(
            'tags', 'ingredient_list__ingredient'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True,
            methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить рецепт в избранное."""
        recipe = self.get_object()
        user = request.user

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Favorite.objects.create(user=user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удалить рецепт из избранного."""
        recipe = self.get_object()
        user = request.user

        favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
        if not favorite:
            return Response(
                {'errors': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок."""
        recipe = self.get_object()
        user = request.user

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок."""
        recipe = self.get_object()
        user = request.user

        cart_item = ShoppingCart.objects.filter(user=user,
                                                recipe=recipe).first()
        if not cart_item:
            return Response(
                {'errors': 'Рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        content = shopping_list(request.user)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; ' \
                                          'filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'],
            permission_classes=[AllowAny], url_path='get-link')
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()

        # Проверяем что короткая ссылка существует
        if not recipe.short_link:
            return Response(
                {'error': 'Короткая ссылка для рецепта не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Формируем полную короткую ссылку
        base_url = request.build_absolute_uri('/')[:-1]
        short_link = f"{base_url}/s/{recipe.short_link}"

        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )
