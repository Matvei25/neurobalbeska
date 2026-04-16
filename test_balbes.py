#!/usr/bin/env python3
"""Тестовый скрипт для проверки модуля NeuroBalbes"""

import asyncio
from app.neurobalbes import Balbes

async def main():
    # Создаём экземпляр бота
    balbes = Balbes(
        texts=[
            "Привет, я Нейробалбес!",
            "Генерирую случайный текст",
            "Создаю мемы и деморализаторы"
        ],
        watermark="@testbot"
    )
    
    print("=== Тест генерации текста ===")
    text = await balbes.text.generate_phrase()
    print(f"Сгенерированный текст: {text}")
    
    print("\n=== Тест генерации мема ===")
    # Для теста передадим dummy изображение (в реальном использовании нужен путь к файлу)
    try:
        meme_path = await balbes.meme.create_text_meme(
            text="Тестовый мем",
            meme_type=1,
            output_file="test_meme.jpg"
        )
        if meme_path:
            print(f"Мем создан: {meme_path}")
        else:
            print("Мем не создан (шаблон не найден - это нормально для теста)")
    except Exception as e:
        print(f"Ошибка при создании мема: {e}")
    
    print("\n=== Тест генерации демотиватора ===")
    try:
        demo_path = await balbes.demotivator.create_demotivator(
            top_text="Заголовок",
            bottom_text="Описание",
            image_path="app/neurobalbes/assets/default.jpg",
            output_dir="/tmp"
        )
        if demo_path:
            print(f"Деморализатор создан: {demo_path}")
        else:
            print("Деморализатор не создан (файл изображения не найден - это нормально для теста)")
    except Exception as e:
        print(f"Ошибка при создании деморализатора: {e}")
    
    print("\n=== Все тесты завершены ===")

if __name__ == "__main__":
    asyncio.run(main())
