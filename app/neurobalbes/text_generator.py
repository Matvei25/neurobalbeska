# -*- coding: utf-8 -*-
"""
Генератор текста на основе Markov chains
"""

import random
import sys
import os

# Добавляем корневую директорию в путь если нужно
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.mc import mc
from app.mc.builtin import validators
from app.mc.builtin.formatters import usual_syntax


class TextGenerator:
    """Класс для генерации различных типов текста"""
    
    def __init__(self, texts: list):
        """
        Инициализация генератора текста
        
        Args:
            texts: Список текстов для обучения
        """
        self.texts = texts
        self.generator = None
        if texts and len(texts) >= 1:
            self.generator = mc.PhraseGenerator(samples=texts)
    
    async def generate_phrase(self, min_words: int = 1, max_words: int = None):
        """
        Генерирует случайную фразу
        
        Args:
            min_words: Минимальное количество слов
            max_words: Максимальное количество слов
            
        Returns:
            str: Сгенерированная фраза или None если недостаточно данных
        """
        if not self.generator:
            return None
        
        validators_list = [validators.words_count(minimal=min_words)]
        if max_words:
            validators_list = [validators.words_count(minimal=min_words, maximal=max_words)]
        
        return await self.generator.generate_phrase(validators=validators_list)
    
    async def generate_dialogue(self, parts_count: int = 3):
        """
        Генерирует диалог из нескольких реплик
        
        Args:
            parts_count: Количество реплик в диалоге
            
        Returns:
            str: Диалог или None если недостаточно данных
        """
        if not self.generator or len(self.texts) < 4:
            return None
        
        parts = []
        for _ in range(parts_count):
            phrase = await self.generator.generate_phrase(
                validators=[validators.words_count(minimal=1)]
            )
            if phrase:
                parts.append(phrase)
        
        if parts:
            return "\n— ".join(parts)
        return None
    
    async def generate_with_syntax(self, min_words: int = 1):
        """
        Генерирует фразу с правильным синтаксисом
        
        Args:
            min_words: Минимальное количество слов
            
        Returns:
            str: Сгенерированная фраза или None если недостаточно данных
        """
        if not self.generator:
            return None
        
        return await self.generator.generate_phrase(
            validators=[validators.words_count(minimal=min_words)],
            formatters=[usual_syntax],
        )
    
    async def generate_anekdote(self, templates: list = None):
        """
        Генерирует анекдот по шаблону
        
        Args:
            templates: Список шаблонов анекдотов
            
        Returns:
            str: Анекдот или None если недостаточно данных
        """
        if not self.generator:
            return None
        
        if templates is None:
            templates = [
                ["Штирлиц шел по лесу, вдруг ему за пазуху упала гусеница.\n«{}», подумал Штирлиц."],
                ["Шел медведь по лесу\nСел в машину и — {}"],
                ["Ебутся два клоуна, а один другому говорит: — «{}»"],
                ["Заходит как-то улитка в бар\nА Бармен ей отвечает\nМы улиток не обслуживаем\nИ выпинывает ее за дверь\nЧерез неделю поиходит улитка\nИ говорит: «{}»"],
                ["— Извините, а у вас огоньку не найдется?\n— «{}» - ответил медведь из машины"]
            ]
        
        template = random.choice(templates)
        phrase = await self.generator.generate_phrase(
            validators=[validators.words_count(minimal=1)]
        )
        
        if phrase:
            return template[0].format(phrase)
        return None
    
    async def continue_sentence(self, prefix: str = ""):
        """
        Продолжает предложение
        
        Args:
            prefix: Начальная часть предложения
            
        Returns:
            str: Продолжение предложения или None если недостаточно данных
        """
        if not self.generator:
            return None
        
        # Генерируем продолжение
        continuation = await self.generator.generate_phrase(
            validators=[validators.words_count(minimal=1)]
        )
        
        if continuation:
            if prefix:
                return f"{prefix} {continuation}"
            return continuation
        return None
    
    async def generate_poem_line(self):
        """
        Генерирует строку для стихотворения
        
        Returns:
            str: Строка стихотворения или None если недостаточно данных
        """
        return await self.generate_phrase(min_words=3, max_words=8)
    
    async def generate_poll_question(self):
        """
        Генерирует вопрос для опроса
        
        Returns:
            str: Вопрос для опроса или None если недостаточно данных
        """
        return await self.generate_phrase(min_words=2, max_words=10)
    
    async def generate_poll_options(self, count: int = 2):
        """
        Генерирует варианты ответов для опроса
        
        Args:
            count: Количество вариантов ответов
            
        Returns:
            list: Список вариантов ответов или None если недостаточно данных
        """
        if not self.generator or len(self.texts) < count:
            return None
        
        options = []
        for _ in range(count):
            option = await self.generator.generate_phrase(
                validators=[validators.words_count(minimal=1, maximal=5)]
            )
            if option:
                options.append(option)
        
        return options if len(options) == count else None
