from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (Tag, Ingredient, Recipe, IngredientInRecipe,
                     Favorite, ShoppingCart, )

User = get_user_model()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""

    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # автозаполнение slug
    ordering = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


class IngredientInRecipeInline(admin.TabularInline):
    """Inline для отображения ингредиентов в рецепте."""

    model = IngredientInRecipe
    extra = 1  # Количество пустых форм для добавления
    min_num = 1  # Минимальное количество ингредиентов


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'created',
        'short_link',
        'tags_display',
        'ingredients_count',
        'favorites_count',
    )
    list_display_links = ('name',)
    search_fields = ('name', 'author__username', 'text')
    list_filter = ('tags', 'created', 'cooking_time')
    filter_horizontal = ('tags',)
    readonly_fields = ('created',)
    inlines = [IngredientInRecipeInline]
    ordering = ('-created',)

    def tags_display(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    tags_display.short_description = 'Теги'

    def ingredients_count(self, obj):
        """Отображает количество ингредиентов."""
        return obj.ingredient_list.count()
    ingredients_count.short_description = 'Ингредиенты'

    def favorites_count(self, obj):
        """Отображает количество добавлений рецепта в избранное."""
        return obj.favorites.count()
    favorites_count.short_description = 'В избранном'


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Админка для связи ингредиентов и рецептов."""

    list_display = ('recipe', 'ingredient', 'amount')
    list_display_links = ('recipe',)
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient__measurement_unit',)
    ordering = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранных рецептов."""

    list_display = ('user', 'recipe', 'added')
    list_display_links = ('user',)
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added',)
    readonly_fields = ('added',)
    ordering = ('-added',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""

    list_display = ('user', 'recipe', 'added')
    list_display_links = ('user',)
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added',)
    readonly_fields = ('added',)
    ordering = ('-added',)
