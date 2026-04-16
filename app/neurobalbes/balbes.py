# -*- coding: utf-8 -*-
"""
Нейробалбес - основной класс для генерации контента

Пример использования:
    from neurobalbes import Balbes
    
    balbes = Balbes(texts=["текст1", "текст2"], pictures=["pic1", "pic2"])
    
    # Генерация текста
    text = await balbes.text.generate_phrase()
    
    # Генерация мема
    meme_path = await balbes.meme.create_text_meme("текст", 1)
    
    # Генерация голосового сообщения
    voice_path, voice_data = await balbes.voice.generate_voice("текст")
    
    # Генерация демотиватора
    demo_path = await balbes.demotivator.create_demotivator(...)
"""

from .text_generator import TextGenerator
from .voice_generator import VoiceGenerator
from .meme_generator import MemeGenerator
from .demotivator_generator import DemotivatorGenerator


class Balbes:
    """
    Основной класс Нейробалбеса для генерации контента
    
    Атрибуты:
        text: Генератор текста
        voice: Генератор голосовых сообщений
        meme: Генератор мемов
        demotivator: Генератор демотиваторов
    """
    
    def __init__(
        self,
        texts: list = None,
        pictures: list = None,
        watermark: str = "",
        voice_lang: str = "ru"
    ):
        """
        Инициализация Нейробалбеса
        
        Args:
            texts: Список текстов для обучения (сообщения из чата)
            pictures: Список идентификаторов картинок (опционально)
            watermark: Водяной знак для демотиваторов
            voice_lang: Язык для синтеза речи
        """
        self.texts = texts or []
        self.pictures = pictures or []
        self.watermark = watermark
        
        # Инициализация генераторов
        self.text = TextGenerator(self.texts)
        self.voice = VoiceGenerator(lang=voice_lang)
        self.meme = MemeGenerator()
        self.demotivator = DemotivatorGenerator(watermark=self.watermark)
    
    def update_texts(self, texts: list):
        """
        Обновляет базу текстов и пересоздаёт текстовый генератор
        
        Args:
            texts: Новый список текстов
        """
        self.texts = texts
        self.text = TextGenerator(self.texts)
    
    def update_pictures(self, pictures: list):
        """
        Обновляет базу картинок
        
        Args:
            pictures: Новый список идентификаторов картинок
        """
        self.pictures = pictures
    
    @property
    def is_ready(self):
        """
        Проверяет готовность к генерации
        
        Returns:
            bool: True если достаточно данных для генерации
        """
        return len(self.texts) >= 1
    
    @property
    def can_generate_memes(self):
        """
        Проверяет возможность генерации мемов
        
        Returns:
            bool: True если достаточно текстов и картинок
        """
        return len(self.texts) >= 10 and len(self.pictures) >= 1
    
    @property
    def can_generate_demotivators(self):
        """
        Проверяет возможность генерации демотиваторов
        
        Returns:
            bool: True если достаточно текстов и картинок
        """
        return len(self.texts) >= 10 and len(self.pictures) >= 1
