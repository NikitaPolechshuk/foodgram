from api.users.serializers import UserSerializer
from api.utils import save_base64_image
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для рецептов (для избранного и корзины)."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""

    author = UserSerializer()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_list',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True
    )
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    image = serializers.CharField(write_only=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate(self, attrs):
        """Общая валидация для всех операций."""
        # Для запросов проверяем, что все обязательные поля присутствуют
        # image для PATCH может отсутствовать
        if self.context['request'].method in ['PATCH', 'PUT']:
            missing_fields = []

            if 'ingredients' not in attrs:
                missing_fields.append('ingredients')
            if 'tags' not in attrs:
                missing_fields.append('tags')
            if (self.context['request'].method != 'PATCH'
               and 'image' not in attrs):
                missing_fields.append('image')

            if missing_fields:
                raise serializers.ValidationError({
                    field: ['Это поле обязательно.']
                    for field in missing_fields
                })
        return attrs

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент'
            )

        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )

        for item in value:
            if 'id' not in item or 'amount' not in item:
                raise serializers.ValidationError(
                    'Каждый ингредиент должен содержать id и amount'
                )

            # ПРЕОБРАЗУЕМ amount В INT перед сравнением
            try:
                amount = int(item['amount'])
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть целым числом'
                )

            if amount < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть не менее 1'
                )

        # Проверяем что ингредиенты существуют
        existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids)
        if len(existing_ingredients) != len(ingredient_ids):
            raise serializers.ValidationError(
                'Один или несколько ингредиентов не существуют'
            )

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег'
            )

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Теги не должны повторяться'
            )

        existing_tags = Tag.objects.filter(id__in=value)
        if len(existing_tags) != len(value):
            raise serializers.ValidationError(
                'Один или несколько тегов не существуют'
            )

        return value

    def validate_image(self, value):
        # Базовая валидация base64 изображения
        if not value.startswith('data:image/'):
            raise serializers.ValidationError(
                'Неверный формат изображения. Ожидается base64 строка'
            )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        image_data = validated_data.pop('image')

        # Создаем рецепт БЕЗ передачи author здесь
        recipe = Recipe.objects.create(**validated_data)

        # Добавляем теги
        recipe.tags.set(tags_data)

        # Добавляем ингредиенты
        for ingredient_data in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )

        # Сохраняем изображение
        recipe.image = save_base64_image(image_data)
        recipe.save()

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        image_data = validated_data.pop('image', None)

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Обновляем изображение если предоставлено
        if image_data is not None:
            # Удаляем старое изображение если оно есть
            if instance.image:
                instance.image.delete(save=False)
            instance.image = save_base64_image(image_data)

        instance.save()

        # Обновляем теги если они предоставлены
        if tags_data is not None:
            instance.tags.set(tags_data)

        # Обновляем ингредиенты если они предоставлены
        if ingredients_data is not None:
            # Удаляем старые ингредиенты
            instance.ingredient_list.all().delete()

            # Добавляем новые ингредиенты
            for ingredient_data in ingredients_data:
                IngredientInRecipe.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )

        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data
