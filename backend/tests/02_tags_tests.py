import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestTagsAPI:
    """Тесты для API тегов."""

    def test_get_tags_list(self, client, tag_breakfast, tag_lunch, tag_dinner):
        """Проверка получения списка тегов."""
        url = reverse('tags-list')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK, (
            'Статус код ответа должен быть 200 при получении списка тегов'
        )
        assert len(response.data) == 3, (
            'В ответе должно быть 3 тега, соответствующих количеству фикстур'
        )

        # Проверяем, что все теги присутствуют в ответе
        tag_names = [tag['name'] for tag in response.data]
        assert 'Завтрак' in tag_names, (
            'Тег "Завтрак" должен присутствовать в списке тегов'
        )
        assert 'Обед' in tag_names, (
            'Тег "Обед" должен присутствовать в списке тегов'
        )
        assert 'Ужин' in tag_names, (
            'Тег "Ужин" должен присутствовать в списке тегов'
        )

        # Проверяем структуру ответа
        for tag in response.data:
            assert 'id' in tag, (
                'Каждый тег в ответе должен содержать поле "id"'
            )
            assert 'name' in tag, (
                'Каждый тег в ответе должен содержать поле "name"'
            )
            assert 'slug' in tag, (
                'Каждый тег в ответе должен содержать поле "slug"'
            )

    def test_get_single_tag(self, client, tag_breakfast):
        """Проверка получения одного тега по ID."""
        url = reverse('tags-detail', kwargs={'pk': tag_breakfast.id})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK, (
            'Статус код ответа должен быть 200 при получении тега по ID'
        )
        assert response.data['id'] == tag_breakfast.id, (
            'ID тега в ответе должен соответствовать ID запрошенного тега'
        )
        assert response.data['name'] == tag_breakfast.name, (
            'Название тега в ответе должно соответствовать '
            'названию запрошенного тега'
        )
        assert response.data['slug'] == tag_breakfast.slug, (
            'Слаг тега в ответе должен соответствовать слагу запрошенного тега'
        )

    def test_tags_method_not_allowed(self, client, tag_breakfast):
        """Проверка, что API принимает только GET запросы."""
        url_list = reverse('tags-list')
        url_detail = reverse('tags-detail', kwargs={'pk': tag_breakfast.id})

        # Тестируем методы для списка тегов
        response = client.post(url_list, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, (
            'POST запрос к списку тегов должен возвращать 405'
        )

        response = client.put(url_list, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, (
            'PUT запрос к списку тегов должен возвращать 405'
        )

        response = client.patch(url_list, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, (
            'PATCH запрос к списку тегов должен возвращать 405'
        )

        response = client.delete(url_list)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, (
            'DELETE запрос к списку тегов должен возвращать 405'
        )

        # Тестируем методы для детального просмотра тега
        response = client.post(url_detail, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, (
            'POST запрос к детальному view тега должен возвращать 405'
        )

        response = client.put(url_detail, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, (
            'PUT запрос к детальному view тега должен возвращать 405'
        )

        response = client.patch(url_detail, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, (
            'PATCH запрос к детальному view тега должен возвращать 405'
        )

        response = client.delete(url_detail)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, (
            'DELETE запрос к детальному view тега должен возвращать 405'
        )
