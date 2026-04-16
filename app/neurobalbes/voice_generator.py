# -*- coding: utf-8 -*-
"""
Генератор голосовых сообщений
"""

import os
import random
from gtts import gTTS


class VoiceGenerator:
    """Класс для генерации голосовых сообщений"""
    
    def __init__(self, lang: str = "ru"):
        """
        Инициализация генератора голоса
        
        Args:
            lang: Язык для синтеза речи
        """
        self.lang = lang
    
    async def generate_voice(self, text: str, output_file: str = None):
        """
        Генерирует голосовое сообщение из текста
        
        Args:
            text: Текст для озвучивания
            output_file: Путь к файлу для сохранения (опционально)
            
        Returns:
            tuple: (путь к файлу, данные файла) или None в случае ошибки
        """
        if not text:
            return None
        
        if output_file is None:
            output_file = f"random_voice_{random.randint(0, 10000000000000000000000000)}.mp3"
        
        try:
            tts = gTTS(text=text, lang=self.lang)
            tts.save(output_file)
            
            # Читаем файл и возвращаем данные
            with open(output_file, "rb") as voice:
                voice_data = voice.read()
            
            return output_file, voice_data
            
        except Exception as e:
            print(f"Ошибка при создании голосового сообщения: {e}")
            # Очищаем файл если он был создан
            if os.path.exists(output_file):
                os.remove(output_file)
            return None
    
    @staticmethod
    def cleanup_file(filepath: str):
        """
        Удаляет временный файл с голосовым сообщением
        
        Args:
            filepath: Путь к файлу для удаления
        """
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Ошибка при удалении файла: {e}")
