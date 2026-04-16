#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример использования модуля Нейробалбес
"""

import asyncio
import sys
import os

# Добавляем корневую директорию в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from neurobalbes import Balbes


async def main():
    # Пример текстов из чата
    texts = [
        "привет как дела",
        "нормально а у тебя",
        "тоже норм",
        "что делаешь",
        "сижу работаю",
        "а я отдыхаю",
        "круто",
        "да нормально",
        "пойдём гулять",
        "не могу занят",
    ]
    
    # Создаём экземпляр Нейробалбеса
    balbes = Balbes(texts=texts, watermark="@neurobalbes")
    
    print("=== Тестирование Нейробалбес ===\n")
    
    # Проверяем готовность
    print(f"Готов к работе: {balbes.is_ready}")
    print(f"Может генерировать мемы: {balbes.can_generate_memes}")
    print(f"Может генерировать демотиваторы: {balbes.can_generate_demotivators}")
    print()
    
    # Генерация текста
    print("--- Генерация текста ---")
    text = await balbes.text.generate_phrase(min_words=2)
    print(f"Сгенерированная фраза: {text}")
    print()
    
    # Генерация диалога
    print("--- Генерация диалога ---")
    dialogue = await balbes.text.generate_dialogue(parts_count=3)
    print(f"Диалог:\n{dialogue}")
    print()
    
    # Генерация анекдота
    print("--- Генерация анекдота ---")
    anek = await balbes.text.generate_anekdote()
    print(f"Анекдот: {anek}")
    print()
    
    # Генерация с правильным синтаксисом
    print("--- Генерация с синтаксисом ---")
    syntax_text = await balbes.text.generate_with_syntax()
    print(f"Текст с синтаксисом: {syntax_text}")
    print()
    
    # Обновление текстов
    print("--- Обновление базы текстов ---")
    new_texts = texts + ["новое сообщение 1", "новое сообщение 2"]
    balbes.update_texts(new_texts)
    print(f"Новое количество текстов: {len(balbes.texts)}")
    print()
    
    print("=== Тестирование завершено ===")


if __name__ == "__main__":
    asyncio.run(main())
