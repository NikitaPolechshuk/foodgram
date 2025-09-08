from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum, F

from recipes.models import Recipe, Ingredient, Tag, Favorite, ShoppingCart
from api.recipes.serializers import (
    RecipeListSerializer, RecipeCreateUpdateSerializer,
    IngredientSerializer, TagSerializer, RecipeMinifiedSerializer
)
from ..permissions import RecipePermission
from ..filters import RecipeFilter


def recipe_short_link_redirect(request, short_link):
    """Редирект по короткой ссылке на страницу рецепта."""

    try:
        recipe = get_object_or_404(Recipe, short_link=short_link)
        # Перенаправляем на страницу рецепта в API
        return redirect(f'/recipes/{recipe.id}')
    except Http404:
        print("Recipe not found, redirecting to home")
        return redirect('/')


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с тегами.
    Только чтение, так как теги создаются через админку.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]  # Доступно всем
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
        shopping_data = ShoppingCart.objects.filter(
            user=request.user
        ).values(
            name=F('recipe__ingredient_list__ingredient__name'),
            unit=F('recipe__ingredient_list__ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('recipe__ingredient_list__amount')
        ).order_by('name')

        # Создаем текстовый файл
        content = "Список покупок:\n\n"
        for item in shopping_data:
            content += f"{item['name']} - {item['total_amount']} "
            content += f"{item['unit']}\n"

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
