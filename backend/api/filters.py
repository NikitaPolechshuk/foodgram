from django.db.models import QuerySet


class RecipeFilter:
    """Класс для фильтрации рецептов."""

    @staticmethod
    def filter_recipes(queryset: QuerySet, request) -> QuerySet:
        """Фильтры к queryset рецептов."""
        # Фильтрация по автору
        author_id = request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        # Фильтрация по избранному
        is_favorited = request.query_params.get('is_favorited')
        if is_favorited == '1' and request.user.is_authenticated:
            queryset = queryset.filter(favorites__user=request.user)

        # Фильтрация по списку покупок
        is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1' and request.user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=request.user)

        # Фильтрация по тегам
        tags = request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        return queryset
