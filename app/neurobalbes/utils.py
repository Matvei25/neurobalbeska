# -*- coding: utf-8 -*-
"""
Вспомогательные функции для генераторов
"""

import os
import logging


def get_font(font_name, size):
    """
    Получает шрифт по имени и размеру, проверяя несколько возможных путей.
    
    Args:
        font_name (str): Имя файла шрифта
        size (int): Размер шрифта
        
    Returns:
        PIL.ImageFont: Объект шрифта или None в случае ошибки
    """
    from PIL import ImageFont
    
    # Список возможных путей к шрифтам в порядке приоритета
    font_paths = [
        os.path.join("app", "media", "fonts", font_name),
        os.path.join("media", "fonts", font_name),
        os.path.join("fonts", font_name),
        font_name,  # Попытка использовать имя шрифта напрямую
    ]
    
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    
    # Если ни один путь не подошел, пробуем использовать шрифт по умолчанию
    logging.warning(f"Шрифт {font_name} не найден, используется шрифт по умолчанию")
    try:
        return ImageFont.load_default()
    except:
        return None


def create_temp_directory(base_dir="temp"):
    """
    Создаёт временную директорию если она не существует
    
    Args:
        base_dir: Базовая директория для временных файлов
        
    Returns:
        str: Путь к созданной/существующей директории
    """
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    return base_dir


def cleanup_temp_files(filepaths: list):
    """
    Удаляет список временных файлов
    
    Args:
        filepaths: Список путей к файлам для удаления
    """
    for filepath in filepaths:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logging.error(f"Ошибка при удалении файла {filepath}: {e}")
