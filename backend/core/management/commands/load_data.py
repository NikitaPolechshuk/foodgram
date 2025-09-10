import csv
import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from recipes.models import Ingredient, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Загрузка данных из CSV файла в Базу Данных'

    def check_file_exist(self, file_path):
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден!')
            )
            return False
        return True

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default='data/',
            help='Base path to CSV files',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        base_path = Path(options['path'])
        self.load_ingredients(base_path / 'ingredients.csv')
        self.load_tags(base_path / 'tags.csv')

    def load_ingredients(self, file_path):
        """Загрузка ингридентов."""
        self.stdout.write(f'Loading ingredients from {file_path}...')

        if not self.check_file_exist(file_path):
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1],
                )
        self.stdout.write(self.style.SUCCESS('Ingredients loaded'))

    def load_tags(self, file_path):
        """Загрузка тэгов."""

        self.stdout.write(f'Loading tags from {file_path}...')

        if not self.check_file_exist(file_path):
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                Tag.objects.get_or_create(
                    name=row[0],
                    slug=row[1]
                )
        self.stdout.write(self.style.SUCCESS('Tags loaded'))
