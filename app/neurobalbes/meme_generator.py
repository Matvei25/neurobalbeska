# -*- coding: utf-8 -*-
"""
Генератор мемов
"""

import os
import random
import logging
from PIL import Image, ImageDraw

from .utils import get_font


class MemeGenerator:
    """Класс для генерации мемов"""
    
    def __init__(self, templates_dir: str = "app/media/images"):
        """
        Инициализация генератора мемов
        
        Args:
            templates_dir: Директория с шаблонами мемов
        """
        self.templates_dir = templates_dir
    
    async def create_text_meme(
        self,
        text: str,
        meme_type: int,
        output_file: str = None
    ):
        """
        Создаёт мем с текстом на шаблоне
        
        Args:
            text: Текст для мема
            meme_type: Тип шаблона (1-10)
            output_file: Путь для сохранения результата
            
        Returns:
            str: Путь к созданному мему или None в случае ошибки
        """
        if output_file is None:
            output_file = f"meme_{random.randint(0, 1000000000)}.jpg"
        
        template_path = os.path.join(self.templates_dir, f"{meme_type}.jpg")
        
        if not os.path.exists(template_path):
            logging.error(f"Шаблон не найден: {template_path}")
            return None
        
        try:
            photo = Image.open(template_path)
            font = get_font("arialbd.ttf", size=30)
            draw = ImageDraw.Draw(photo)
            
            # Позиционирование текста в зависимости от шаблона
            positions = {
                1: (90, 5),
                2: (50, 200),
                3: (50, 50),
                4: (50, 100),
                5: (50, 150),
                6: (50, 200),
                7: (50, 250),
                8: (50, 300),
                9: (50, 350),
                10: (50, 400),
            }
            
            position = positions.get(meme_type, (50, 50))
            draw.text(position, text.lower(), font=font, fill="black")
            
            photo.save(output_file)
            return output_file
            
        except Exception as e:
            logging.error(f"Ошибка при создании мема: {e}")
            return None
    
    async def create_image_meme(
        self,
        user_image_path: str,
        meme_type: int,
        output_file: str = None
    ):
        """
        Создаёт мем с изображением пользователя на шаблоне
        
        Args:
            user_image_path: Путь к изображению пользователя
            meme_type: Тип шаблона (11-24)
            output_file: Путь для сохранения результата
            
        Returns:
            str: Путь к созданному мему или None в случае ошибки
        """
        if output_file is None:
            output_file = f"meme_{random.randint(0, 1000000000)}.jpg"
        
        # Шаблон для мема с изображением (тип - 10)
        template_type = meme_type - 10
        template_path = os.path.join(self.templates_dir, f"{template_type}.jpg")
        
        if not os.path.exists(template_path):
            logging.error(f"Шаблон не найден: {template_path}")
            return None
        
        if not os.path.exists(user_image_path):
            logging.error(f"Изображение пользователя не найдено: {user_image_path}")
            return None
        
        try:
            # Открываем шаблон
            template = Image.open(template_path)
            
            # Открываем и обрабатываем изображение пользователя
            user_img = Image.open(user_image_path).convert("RGBA")
            
            # Размеры и позиции зависят от шаблона
            sizes = {
                1: (400, 300),
                2: (300, 300),
                3: (350, 350),
                4: (400, 400),
            }
            
            positions = {
                1: (0, 0),
                2: (50, 50),
                3: (25, 25),
                4: (0, 50),
            }
            
            size = sizes.get(template_type, (400, 300))
            position = positions.get(template_type, (0, 0))
            
            # Изменяем размер изображения пользователя
            user_img = user_img.resize(size)
            
            # Вставляем изображение пользователя в шаблон
            template.paste(user_img, position)
            
            template.save(output_file)
            return output_file
            
        except Exception as e:
            logging.error(f"Ошибка при создании мема с изображением: {e}")
            return None
    
    @staticmethod
    def cleanup_files(filepaths: list):
        """
        Удаляет временные файлы
        
        Args:
            filepaths: Список путей к файлам для удаления
        """
        for filepath in filepaths:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logging.error(f"Ошибка при удалении файла {filepath}: {e}")
