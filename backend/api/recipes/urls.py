from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.recipes.views import TagViewSet, RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
]
