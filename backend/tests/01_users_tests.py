import pytest
from rest_framework import status
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestUserRegistration:
    """Тесты регистрации пользователей."""

    url = reverse('users-list')

    def test_successful_registration(self, api_client):
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123'
        }

        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED, (
            'Регистрация нового пользователя не удалась'
        )

    def test_registration_with_invalid_email(self, api_client):
        data = {
            'email': 'invalid-email',
            'username': 'invaliduser',
            'first_name': 'Invalid',
            'last_name': 'User',
            'password': 'testpass123'
        }

        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            'Регистрация с некорректным email должна возвращать ошибку 400'
        )


class TestUserAccess:
    """Тесты доступа к пользовательским данным."""

    def test_list_users_public_access(self, api_client, create_user):
        create_user(email='user1@example.com')
        url = reverse('users-list')

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK, (
            'Список пользователей должен быть доступен всем'
        )

    def test_retrieve_user_public_access(self, api_client, create_user):
        user = create_user(email='public@example.com')
        url = reverse('users-detail', kwargs={'pk': user.id})

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK, (
            'Профиль пользователя должен быть доступен всем'
        )

    def test_me_endpoint_requires_auth(self, api_client):
        url = reverse('users-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            'Эндпоинт /me/ должен требовать авторизацию'
        )

    def test_me_endpoint_authenticated(self, authenticated_client):
        client, user = authenticated_client
        url = reverse('users-me')

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK, (
            'Авторизованный пользователь должен иметь доступ к /me/'
        )


class TestPasswordChange:
    """Тесты смены пароля."""

    def test_password_change_success(self, authenticated_client):
        client, user = authenticated_client
        url = reverse('users-set-password')

        data = {
            'current_password': 'testpass123',
            'new_password': 'newsecurepass456'
        }

        response = client.post(url, data)
        assert response.status_code == status.HTTP_204_NO_CONTENT, (
            'Успешная смена пароля должна возвращать 204'
        )

    def test_password_change_with_wrong_current(self, authenticated_client):
        client, user = authenticated_client
        url = reverse('users-set-password')

        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpass123'
        }

        response = client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            'Смена пароля с неверным текущим паролем '
            'должна возвращать ошибку 400'
        )


class TestUserAvatar:
    """Тесты работы с аватаркой."""

    def test_upload_and_delete_avatar(self, authenticated_client, test_image):
        """Проверка загрузки и удаления аватарки."""
        url = reverse('user-avatar')
        client, user = authenticated_client
        data = {'avatar': test_image}

        # Добавляем аватарку
        response = client.put(url, data, format='multipart')
        assert response.status_code == status.HTTP_200_OK, (
            'Загрузка аватарки должна возвращать 200'
        )
        assert 'avatar' in response.data, (
            'Ответ должен содержать поле avatar'
        )
        assert response.data['avatar'] is not None, (
            'URL аватарки не должен быть пустым'
        )

        # Проверяем сохранение в БД
        user.refresh_from_db()
        assert user.avatar is not None, (
            'Аватарка должна сохраниться в базе данных'
        )
        assert user.avatar.name != '', (
            'Имя файла аватарки не должно быть пустым'
        )
        uploaded_avatar_name = user.avatar.name

        # Удаляем аватарку
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT, (
            'Удаление аватарки должно возвращать 204'
        )
        assert response.data['avatar'] is None, (
            'После удаления avatar должен быть null'
        )

        # Проверяем удаление из БД
        user.refresh_from_db()
        assert user.avatar.name == '' or user.avatar.name is None, (
            'Аватарка должна быть удалена из базы данных'
        )
        assert user.avatar.name != uploaded_avatar_name, (
            'Имя аватарки должно измениться после удаления'
        )


class TestSubscriptions:
    """Тесты работы с подписками."""

    def test_successful_subscription(self, authenticated_client, create_user):
        """Успешная подписка на пользователя."""
        client, subscriber = authenticated_client
        author = create_user(
            email='author@example.com',
            username='authoruser'
        )

        url = reverse('user-subscribe', kwargs={'pk': author.id})
        response = client.post(url)

        assert response.status_code == status.HTTP_201_CREATED, (
            'Подписка должна возвращать статус 201'
        )
        assert 'email' in response.data, (
            'Ответ должен содержать email автора'
        )
        assert response.data['email'] == author.email, (
            'Email в ответе должен совпадать с email автора'
        )

    def test_double_subscription_fails(self, authenticated_client,
                                       create_user):
        """Нельзя подписаться на одного пользователя дважды."""
        client, subscriber = authenticated_client
        author = create_user(
            email='author@example.com',
            username='authoruser'
        )

        url = reverse('user-subscribe', kwargs={'pk': author.id})

        # Первая подписка - должна быть успешной
        response1 = client.post(url)
        assert response1.status_code == status.HTTP_201_CREATED, (
            'Первая подписка должна быть успешной'
        )

        # Вторая подписка - должна вернуть ошибку
        response2 = client.post(url)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST, (
            'Повторная подписка должна возвращать ошибку 400'
        )
        assert 'errors' in response2.data or 'non_field_errors' in response2.data, (
            'Ответ должен содержать описание ошибки'
        )

    def test_self_subscription_fails(self, authenticated_client):
        """Нельзя подписаться на самого себя."""
        client, user = authenticated_client

        url = reverse('user-subscribe', kwargs={'pk': user.id})
        response = client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            'Подписка на самого себя должна возвращать ошибку 400'
        )
        assert 'errors' in response.data or 'non_field_errors' in response.data, (
            'Ответ должен содержать описание ошибки'
        )

    def test_unsubscribe_success(self, authenticated_client, create_user):
        """Успешная отписка от пользователя."""
        client, subscriber = authenticated_client
        author = create_user(
            email='author@example.com',
            username='authoruser'
        )

        # Сначала подписываемся
        url = reverse('user-subscribe', kwargs={'pk': author.id})
        response_subscribe = client.post(url)
        assert response_subscribe.status_code == status.HTTP_201_CREATED, (
            'Подписка должна быть успешной перед отпиской'
        )

        # Затем отписываемся (DELETE запрос на тот же URL)
        response_unsubscribe = client.delete(url)

        assert response_unsubscribe.status_code == status.HTTP_204_NO_CONTENT, (
            'Отписка должна возвращать статус 204'
        )

    def test_unsubscribe_without_subscription_fails(self, authenticated_client, create_user):
        """Отписка без предварительной подписки должна вернуть ошибку."""
        client, subscriber = authenticated_client
        author = create_user(
            email='author@example.com',
            username='authoruser'
        )

        url = reverse('user-subscribe', kwargs={'pk': author.id})
        response = client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            'Отписка без подписки должна возвращать ошибку 400'
        )
