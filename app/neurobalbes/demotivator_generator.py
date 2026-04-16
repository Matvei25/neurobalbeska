# -*- coding: utf-8 -*-
"""
Генератор демотиваторов
"""

import os
import random
import logging
from PIL import Image

from app.simpledemotivators_2_0 import Demotivator


class DemotivatorGenerator:
    """Класс для генерации демотиваторов"""
    
    def __init__(self, watermark: str = ""):
        """
        Инициализация генератора демотиваторов
        
        Args:
            watermark: Водяной знак для демотиваторов
        """
        self.watermark = watermark
    
    async def create_demotivator(
        self,
        top_text: str,
        bottom_text: str,
        image_path: str,
        output_dir: str,
        style: int = None
    ):
        """
        Создаёт демотиватор
        
        Args:
            top_text: Текст сверху
            bottom_text: Текст снизу
            image_path: Путь к изображению
            output_dir: Директория для сохранения результата
            style: Стиль демотиватора (1 или 2), если None - выбирается случайно
            
        Returns:
            str: Путь к созданному демотиватору или None в случае ошибки
        """
        if not os.path.exists(image_path):
            logging.error(f"Изображение не найдено: {image_path}")
            return None
        
        # Проверяем изображение
        try:
            with Image.open(image_path) as img:
                img.load()
                logging.info(f"Image validated: {image_path}, size: {img.size}")
        except Exception as e:
            logging.error(f"Invalid image file: {e}")
            return None
        
        # Выбираем стиль
        if style is None:
            style = random.randint(1, 2)
        
        try:
            # Создаем демотиватор
            if style == 1:
                dem = Demotivator(top_text.lower(), bottom_text.lower())
            else:
                dem = Demotivator(top_text.lower(), "")
            
            # Генерируем имя файла результата
            result_prefix = f"result_{random.randint(0, 1000000000)}"
            input_filename = os.path.basename(image_path)
            
            # Создаем демотиватор
            await dem.create(
                folder_name=output_dir,
                avatar_name=input_filename,
                result_filename=result_prefix,
                watermark=self.watermark,
            )
            
            # Возвращаем путь к результату
            result_path = os.path.join(output_dir, f"{result_prefix}_dem.jpg")
            
            if os.path.exists(result_path):
                return result_path
            else:
                logging.error(f"Файл демотиватора не создан: {result_path}")
                return None
                
        except Exception as e:
            logging.error(f"Error creating demotivator: {e}", exc_info=True)
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
