import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from recipes.models import Tag


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):

    User = get_user_model()

    def make_user(**kwargs):
        # Базовые данные
        user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
        # Обновляем переданными значениями
        user_data.update(kwargs)

        return User.objects.create_user(**user_data)
    return make_user


@pytest.fixture
def authenticated_client(api_client, create_user):
    user = create_user()
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def test_image():
    # PNG изображения размером 10x10 пикселей (красный квадрат на белом фоне).
    image_data = (
        'data:image/png;base64,'
        'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAGElEQVQYlWNkYGD4z4AE'
        '/jMwMDAxMDEwMgC1EwP0K8W5CAAAAABJRU5ErkJggg=='
    )
    return image_data


@pytest.fixture
def tag_breakfast():
    """Фикстура для тега 'Завтрак'."""
    return Tag.objects.create(
        name='Завтрак',
        slug='breakfast'
    )


@pytest.fixture
def tag_lunch():
    """Фикстура для тега 'Обед'."""
    return Tag.objects.create(
        name='Обед',
        slug='lunch'
    )


@pytest.fixture
def tag_dinner():
    """Фикстура для тега 'Ужин'."""
    return Tag.objects.create(
        name='Ужин',
        slug='dinner'
    )
