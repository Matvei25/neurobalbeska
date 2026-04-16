# Neurobalbes Module

Модуль `Neurobalbes` для генерации контента: текста, мемов, демотиваторов и голосовых сообщений. Может использоваться как отдельно, так и в составе Telegram бота.

## Авторы

- **Matvei25**
- **qwen-intl**

## Возможности

- Генерация случайных фраз и текста на основе обученной модели
- Создание мемов с наложением текста на изображения
- Генерация демотиваторов в классическом стиле
- Создание голосовых сообщений из текста (TTS)
- Автоматическое масштабирование текста под размер изображения
- Поддержка водяных знаков

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/l1v0n1/neurobalbes-telegram.git
cd neurobalbes-telegram
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r app/requirements.txt
```

## Использование модуля

### Базовый пример

```python
from app.neurobalbes import Balbes

# Инициализация
balbes = Balbes(
    texts=["список", "фраз", "для", "обучения"],
    watermark="@mybot"
)

# Генерация текста
text = await balbes.text.generate_phrase()
print(text)

# Генерация мема
meme_path = await balbes.meme.create_text_meme("Текст мема", font_size=1)

# Генерация демотиватора
demo_path = await balbes.demotivator.create_demotivator(
    top_text="Заголовок",
    bottom_text="Описание",
    image_path="path/to/image.jpg"
)

# Генерация голосового сообщения
voice_path, voice_data = await balbes.voice.generate_voice("Текст для озвучки")
```

### Настройка путей к ресурсам

При инициализации можно указать пути к шрифтам и временной папке:

```python
balbes = Balbes(
    texts=["..."],
    fonts_dir="app/media/fonts",
    temp_dir="app/media/temp",
    watermark="@mybot"
)
```

## Структура модуля

```
app/neurobalbes/
├── __init__.py         # Точка входа, экспорт классов
├── balbes.py           # Основной класс Balbes
├── text_generator.py   # Генерация текста
├── meme_generator.py   # Генерация мемов
├── voice_generator.py  # Генерация голосовых сообщений
├── demotivator_generator.py  # Генерация демотиваторов
├── utils.py            # Вспомогательные функции
├── README.md           # Документация модуля
└── example.py          # Пример использования
```

## Интеграция с Telegram ботом

Модуль разработан для лёгкой интеграции с aiogram и другими фреймворками:

```python
from aiogram import Router, types
from app.neurobalbes import Balbes

router = Router()
balbes = Balbes(texts=[...])

@router.message(commands=["gen"])
async def cmd_gen(message: types.Message):
    text = await balbes.text.generate_phrase()
    await message.answer(text)
```

## Лицензия

MIT License