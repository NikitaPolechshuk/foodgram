from rest_framework import permissions


class RecipePermission(permissions.BasePermission):
    """
    Права доступа для рецептов:
    - Чтение: все пользователи
    - Создание: авторизованные пользователи
    - Изменение/удаление: автор или администратор
    """

    def has_permission(self, request, view):
        # Разрешаем чтение всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем создание только авторизованным
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешаем чтение всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем изменение/удаление автору или администратору
        return obj.author == request.user or request.user.is_staff
