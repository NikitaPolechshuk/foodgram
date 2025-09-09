import base64
import os
import uuid

from django.conf import settings
from django.core.files.base import ContentFile

from foodgram.constants import RECIEP_IMG_DIR


def save_base64_image(base64_string):
    """Сохраняет base64 изображение в файл и возвращает путь к нему."""

    if not base64_string or not base64_string.startswith('data:image/'):
        return None

    try:
        # Извлекаем данные из base64 строки
        format, imgstr = base64_string.split(';base64,')
        ext = format.split('/')[-1]

        # Генерируем уникальное имя файла
        filename = f"{uuid.uuid4().hex}.{ext}"

        # Создаем путь для сохранения
        file_path = os.path.join(settings.MEDIA_ROOT, RECIEP_IMG_DIR, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Декодируем и сохраняем файл
        data = ContentFile(base64.b64decode(imgstr), name=filename)

        return data

    except (ValueError, AttributeError, TypeError) as e:
        raise ValueError(f"Ошибка обработки изображения: {str(e)}")
