from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify

import foodgram.constants as constants

User = get_user_model()


class Tag(models.Model):
    """Модель тега рецепта."""

    name = models.CharField(
        'Название',
        max_length=constants.NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=constants.SLUG_MAX_LENGTH,
        unique=True,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название',
        max_length=constants.NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=constants.MEASURE_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта с короткой ссылкой."""

    name = models.CharField(
        'Название',
        max_length=constants.NAME_MAX_LENGTH
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    text = models.TextField(
        'Описание'
    )
    image = models.ImageField(
        'Изображение',
        upload_to=constants.RECIEP_IMG_DIR
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (минуты)',
        validators=[MinValueValidator(1)]
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    short_link = models.CharField(
        'Короткая ссылка',
        max_length=10,
        unique=True,
        blank=True,
        help_text='Уникальная короткая ссылка для рецепта'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Генерация короткой ссылки при создании рецепта."""
        if not self.short_link:
            self.short_link = self._generate_short_link()
        super().save(*args, **kwargs)

    def _generate_short_link(self):
        """Генерация уникальной короткой ссылки."""
        while True:
            # Генерируем случайную строку из 6 символов
            short_link = get_random_string(6)
            # Проверяем уникальность
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link


class IngredientInRecipe(models.Model):
    """Промежуточная модель для связи ингредиентов и рецептов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient.name} в {self.recipe.name}'


class Favorite(models.Model):
    """Модель для избранных рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    added = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель для списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    added = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
