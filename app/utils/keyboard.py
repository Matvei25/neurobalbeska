"""Модуль для создания клавиатур бота.

Может быть импортирован и использован в других скриптах.
"""
from aiogram import types


def create_help_keyboard() -> types.InlineKeyboardMarkup:
    """Создаёт клавиатуру с кнопками 'Добавить в чат' и 'Помощь'."""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text='Добавить в чат', url='http://t.me/neurobalbesbot?startgroup=start'),
            types.InlineKeyboardButton(text='Помощь', url='https://telegra.ph/FAQ-01-16-7')
        ]
    ])
    return keyboard


def create_bot_settings_keyboard() -> types.InlineKeyboardMarkup:
    """Создаёт клавиатуру настроек бота."""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text='silent.on', callback_data='silent.on'),
            types.InlineKeyboardButton(text='silent.off', callback_data='silent.off')
        ],
        [
            types.InlineKeyboardButton(text='intelligent.on', callback_data='intelligent.on'),
            types.InlineKeyboardButton(text='intelligent.off', callback_data='intelligent.off')
        ],
        [
            types.InlineKeyboardButton(text='speed 1', callback_data='speed_1'),
            types.InlineKeyboardButton(text='speed 2', callback_data='speed_2'),
            types.InlineKeyboardButton(text='speed 3', callback_data='speed_3')
        ],
        [
            types.InlineKeyboardButton(text='speed 4', callback_data='speed_4'),
            types.InlineKeyboardButton(text='speed 5', callback_data='speed_5'),
            types.InlineKeyboardButton(text='speed 6', callback_data='speed_6')
        ],
        [
            types.InlineKeyboardButton(text='Заблокировать стикер', callback_data='blockstick')
        ]
    ])
    return keyboard


def create_silent_off_keyboard() -> types.InlineKeyboardMarkup:
    """Создаёт клавиатуру с кнопкой отключения silent режима."""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='silent.off', callback_data='silent.off')]
    ])
    return keyboard


def create_wipe_keyboard() -> types.InlineKeyboardMarkup:
    """Создаёт клавиатуру для очистки сообщений."""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text='all', callback_data='wipe_all'),
            types.InlineKeyboardButton(text='text', callback_data='wipe_text'),
            types.InlineKeyboardButton(text='photo', callback_data='wipe_photo')
        ],
        [
            types.InlineKeyboardButton(text='stickers', callback_data='wipe_stickers'),
            types.InlineKeyboardButton(text='blocked stickers', callback_data='wipe_blockedstickers')
        ]
    ])
    return keyboard


def create_admin_panel_keyboard() -> types.InlineKeyboardMarkup:
    """Создаёт клавиатуру админ-панели."""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text='Рассылка', callback_data='admin_rass'),
            types.InlineKeyboardButton(text='Статистика', callback_data='admin_stats')
        ]
    ])
    return keyboard


def create_cancel_keyboard() -> types.ReplyKeyboardMarkup:
    """Создаёт клавиатуру с кнопкой 'Отмена'."""
    keyboard = types.ReplyKeyboardMarkup(keyboard=[
        [types.KeyboardButton(text='Отмена')]
    ], resize_keyboard=True)
    return keyboard


# Для обратной совместимости - готовые экземпляры клавиатур
help = create_help_keyboard()
bset = create_bot_settings_keyboard()
silentoff = create_silent_off_keyboard()
wipe = create_wipe_keyboard()
apanel = create_admin_panel_keyboard()
back = create_cancel_keyboard()
