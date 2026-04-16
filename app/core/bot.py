# -*- coding: utf-8 -*-
# Системные библиотеки
import logging
import random
import os
import time
import re
import asyncio
import sqlite3
import uuid
import json
import glob
import pathlib
import hashlib
import sys
import aiohttp
from datetime import datetime, timedelta
import aiogram.utils.exceptions

# Обработка данных и анализ
# Добавляем корневую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.mc import mc
from app.mc.builtin import validators
from app.mc.builtin.formatters import usual_syntax
import numpy as np

# Работа с изображениями и медиа
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
# Импортируем новую библиотеку вместо старой
from app.simpledemotivators_2_0 import Demotivator, Quote, TextImage
from app.media.help_utils import images_to_grid

# Телеграм и API интеграции
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import exceptions
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from translatepy import Translator
from app.api.porfir import porfirevich
from app.api.dalle import dalle_api

# Локальные модули
from app.core import config
from app.core.config import API_TOKEN, admin, bot_username, version, github_url
from app.utils import keyboard
from app.database import database as db

# Настройка логирования
log_dir = os.path.join("app", "logs")
if not os.path.exists(log_dir):
	os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler(os.path.join(log_dir, "bot.log")),
		logging.StreamHandler()
	]
)

# Инициализация бота
storage = MemoryStorage()
bot = Bot(token=API_TOKEN, timeout=200)
dp = Dispatcher(bot, storage=storage)

# Инициализация сервисов
translator = Translator()

# Глобальные переменные
dialogs = {}

# Определение состояний
class adm(StatesGroup):
	send_text = State()

class stick(StatesGroup):
	blocked = State()

# Кэш для часто используемых данных
chat_settings_cache = {}

def simbols_exists(word):
	s = """/@:"""
	return any(x for x in s if x in word)


@dp.message_handler(content_types=["new_chat_members"])
async def chat_invited(message: types.Message):
	hello_message = "дорова я нейробалбес\nкаждые 20 сообщений я генерирую мемы, так же могу генерить текст и голосовые сообщения, запоминаю ваши сообщения и картинки, которые вы отправляете\n\nне забудьте дать мне админку, а то я не смогу работать(\n\n/help - команды бота\n\n"
	for user in message.new_chat_members:
		if user.id == bot.id:
			user_channel_status = await bot.get_chat_member(
				chat_id=channel_name, user_id=message.from_user.id
			)
			if user_channel_status["status"] != "left":
				await bot.send_message(
					message.chat.id, hello_message, reply_markup=keyboard.help
				)
			else:
				await bot.send_message(
					message.chat.id,
					"Вы не подписаны на канал бота, я выхожу.\nДобавьте меня когда подпишитесь",
					reply_markup=keyboard.help,
				)
				await bot.leave_chat(message.chat.id)


@dp.message_handler(commands="admin", chat_type=types.ChatType.PRIVATE)
async def admin_panel(message: types.Message):
	if int(message.chat.id) == admin:
		await message.answer("Админ-панель", reply_markup=keyboard.apanel)

@dp.message_handler(content_types=["text"], chat_type=types.ChatType.PRIVATE)
async def private_handler(message: types.Message):
	print(message.text, message.chat.id)
	await message.answer("я работаю только в группах", reply_markup=keyboard.help)


@dp.message_handler(commands="help", chat_type=["group", "supergroup"])
async def help_message(message: types.Message):
	help_text = """
<b>📋 Команды бота Нейробалбес:</b>

<b>🤖 Основные команды:</b>
/help - список команд
/info - информация о боте
/settings - настройки бота
/premium - узнать премиум статус чата

<b>📝 Генерация текста:</b>
/gen - сгенерировать случайную фразу
/gensyntax - сгенерировать текст с правильным синтаксисом
/genlong - сгенерировать длинный текст
/genpoem - сгенерировать стихотворение
/genbugurt - сгенерировать бугурт
/genanek - сгенерировать анекдот
/gendialogue - сгенерировать диалог
/gensymbols [число] - сгенерировать текст определенной длины
/cont [текст] - продолжить фразу
/choice [A или B] - выбрать один из вариантов

<b>🔊 Голосовые сообщения:</b>
/genvoice - сгенерировать голосовое сообщение

<b>📊 Опросы:</b>
/genpoll - сгенерировать случайный опрос

<b>🖼 Изображения и мемы:</b>
/gendem - сгенерировать демотиватор
/genmem - сгенерировать мем
/quote - создать цитату (в ответ на сообщение)

<b>🗑 Управление данными:</b>
/wipe - очистить базу данных чата
"""
	await message.answer(help_text, parse_mode="HTML")


@dp.message_handler(commands=["info"])
async def info(message: types.Message):
	"""Отображает информацию о боте и статусе чата."""
	chat_id = message.chat.id
	
	# Получаем информацию о базе данных
	try:
		database = db.fullbase(chat_id)
		phrases_count = len(database["textbase"])
		photos_count = len(database["photobase"])
		stickers_count = len(database["stickers"])
		blocked_stickers = len(database["blockedstickers"])
		
		# Получаем информацию о счетчике сообщений
		message_counter = database.get("textleft", 0)
		messages_left = 20 - message_counter
		if messages_left <= 0:
			messages_left = 20
		
		# Получаем общую статистику по всем чатам
		total_chats = db.get_total_chats_count()
		total_phrases = db.get_total_phrases_count()
		
		# Получаем информацию о боте
		bot_info = await bot.get_me()
		bot_name = bot_info.username
		
		# Формируем сообщение
		info_message = (
			f"ℹ️ <b>Информация о боте</b>\n\n"
			f"🤖 Бот: @{bot_name}\n"
			f"🆔 ID чата: <code>{chat_id}</code>\n\n"
			f"📊 <b>Статистика чата:</b>\n"
			f"📝 Фраз в базе: {phrases_count}\n"
			f"🖼 Изображений: {photos_count}\n"
			f"🎭 Стикеров: {stickers_count}\n"
			f"🚫 Заблокировано стикеров: {blocked_stickers}\n"
			f"🔄 Осталось {messages_left} сообщений до генерации мема/демотиватора\n\n"
			f"🌐 <b>Общая статистика:</b>\n"
			f"👥 Всего чатов: {total_chats}\n"
			f"💬 Всего фраз: {total_phrases}\n\n"
			f"📋 <b>Системная информация:</b>\n"
			f"🔄 Версия: {version}\n"
			f"🔗 GitHub: <a href='{github_url}'>neurobalbes-telegram</a>"
		)
		
		# Отправляем сообщение
		await message.reply(info_message, parse_mode="HTML")
		
	except Exception as e:
		logging.error(f"Ошибка при получении информации: {e}")
		await message.reply(f"❌ Произошла ошибка при получении информации: {e}")


@dp.message_handler(commands="settings", chat_type=["group", "supergroup"])
async def settings(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		can_talk, intelligent, speed = (
			database["talk"],
			database["intelligent"],
			database["speed"],
		)
		if can_talk == 1 and intelligent == 0:
			mode = "может отправлять сообщения"
		elif can_talk == 0:
			mode = "не может отправлять сообщения"
		elif intelligent == 1 and can_talk == 1:
			mode = "в грамотном режиме"
		await message.answer(
			"Настройки бота\n\nНа данный момент бот {}\nСкорость генерации бота: {}\n\nУкажите настройку:\nsilent.on - бот не может писать\nsilent.off - бот может писать\n\nintelligent.on - грамотный режим общения\nintelligent.off - обычный режим общения\n\nspeed - скорость генерации текста (чем больше число, тем медленнее генерация)\n\nИспользуйте клавиатуру ниже".format(
				mode, speed
			),
			reply_markup=keyboard.bset,
		)


@dp.message_handler(commands="gen", chat_type=["group", "supergroup"])
async def generate_text(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(texts)
		if text_lines >= 1:
			generator = mc.PhraseGenerator(samples=texts)
			random_text = await generator.generate_phrase(
				validators=[validators.words_count(minimal=1)]
			)
			await message.answer(random_text)


@dp.message_handler(commands="genanek", chat_type=["group", "supergroup"])
async def gen_anek(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		a1 = ["Штирлиц шел по лесу, вдруг ему за пазуху упала гусеница.\n«{}», подумал Штирлиц."]
		a2 = ["Шел медведь по лесу\nСел в машину и — {}"]
		a3 = ["Ебутся два клоуна, а один другому говорит: — «{}»"]
		a4 = ["Заходит как-то улитка в бар\nА Бармен ей отвечает\nМы улиток не обслуживаем\nИ выпинывает ее за дверь\nЧерез неделю поиходит улитка\nИ говорит: «{}»"]
		a5 = ["— Извините, а у вас огоньку не найдется?\n— «{}» - ответил медведь из машины"]
		anek = random.choice([a1,a2,a3,a4,a5])
		generator = mc.PhraseGenerator(samples=texts)
		random_text = await generator.generate_phrase(
			validators=[validators.words_count(minimal=1)]
		)
		await message.answer(anek[0].format(random_text))


@dp.message_handler(commands="gendialogue", chat_type=["group", "supergroup"])
async def generate_dlg(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(texts)
		if text_lines >= 4:
			parts = []
			for _ in range(random.randint(3, 4)):
				generator = mc.PhraseGenerator(samples=texts)
				random_text = await generator.generate_phrase(
					validators=[validators.words_count(minimal=1)]
				)
				parts.append(random_text)
			response = "\n— ".join(parts)
			await message.answer(response)


@dp.message_handler(commands="gensyntax", chat_type=["group", "supergroup"])
async def generate_usual_syntax(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(texts)
		if text_lines >= 1:
			generator = mc.PhraseGenerator(samples=texts)
			random_text = await generator.generate_phrase(
				validators=[validators.words_count(minimal=1)],
				formatters=[usual_syntax],
			)
			await message.answer(random_text)


@dp.message_handler(commands="genvoice", chat_type=["group", "supergroup"])
async def generate_voice_message(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(texts)
		if text_lines >= 1:
			generator = mc.PhraseGenerator(samples=texts)
			random_text = await generator.generate_phrase(
				validators=[validators.words_count(minimal=1)]
			)
			random_file = (
				f"random_voice_{random.randint(0, 10000000000000000000000000)}.mp3"
			)
			try:
				tts = gTTS(text=random_text, lang="ru")
				tts.save(random_file)
				with open(random_file, "rb") as voice:
					await bot.send_voice(message.chat.id, voice)
					os.remove(random_file)
			except:
				os.remove(random_file)


@dp.message_handler(commands="gensymbols", chat_type=["group", "supergroup"])
async def generate_text_by_symbols(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(database["textbase"])
		count = message.get_args()
		if count.isdigit():
			count = int(count)
			if count <= 50 and count >= 1:
				if text_lines >= 50:
					try:
						generator = mc.PhraseGenerator(samples=texts)
						random_text = await generator.generate_phrase(
							validators=[
								validators.chars_count(minimal=count, maximal=count)
							]
						)
						await message.answer(random_text)
					except:
						await message.answer("Недостаточно сообщений для генерации.")
				else:
					await message.answer("Недостаточно сообщений для генерации.")
			else:
				await message.answer("Введите число от 1 до 50")
		else:
			await message.answer("Вы не ввели число")


@dp.message_handler(commands="genlong", chat_type=["group", "supergroup"])
async def generate_long_sentence(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(database["textbase"])
		if text_lines >= 100:
			try:
				generator = mc.PhraseGenerator(samples=texts)
				random_text = await generator.generate_phrase(
					validators=[validators.chars_count(minimal=50)]
				)
				await message.answer(random_text)
			except:
				await message.answer("Недостаточно сообщений для генерации.")
		else:
			await message.answer("Недостаточно сообщений для генерации.")


@dp.message_handler(commands="genpoem", chat_type=["group", "supergroup"])
async def generate_poem(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(database["textbase"])
		if text_lines >= 100:
			generator = mc.PhraseGenerator(samples=texts)
			poem = []
			poem.append("от знаменитого писателя - Нейробалбеса\n")
			for i in range(random.randint(4, 16)):
				phrase = await generator.generate_phrase(
					validators=[validators.words_count(minimal=4)],
					formatters=[usual_syntax],
				)
				poem.append(phrase)
			finish = "\n".join(poem)
			await message.answer(finish)
		else:
			await message.answer("Недостаточно сообщений для генерации")


@dp.message_handler(commands="genpoll", chat_type=["group", "supergroup"])
async def generate_poll(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(database["textbase"])
		if text_lines >= 4:
			generator = mc.PhraseGenerator(samples=texts)
			random_text = await generator.generate_phrase(
				validators=[validators.chars_count(minimal=1, maximal=100)]
			)
			random_text2 = await generator.generate_phrase(
				validators=[validators.chars_count(minimal=1, maximal=100)]
			)
			random_text3 = await generator.generate_phrase(
				validators=[validators.chars_count(minimal=1, maximal=100)]
			)
			random_text4 = await generator.generate_phrase(
				validators=[validators.chars_count(minimal=1, maximal=100)]
			)
			await bot.send_poll(
				message.chat.id, random_text, [random_text2, random_text3, random_text4]
			)


@dp.message_handler(commands="genbugurt", chat_type=["group", "supergroup"])
async def generate_bugurt(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		text_lines = len(texts)
		if text_lines >= 1:
			generator = mc.PhraseGenerator(samples=texts)
			bugurt = []
			for i in range(random.randint(2, 8)):
				phrase = await generator.generate_phrase(
					validators=[validators.words_count(minimal=1)]
				)
				bugurt.append(phrase)
			finish = "\n@\n".join(bugurt)
			await message.answer(finish.upper())


@dp.message_handler(commands="cont", chat_type=["group", "supergroup"])
async def continue_sentence(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		texts = database["textbase"]
		txt = str(message.get_args())
		retrieved_elements = list(filter(lambda x: txt in x, texts))
		if retrieved_elements == []:
			await message.answer(txt)
		else:
			await message.answer(random.choice(retrieved_elements))


@dp.message_handler(commands="choice", chat_type=["group", "supergroup"])
async def choice_oneortwo(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		try:
			t, d = message.get_args().split("или")
			l = [t, d]
			s = [
				"ну наверно",
				"я думаю",
				"я наверно выберу",
				"ну конечно же",
				"ты еще спрашиваешь? я выбираю",
				"балбес выбирает",
			]
			await message.answer(f"{random.choice(s)} {random.choice(l)}")
		except:
			await message.answer(
				"Введите команды в формате: /choice а или б (а и б нужно заменить на ваши слова)"
			)



@dp.message_handler(commands="gendem", chat_type=["group", "supergroup"])
async def generate_demotivator(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		text_lines = len(database["textbase"])
		pic_count = len(database["photobase"])
		texts = database["textbase"]
		pictures = database["photobase"]
		if text_lines >= 10 and pic_count >= 1:
			if (
				message.chat.id not in dialogs
				or time.time() >= dialogs[message.chat.id]
			):
				dialogs[message.chat.id] = time.time() + 10
				generator = mc.PhraseGenerator(samples=texts)
				random_text = await generator.generate_phrase(
					validators=[validators.words_count(minimal=1, maximal=5)]
				)
				random_bottom_text = await generator.generate_phrase(
					validators=[validators.words_count(minimal=1, maximal=5)]
				)
				
				# Создаем временную директорию
				temp_dir = await init_temp_directories()
				
				# Подготавливаем идентификаторы для файлов
				random_picture = random.choice(pictures)
				random_filename = get_temp_filename(prefix="input", extension="jpg")
				result_prefix = get_temp_filename(prefix="result", extension="")
				
				# Скачиваем изображение
				dw = await bot.download_file_by_id(random_picture)
				random_filepath = os.path.join(temp_dir, random_filename)
				with open(random_filepath, "wb") as f:
					f.write(dw.read())
				
				# Проверяем изображение
				valid_image = False
				try:
					with Image.open(random_filepath) as img:
						img.load()
						logging.info(f"Image validated successfully: {random_filepath}, size: {img.size}, format: {img.format}")
						valid_image = True
				except Exception as img_error:
					logging.error(f"Invalid image file: {img_error}")
					if os.path.exists(random_filepath):
						os.remove(random_filepath)
					await message.reply("Не удалось создать демотиватор: некорректное изображение.")
				
				if valid_image:
					# Создаем демотиватор используя новую библиотеку
					style = random.randint(1, 2)
					
					try:
						# В зависимости от стиля создаем демотиватор с одним или двумя текстовыми полями
						if style == 1:
							dem = Demotivator(random_text.lower(), random_bottom_text.lower())
						else:
							dem = Demotivator(random_text.lower(), "")
						
						# Создаем демотиватор асинхронно
						await dem.create(
							folder_name=temp_dir, 
							avatar_name=random_filename, 
							result_filename=result_prefix,
							watermark=bot_username,
						)
						
						# Полный путь к результату
						dem_filepath = os.path.join(temp_dir, f"{result_prefix}_dem.jpg")
						
						# Отправляем результат, если файл существует
						if os.path.exists(dem_filepath):
							with open(dem_filepath, "rb") as photo:
								await bot.send_photo(message.chat.id, photo)
							# Удаляем результат
							os.remove(dem_filepath)
						else:
							await message.reply("Не удалось создать демотиватор. Попробуйте еще раз.")
							
					except Exception as e:
						logging.error(f"Error creating demotivator: {e}", exc_info=True)
						await message.reply("Произошла ошибка при создании демотиватора.")
					
					# Удаляем исходное изображение
					if os.path.exists(random_filepath):
						os.remove(random_filepath)
						
			elif message.chat.id in dialogs and time.time() <= dialogs[message.chat.id]:
				await message.answer("слишком рано\nподожди еще немного")
		else:
			await message.answer(
				"Недостаточно сообщений для генерации.\nНужное количество: 10 сообщений и 1 фотография"
			)


@dp.message_handler(commands="genmem", chat_type=["group", "supergroup"])
async def generate_meme(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		database = db.fullbase(message.chat.id)
		text_lines = len(database["textbase"])
		pic_count = len(database["photobase"])
		texts = database["textbase"]
		pictures = database["photobase"]
		random_filename = (
			f"randomimg_{random.randint(0, 10000000000000000000000000)}.jpg"
		)
		dem_filename = f"result_{random.randint(0, 10000000000000000000000000)}.jpg"
		if text_lines >= 10 and pic_count >= 1:
			if (
				message.chat.id not in dialogs
				or time.time() >= dialogs[message.chat.id]
			):
				dialogs[message.chat.id] = time.time() + 10
				generator = mc.PhraseGenerator(samples=texts)
				ll = random.randint(1, 24)
				if ll == 1:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=30)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=30)]
					)
					photo1 = Image.open(get_image_path("mem.jpg"))
					font = get_font("arialbd.ttf", size=30)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((90, 5), rndtxt.lower(), font=font, fill="black")
					idraw.text((70, 82), rndtxt2.lower(), font=font, fill="black")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 2:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())

					photo1 = Image.open(get_image_path("mem2.jpg"))

					user_img = (
						Image.open(random_filename).convert("RGBA").resize((348, 231))
					)
					
					photo1.paste(user_img, (367, 210))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				elif ll == 3:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					photo1 = Image.open(get_image_path("mem2.jpg"))
					user_img = (
						Image.open(random_filename).convert("RGBA").resize((595, 289))
					)
					photo1.paste(user_img, (0, 304))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				elif ll == 4:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=30)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=30)]
					)
					photo1 = Image.open(get_image_path("2.jpg"))
					font = get_font("arialbd.ttf", size=45)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((50, 200), rndtxt.lower(), font=font, fill="black")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 5:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("1.jpg"))
					font = get_font("arialbd.ttf", size=40)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((125, 350), rndtxt.lower(), font=font, fill="black")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 6:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("4.jpg"))
					font = get_font("arialbd.ttf", size=30)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((120, 170), rndtxt.lower(), font=font, fill="black")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 7:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("7.jpg"))
					font = get_font("arialbd.ttf", size=40)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((150, 130), rndtxt.lower(), font=font, fill="black")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 8:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("5.jpg"))
					font = get_font("arialbd.ttf", size=65)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((340, 210), rndtxt.lower(), font=font, fill="black")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 9:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("6.jpg"))
					font = get_font("arialbd.ttf", size=26)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((180, 50), rndtxt.lower(), font=font, fill="black")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				if ll == 10:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("3.jpg"))
					font = get_font("arialbd.ttf", size=30)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((85, 290), rndtxt.lower(), font=font, fill="white")
					idraw.text((85, 825), rndtxt2.lower(), font=font, fill="white")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 11:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					photo1 = Image.open(get_image_path("11.jpg"))
					user_img = (
						Image.open(random_filename).convert("RGBA").resize((300, 277))
					)
					photo1.paste(user_img, (364, 380))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				elif ll == 12:
					random_filename2 = (
						f"randomimg_{random.randint(0, 10000000000000000000000000)}.jpg"
					)
					rndpic = random.choice(pictures)
					rndpic2 = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					dw = await bot.download_file_by_id(rndpic2)
					with open(random_filename2, "wb") as f:
						f.write(dw.read())

					photo1 = Image.open(get_image_path("10.jpg"))

					user_img = (
						Image.open(random_filename).convert("RGBA").resize((470, 287))
					)
					user_img2 = (
						Image.open(random_filename2).convert("RGBA").resize((470, 287))
					)
					photo1.paste(user_img, (314, 25))
					photo1.paste(user_img2, (314, 324))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
							os.remove(random_filename2)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
						os.remove(random_filename2)
				elif ll == 13:
					random_filename2 = (
						f"randomimg_{random.randint(0, 10000000000000000000000000)}.jpg"
					)
					random_filename3 = (
						f"randomimg_{random.randint(0, 10000000000000000000000000)}.jpg"
					)
					random_filename4 = (
						f"randomimg_{random.randint(0, 10000000000000000000000000)}.jpg"
					)
					rndpic = random.choice(pictures)
					rndpic2 = random.choice(pictures)
					rndpic3 = random.choice(pictures)
					rndpic4 = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					dw = await bot.download_file_by_id(rndpic2)
					with open(random_filename2, "wb") as f:
						f.write(dw.read())

					dw = await bot.download_file_by_id(rndpic3)
					with open(random_filename3, "wb") as f:
						f.write(dw.read())
					dw = await bot.download_file_by_id(rndpic4)
					with open(random_filename4, "wb") as f:
						f.write(dw.read())

					photo1 = Image.open(get_image_path("12.jpg"))

					user_img = (
						Image.open(random_filename).convert("RGBA").resize((336, 255))
					)
					user_img2 = (
						Image.open(random_filename2).convert("RGBA").resize((336, 253))
					)
					user_img3 = (
						Image.open(random_filename3).convert("RGBA").resize((336, 255))
					)
					user_img4 = (
						Image.open(random_filename4).convert("RGBA").resize((336, 313))
					)
					photo1.paste(user_img, (0, 0))
					photo1.paste(user_img2, (0, 255))
					photo1.paste(user_img3, (0, 509))
					photo1.paste(user_img4, (0, 768))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
							os.remove(random_filename2)
							os.remove(random_filename3)
							os.remove(random_filename4)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
						os.remove(random_filename2)
						os.remove(random_filename3)
						os.remove(random_filename4)
				elif ll == 14:
					random_filename2 = (
						f"randomimg_{random.randint(0, 10000000000000000000000000)}.jpg"
					)
					rndpic = random.choice(pictures)
					rndpic2 = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					dw = await bot.download_file_by_id(rndpic2)
					with open(random_filename2, "wb") as f:
						f.write(dw.read())

					photo1 = Image.open(get_image_path("13.jpg"))

					user_img = (
						Image.open(random_filename).convert("RGBA").resize((256, 199))
					)
					user_img2 = (
						Image.open(random_filename2).convert("RGBA").resize((256, 199))
					)
					photo1.paste(user_img, (0, 0))
					photo1.paste(user_img2, (0, 201))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
							os.remove(random_filename2)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
						os.remove(random_filename2)
				elif ll == 15:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())

					photo1 = Image.open(get_image_path("14.jpg"))

					user_img = (
						Image.open(random_filename).convert("RGBA").resize((450, 281))
					)
					photo1.paste(user_img, (147, 311))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				elif ll == 16:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("15.jpg"))
					font = get_font("arialbd.ttf", size=33)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((70, 160), rndtxt.lower(), font=font, fill="white")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 17:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())

					photo1 = Image.open(get_image_path("16.jpg"))

					user_img = (
						Image.open(random_filename).convert("RGBA").resize((406, 423))
					)
					photo1.paste(user_img, (460, 657))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				elif ll == 18:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("17.jpg"))
					font = get_font("arialbd.ttf", size=30)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((250, 330), rndtxt.lower(), font=font, fill="white")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 19:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=16)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=16)]
					)
					photo1 = Image.open(get_image_path("18.jpg"))
					font = get_font("arialbd.ttf", size=30)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((100, 130), rndtxt.lower(), font=font, fill="white")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 20:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					photo1 = Image.open(get_image_path("19.jpg"))
					user_img = (
						Image.open(random_filename).convert("RGBA").resize((567, 360))
					)
					photo1.paste(user_img, (0, 345))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				elif ll == 21:
					rndtxt = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					rndtxt2 = await generator.generate_phrase(
						validators=[validators.chars_count(minimal=1, maximal=20)]
					)
					photo1 = Image.open(get_image_path("20.jpg"))
					font = get_font("arialbd.ttf", size=25)
					idraw = ImageDraw.Draw(photo1)
					idraw.text((455, 80), rndtxt.lower(), font=font, fill="black")
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
					except:
						os.remove(dem_filename)
				elif ll == 22:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					photo1 = Image.open(get_image_path("21.jpg"))
					user_img = (
						Image.open(random_filename).convert("RGBA").resize((720, 520))
					)
					photo1.paste(user_img, (0, 78))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				elif ll == 23:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					photo1 = Image.open(get_image_path("22.jpg"))
					user_img = (
						Image.open(random_filename).convert("RGBA").resize((794, 470))
					)
					photo1.paste(user_img, (0, 615))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				elif ll == 24:
					rndpic = random.choice(pictures)
					dw = await bot.download_file_by_id(rndpic)
					with open(random_filename, "wb") as f:
						f.write(dw.read())
					photo1 = Image.open(get_image_path("23.jpg"))
					user_img = (
						Image.open(random_filename).convert("RGBA").resize((556, 314))
					)
					photo1.paste(user_img, (524, 755))
					photo1.save(dem_filename)
					try:
						with open(dem_filename, "rb") as photo:
							await bot.send_photo(message.chat.id, photo)
							os.remove(dem_filename)
							os.remove(random_filename)
					except:
						os.remove(dem_filename)
						os.remove(random_filename)
				try:
					del dialogs[message.chat.id]
				except:
					pass
			elif message.chat.id in dialogs and time.time() <= dialogs[message.chat.id]:
				await message.answer("слишком рано\nподожди еще немного")
		else:
			await message.answer(
				"Недостаточно сообщений для генерации.\nНужное количество: 10 сообщений и 1 фотография"
			)


@dp.callback_query_handler(lambda call: call.data.startswith("admin"))
async def adminpanel(call):
	if "rass" in call.data:
		await call.message.answer(
			"Введите текст для рассылки.\n\nДля отмены нажмите кнопку ниже 👇",
			reply_markup=keyboard.back,
		)
		await adm.send_text.set()
	elif "stats" in call.data:
		count = db.sender()
		await call.answer("Всего чатов: {}".format(len(count)))


@dp.callback_query_handler(text="blockstick")
async def blocksticker(call: types.CallbackQuery):
	member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
	if member.is_chat_admin():
		await call.message.answer("Отправьте стикер для блокировки")
		await stick.blocked.set()
	else:
		await call.answer("Вы не администратор группы")


@dp.message_handler(state=stick.blocked, content_types=["sticker"])
async def yanegr(message: types.Message, state: FSMContext):
	member = await bot.get_chat_member(message.chat.id, message.from_user.id)
	if member.is_chat_admin():
		await state.finish()
		db.update_sticker_blocks(message.chat.id, message.sticker.file_id)
		await message.answer("Стикер успешно добавлен в список заблокированных.")


@dp.message_handler(state=adm.send_text)
async def process_name(message: types.Message, state: FSMContext):
	if message.text == "Отмена":
		await message.answer(
			"Отмена! Возвращаю в главное меню.",
			reply_markup=types.ReplyKeyboardRemove(),
		)
		await state.finish()
	else:
		info = db.sender()
		await message.answer("Начинаю рассылку в группы, где я состою...")
		success_count = 0
		error_count = 0
		skipped_count = 0
		
		for chat_info in info:
			try:
				if not chat_info or len(chat_info) == 0:
					skipped_count += 1
					continue
					
				chat_id = chat_info[0]
				
				# Обработка разных форматов chat_id
				target_id = None
				
				# Если ID начинается с 'peer', это группа
				if isinstance(chat_id, str) and chat_id.startswith('peer'):
					try:
						target_id = int(f'-{chat_id[4:]}')
					except (ValueError, IndexError):
						logging.error(f"Неверный формат ID группы: {chat_id}")
						error_count += 1
						continue
				# Если ID отрицательное число, это также группа
				elif isinstance(chat_id, int) and chat_id < 0:
					target_id = chat_id
				# Если пытаемся превратить строку в число и оно отрицательное
				elif isinstance(chat_id, str) and chat_id.startswith('-'):
					try:
						target_id = int(chat_id)
					except ValueError:
						logging.error(f"Неверный формат ID группы: {chat_id}")
						error_count += 1
						continue
				
				# Пропускаем, если это не ID группы
				if not target_id or target_id >= 0:
					skipped_count += 1
					continue
				
				# Проверяем, состоит ли бот в этой группе
				try:
					# Пробуем получить информацию о чате - если это удастся, значит бот там состоит
					chat = await bot.get_chat(target_id)
					
					# Проверяем, что это группа или супергруппа
					if chat.type in ["group", "supergroup"]:
						await bot.send_message(target_id, message.text)
						success_count += 1
						logging.info(f"Сообщение отправлено в группу {chat.title} (ID: {target_id})")
					else:
						skipped_count += 1
						logging.info(f"Пропускаем {target_id}: не является группой")
				except aiogram.utils.exceptions.ChatNotFound:
					skipped_count += 1
					logging.info(f"Пропускаем {target_id}: бот не состоит в группе или группа не существует")
				except aiogram.utils.exceptions.BotKicked:
					skipped_count += 1
					logging.info(f"Пропускаем {target_id}: бот был исключен из группы")
				except Exception as e:
					error_count += 1
					logging.error(f"Ошибка при отправке в {target_id}: {str(e)}")
			except Exception as e:
				error_count += 1
				logging.error(f"Ошибка при обработке: {str(e)}")
		
		await state.finish()
		await message.answer(
			f"Рассылка завершена.\n"
			f"✅ Успешно отправлено: {success_count}\n"
			f"⏩ Пропущено: {skipped_count}\n"
			f"❌ Ошибок: {error_count}", 
			reply_markup=keyboard.help
		)


@dp.callback_query_handler()
async def settings_silent_on(call):
	db.insert(call.message.chat.id)
	if call.from_user.is_bot is False:
		member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
		if member.is_chat_admin():
			base = db.fullbase(call.message.chat.id)
			if call.data == "silent.on":
				if base["talk"] == 0:
					await call.answer("Данная настройка уже выбрана")
				else:
					db.change_field(call.message.chat.id, "talk", 0)
					await call.answer(
						"Вы запретили мне писать, теперь я буду молчать :("
					)
			elif call.data == "silent.off":
				if base["talk"] == 1:
					await call.answer("Данная настройка уже выбрана")
				else:
					db.change_field(call.message.chat.id, "talk", 1)
					await call.answer("Вы разрешили мне писать, спасибо!")
			elif call.data == "intelligent.on":
				if base["intelligent"] == 1:
					await call.answer("Данная настройка уже выбрана")
				else:
					db.change_field(call.message.chat.id, "intelligent", 1)
					await call.answer(
						"Уважаемый, теперь моя манера речи сильно изменится."
					)
			elif call.data == "intelligent.off":
				if base["intelligent"] == 0:
					await call.answer("Данная настройка уже выбрана")
				else:
					db.change_field(call.message.chat.id, "intelligent", 0)
					await call.answer("Бот теперь в обычном режиме")
			elif "speed" in call.data:
				speed = call.data.split("_")[1]
				if base["speed"] == int(speed):
					await call.answer("Данная скорость уже выбрана.")
				else:
					db.change_field(call.message.chat.id, "speed", int(speed))
					await call.answer("Новая скорость генерации успешно установлена.")
			elif "wipe" in call.data:
				wipe = call.data.split("_")[1]
				if wipe == "all":
					db.clear_all_base(call.message.chat.id)
					await call.answer("Все данные успешно удалены.")
				elif wipe == "text":
					db.clear_text_base(call.message.chat.id)
					await call.answer("Все сообщения успешно удалены.")
				elif wipe == "photo":
					db.clear_photo_base(call.message.chat.id)
					await call.answer("Все фото успешно удалены.")
				elif wipe == "stickers":
					db.clear_sticker_base(call.message.chat.id)
					await call.answer("Все стикеры успешно удалены.")
				elif wipe == "blockedstickers":
					db.clear_blockedstickers(call.message.chat.id)
					await call.answer("Все заблокированные стикеры удалены.")
		else:
			await call.answer("Вы не администратор группы")


@dp.message_handler(commands="quote", chat_type=["group", "supergroup"])
async def quote(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		# Создаем временную директорию, если её нет
		temp_dir = await init_temp_directories()
		save_filename = get_temp_filename(prefix="quote", extension="png")
		
		if message.reply_to_message is None:
			await message.answer("Используйте эту команду ответив на сообщение.")
		else:
			if message.reply_to_message.text is None:
				text = ""
			else:
				text = message.reply_to_message.text
				
			try:
				# Создаем объект цитаты с новой библиотекой
				quote_maker = Quote(text, message.reply_to_message.from_user.first_name)
				
				# Используем асинхронный метод create
				await quote_maker.create(
					folder_name=temp_dir,
					avatar_name="https://sun9-84.userapi.com/impf/GvKkDkADCuUzRkEglKfsMhIu_fFEwR7gra0-6A/72NHz1uPsO4.jpg?size=720x708&quality=96&sign=dabbf769d7e2086a37367d3bfeedd222&type=album",
					result_filename=save_filename,
					use_url=True,
				)
				
				# Полный путь к сгенерированному файлу
				result_file = os.path.join(temp_dir, f"{save_filename}_quote.png")
				
				# Отправляем фото, если файл существует
				if os.path.exists(result_file):
					with open(result_file, "rb") as p:
						await bot.send_photo(message.chat.id, p)
					# Удаляем временный файл
					os.remove(result_file)
				else:
					await message.reply("Не удалось создать цитату. Попробуйте еще раз.")
			except Exception as e:
				logging.error(f"Ошибка при создании цитаты: {e}", exc_info=True)
				await message.reply("Произошла ошибка при создании цитаты.")


@dp.message_handler(commands="wipe", chat_type=["group", "supergroup"])
async def wipe_db(message: types.Message):
	db.insert(message.chat.id)
	if message.from_user.is_bot is False:
		await message.answer(
			"Выбери на клавиатуре, что хотите очистить\n\nвсё (all), картинки (photo) или текст (text)",
			reply_markup=keyboard.wipe,
		)


@dp.message_handler(content_types=["photo"], chat_type=["group", "supergroup"])
async def photo_handler(message: types.Message):
	# Оптимизация: используем одну транзакцию для всех операций с БД
	db.insert(message.chat.id)
	
	if message.from_user.is_bot:
		return
		
	# Обработка подписи фото, если есть
	if message.caption:
		db.update_text_base(message.chat.id, message.caption)
	
	# Получаем файл изображения
	file_id = message.photo[-1].file_id
	
	# Проверяем лимиты
	base = db.fullbase(message.chat.id)
	pic_count = len(base["photobase"])
	
	# Определяем лимит на основе премиум-статуса
	premium_path = os.path.join("app", "premium.txt")
	try:
		with open(premium_path, "r", encoding="utf8") as premiums:
			prem = [line.strip() for line in premiums.readlines() if line.strip() and not line.startswith('#')]
	except FileNotFoundError:
		logging.warning("premium.txt file not found. Creating empty file.")
		os.makedirs(os.path.dirname(premium_path), exist_ok=True)
		with open(premium_path, "w", encoding="utf8") as premiums:
			premiums.write("# List of premium chat IDs\n# Add one chat ID per line\n")
		prem = []
	
	max_photo = 1000 if str(message.chat.id) in prem else 500
	
	# Добавляем фото только если не превышен лимит
	if pic_count < max_photo:
		db.update_photo_base(message.chat.id, file_id)


@dp.message_handler(content_types=["sticker"], chat_type=["group", "supergroup"])
async def stickers_handler(message: types.Message):
	# Пропускаем сообщения от ботов
	if message.from_user.is_bot:
		return
		
	# Вставляем чат в базу данных, если его там еще нет
	db.insert(message.chat.id)
	
	# Проверяем лимиты
	base = db.fullbase(message.chat.id)
	stic_count = len(base["stickers"])
	
	# Определяем лимит на основе премиум-статуса
	premium_path = os.path.join("app", "premium.txt")
	try:
		with open(premium_path, "r", encoding="utf8") as premiums:
			prem = [line.strip() for line in premiums.readlines() if line.strip() and not line.startswith('#')]
	except FileNotFoundError:
		logging.warning("premium.txt file not found. Creating empty file.")
		os.makedirs(os.path.dirname(premium_path), exist_ok=True)
		with open(premium_path, "w", encoding="utf8") as premiums:
			premiums.write("# List of premium chat IDs\n# Add one chat ID per line\n")
		prem = []
	
	max_stickers = 400 if str(message.chat.id) in prem else 200
	
	# Добавляем стикер только если не превышен лимит
	if stic_count < max_stickers:
		db.update_sticker_base(message.chat.id, message.sticker.file_id)


@dp.message_handler(content_types=["text"], chat_type=["group", "supergroup"])
async def all_message_handler(message: types.Message):
	# Пропускаем сообщения от ботов
	if message.from_user.is_bot:
		return
	
	# Проверяем, является ли сообщение командой или ссылкой
	if (message.text in [
			"gen", "genmem", "gendem", "genpoll", "info", "help", 
			"genbugurt", "genpoem", "genlong", "gensymbols", "genvoice",
			"gensyntax", "settings", "cont", "choice", "http", "wipe"
		] or message.text.startswith("/") or message.text.startswith("http")
	):
		return
		
	# Проверяем длину сообщения
	if not (0 < len(message.text) <= 1000):
		return
		
	# Вставляем чат в базу данных, если его там еще нет
	chat_id = message.chat.id
	db.insert(chat_id)
	
	# Устанавливаем лимит для всех чатов
	maxlen = 2000
	
	# Получаем базу данных чата
	database = db.fullbase(chat_id)
	
	# Добавляем сообщение в базу, если не превышен лимит
	if len(database["textbase"]) < maxlen:
		db.update_text_base(chat_id, message.text)
	
	# Получаем обновленную базу данных и извлекаем нужные данные
	database = db.fullbase(chat_id)
	text_lines = len(database["textbase"])
	pic_count = len(database["photobase"])
	
	# Получаем параметры чата
	can_talk = database.get("talk", 1)  # Режим разговора (1 - включен, 0 - выключен)
	intelligent = database.get("intelligent", 0)  # Умный режим
	try:
		speed = int(database.get("speed", 20))  # Скорость генерации сообщений
	except (ValueError, TypeError):
		logging.warning(f"Invalid speed value in database for chat_id {chat_id}, using default")
		speed = 20
	txtgen = database.get("textleft", 0)  # Счетчик сообщений
	
	# Обновляем счетчики текстовых сообщений
	db.update_text_left(chat_id)
	db.update_text_count(chat_id, text_lines)
	
	# Получаем тексты и фотографии
	texts = database["textbase"]
	pictures = database["photobase"]
	
	# Если режим тишины включен, выходим
	if can_talk == 0:
		return
	
	try:
		# Создаем генератор фраз
		generator = mc.PhraseGenerator(samples=texts)
		
		# Генерируем текст на основе настроек
		if intelligent == 1:
			generation_style = await generator.generate_phrase(
				validators=[validators.words_count(minimal=1)],
				formatters=[usual_syntax],
			)
		else:
			generation_style = await generator.generate_phrase(
				validators=[validators.words_count(minimal=1)]
			)
		
		# Сбрасываем счетчик сообщений если достигнут лимит
		if txtgen >= 19:
			db.change_field(chat_id, "textleft", 0)
			
			# Генерация мема или демотиватора каждые 20 сообщений
			if text_lines >= 20 and pic_count >= 1:
				# Случайно выбираем тип контента
				content_type = random.randint(1, 3)
				
				if content_type == 1 and pic_count >= 1:
					# Генерация мема
					await generate_random_meme(chat_id, texts, pictures, generator)
				elif content_type == 2 and pic_count >= 1:
					# Генерация демотиватора
					await generate_random_demotivator(chat_id, texts, pictures, generator)
				elif content_type == 3:
					# Генерация опроса
					await generate_random_poll(chat_id, generator)
		
		# Проверяем упоминание бота в сообщении
		if "балбес" in message.text.lower() or "balbes" in message.text.lower():
			try:
				await message.reply(generation_style)
			except exceptions.RetryAfter as e:
				await asyncio.sleep(e.timeout)
		else:
			# Случайная генерация с заданной вероятностью
			if random.randint(1, speed) == 1:
				# Определяем, отвечать на сообщение или просто отправить в чат
				if random.randint(1, 10) == 5:
					try:
						await message.reply(generation_style)
					except exceptions.RetryAfter as e:
						await asyncio.sleep(e.timeout)
				else:
					try:
						await message.answer(generation_style)
					except exceptions.RetryAfter as e:
						await asyncio.sleep(e.timeout)
			else:
				# Редкая генерация голосового сообщения (1/17 вероятность)
				if random.randint(1, 17) == 1:
					await generate_and_send_voice(message, database)
				# Редкая отправка стикера (1/17 вероятность)
				elif random.randint(1, 17) == 2 and len(database["stickers"]) > 0:
					await send_random_sticker(chat_id, database)
	except exceptions.RetryAfter as e:
		logging.error(f'Словил ошибку RetryAfter: {e}')
		await asyncio.sleep(e.timeout)
	except Exception as e:
		logging.error(f'Ошибка при обработке текстового сообщения: {e}')

# Функция для отправки случайного стикера
async def send_random_sticker(chat_id, database):
	"""
	Отправляет случайный стикер из базы стикеров чата.
	"""
	stickers = database["stickers"]
	blocked = database["blockedstickers"]
	
	if not stickers:
		return
		
	sticker = random.choice(stickers)
	if sticker not in blocked:
		try:
			await bot.send_sticker(chat_id, sticker)
		except exceptions.RetryAfter as e:
			await asyncio.sleep(e.timeout)
		except Exception as e:
			logging.error(f"Ошибка при отправке стикера: {e}")

# Функция генерации случайного мема
async def generate_random_meme(chat_id, texts, pictures, generator):
	"""
	Генерирует и отправляет случайный мем.
	"""
	try:
		# Создаем временные файлы
		random_filename = f"randomimg_{random.randint(0, 10000000000000000000000000)}.jpg"
		dem_filename = f"result_{random.randint(0, 10000000000000000000000000)}.jpg"
		
		# Выбираем случайный шаблон мема
		meme_type = random.randint(1, 24)
		
		if meme_type <= 10:  # Мемы с текстом
			# Генерируем текст для мема
			rndtxt = await generator.generate_phrase(
				validators=[validators.chars_count(minimal=1, maximal=30)]
			)
			
			# Выбираем шаблон
			template_path = f"app/media/images/{meme_type}.jpg"
			
			if os.path.exists(template_path):
				photo1 = Image.open(template_path)
				font = get_font("arialbd.ttf", size=30)
				idraw = ImageDraw.Draw(photo1)
				
				# Добавляем текст (позиции зависят от шаблона)
				if meme_type == 1:
					idraw.text((90, 5), rndtxt.lower(), font=font, fill="black")
				elif meme_type == 2:
					idraw.text((50, 200), rndtxt.lower(), font=font, fill="black")
				# Другие варианты позиционирования...
				
				# Сохраняем и отправляем
				photo1.save(dem_filename)
				with open(dem_filename, "rb") as photo:
					await bot.send_photo(chat_id, photo)
			
		else:  # Мемы с изображениями
			# Скачиваем случайную картинку
			rndpic = random.choice(pictures)
			dw = await bot.download_file_by_id(rndpic)
			with open(random_filename, "wb") as f:
				f.write(dw.read())
			
			# Обрабатываем изображение
			template_path = f"app/media/images/{meme_type-10}.jpg"
			if os.path.exists(template_path):
				photo1 = Image.open(template_path)
				
				# Размеры и позиции зависят от шаблона
				size = (400, 300)  # Примерный размер
				position = (0, 0)  # Примерная позиция
				
				# Подготавливаем изображение пользователя
				try:
					user_img = Image.open(random_filename).convert("RGBA").resize(size)
					photo1.paste(user_img, position)
					photo1.save(dem_filename)
					
					# Отправляем результат
					with open(dem_filename, "rb") as photo:
						await bot.send_photo(chat_id, photo)
				except Exception as e:
					logging.error(f"Ошибка при создании мема: {e}")
	
	except Exception as e:
		logging.error(f"Ошибка при генерации мема: {e}")
	finally:
		# Удаляем временные файлы
		for filename in [random_filename, dem_filename]:
			if os.path.exists(filename):
				try:
					os.remove(filename)
				except:
					pass

# Функция для генерации случайного демотиватора
async def generate_random_demotivator(chat_id, texts, pictures, generator):
	"""
	Генерирует и отправляет случайный демотиватор.
	"""
	try:
		# Генерируем тексты
		random_text = await generator.generate_phrase(
			validators=[validators.words_count(minimal=1, maximal=5)]
		)
		random_bottom_text = await generator.generate_phrase(
			validators=[validators.words_count(minimal=1, maximal=5)]
		)
		
		# Создаем временную директорию
		temp_dir = await init_temp_directories()
		
		# Подготавливаем идентификаторы для файлов
		random_picture = random.choice(pictures)
		random_filename = get_temp_filename(prefix="input", extension="jpg")
		result_prefix = get_temp_filename(prefix="result", extension="")
		
		# Скачиваем случайное изображение
		dw = await bot.download_file_by_id(random_picture)
		random_filepath = os.path.join(temp_dir, random_filename)
		with open(random_filepath, "wb") as f:
			f.write(dw.read())
		
		# Создаем демотиватор
		style = random.randint(1, 2)
		if style == 1:
			# Демотиватор с двумя текстами
			try:
				dem = Demotivator(random_text.lower(), random_bottom_text.lower())
				await dem.create(
					folder_name=temp_dir, 
					avatar_name=random_filename, 
					result_filename=result_prefix,
					watermark=bot_username,
				)
				
				# Полный путь к результату
				dem_filepath = os.path.join(temp_dir, f"{result_prefix}_dem.jpg")
				
				# Отправляем результат
				if os.path.exists(dem_filepath):
					with open(dem_filepath, "rb") as photo:
						await bot.send_photo(chat_id, photo)
					# Удаляем после отправки
					os.remove(dem_filepath)
				
			except Exception as e:
				logging.error(f"Ошибка при создании демотиватора: {e}")
		else:
			# Демотиватор с одним текстом
			try:
				dem = Demotivator(random_text.lower(), "")
				await dem.create(
					folder_name=temp_dir, 
					avatar_name=random_filename, 
					result_filename=result_prefix,
					watermark=bot_username,
				)
				
				# Полный путь к результату
				dem_filepath = os.path.join(temp_dir, f"{result_prefix}_dem.jpg")
				
				# Отправляем результат
				if os.path.exists(dem_filepath):
					with open(dem_filepath, "rb") as photo:
						await bot.send_photo(chat_id, photo)
					# Удаляем после отправки
					os.remove(dem_filepath)
					
			except Exception as e:
				logging.error(f"Ошибка при создании демотиватора: {e}")
	
	except Exception as e:
		logging.error(f"Ошибка при генерации демотиватора: {e}")
	finally:
		# Удаляем временные файлы
		try:
			if os.path.exists(random_filepath):
				os.remove(random_filepath)
		except:
			pass

# Функция для генерации случайного опроса
async def generate_random_poll(chat_id, generator):
	"""
	Генерирует и отправляет случайный опрос.
	"""
	try:
		# Генерируем вопрос и варианты ответов
		random_text = await generator.generate_phrase(
			validators=[validators.chars_count(minimal=1, maximal=100)]
		)
		random_text2 = await generator.generate_phrase(
			validators=[validators.chars_count(minimal=1, maximal=100)]
		)
		random_text3 = await generator.generate_phrase(
			validators=[validators.chars_count(minimal=1, maximal=100)]
		)
		random_text4 = await generator.generate_phrase(
			validators=[validators.chars_count(minimal=1, maximal=100)]
		)
		
		# Отправляем опрос
		await bot.send_poll(
			chat_id,
			random_text,
			[random_text2, random_text3, random_text4],
		)
	except Exception as e:
		logging.error(f"Ошибка при генерации опроса: {e}")

# Вспомогательная функция для генерации ответа
async def generate_response(database):
	"""
	Генерирует текстовый ответ на основе базы данных чата.
	
	Args:
		database: База данных чата с текстами
		
	Returns:
		str: Сгенерированный текст
	"""
	texts = database["textbase"]
	if len(texts) < 10:
		return "Недостаточно сообщений для генерации"
		
	generator = mc.PhraseGenerator(samples=texts)
	return await generator.generate_phrase(
		validators=[validators.words_count(minimal=1)]
	)

# Вспомогательная функция для генерации и отправки голосового сообщения
async def generate_and_send_voice(message, database):
	"""
	Генерирует и отправляет голосовое сообщение.
	
	Args:
		message: Объект сообщения
		database: База данных чата с текстами
	"""
	texts = database["textbase"]
	if len(texts) < 10:
		return
		
	generator = mc.PhraseGenerator(samples=texts)
	random_text = await generator.generate_phrase(
		validators=[validators.words_count(minimal=1)]
	)
	
	# Создаем временный файл для голосового сообщения
	random_file = f"random_voice_{random.randint(0, 10000000000000000000000000)}.mp3"
	try:
		tts = gTTS(text=random_text, lang="ru")
		tts.save(random_file)
		
		with open(random_file, "rb") as voice:
			await bot.send_voice(message.chat.id, voice)
			
	except Exception as e:
		logging.error(f"Ошибка при создании голосового сообщения: {e}")
	finally:
		# Удаляем временный файл
		if os.path.exists(random_file):
			os.remove(random_file)

# Helper function to find and load fonts with fallbacks
def get_font(font_name, size):
	"""
	Получает шрифт по имени и размеру, проверяя несколько возможных путей.
	
	Args:
		font_name (str): Имя файла шрифта
		size (int): Размер шрифта
		
	Returns:
		PIL.ImageFont: Объект шрифта или None в случае ошибки
	"""
	# Список возможных путей к шрифтам в порядке приоритета
	font_paths = [
		os.path.join("app", "media", "fonts", font_name),
		os.path.join("app", "media", "demotivators", "fonts", font_name),
		os.path.join("app", "fonts", font_name),
		os.path.join("fonts", font_name),
		os.path.join("demotivators", "fonts", font_name),
		font_name  # Попытка загрузить шрифт напрямую (системный шрифт)
	]
	
	# Проверяем каждый путь
	for path in font_paths:
		try:
			if os.path.exists(path):
				return ImageFont.truetype(path, size)
			logging.debug(f"Шрифт не найден по пути: {path}")
		except Exception as e:
			logging.debug(f"Ошибка при загрузке шрифта {path}: {e}")
	
	# Если ни один путь не сработал, пробуем загрузить системный шрифт
	try:
		# Попытка использовать стандартный шрифт
		default_font = ImageFont.load_default()
		logging.warning(f"Используется стандартный шрифт вместо {font_name}")
		return default_font
	except Exception as e:
		logging.error(f"Не удалось загрузить даже стандартный шрифт: {e}")
		return None

# Helper function to find image files with fallback
def get_image_path(image_name):
	# Primary path - app/media/images
	primary_path = os.path.join("app", "media", "images", image_name)
	if os.path.exists(primary_path):
		return primary_path
	
	# Fallback 1 - app/Images 
	fallback1 = os.path.join("app", "Images", image_name)
	if os.path.exists(fallback1):
		return fallback1
	
	# Fallback 2 - Images (legacy)
	fallback2 = os.path.join("Images", image_name)
	if os.path.exists(fallback2):
		return fallback2
		
	# If image doesn't exist in any location, return primary path anyway
	# (this will likely cause an error, but maintains backward compatibility)
	logging.warning(f"Image not found: {image_name}")
	return primary_path

# Функция для очистки временных файлов
def cleanup_temp_files():
	"""Удаляет временные файлы, которые могли остаться от предыдущих запусков."""
	patterns = [
		'random_voice_*.mp3',
		'result_*.jpg',
		'input_*.jpg',
		'quote_*.png',
		'pictext_*.png',
		'*_dem.jpg',
		'*_quote.png',
	]
	
	for pattern in patterns:
		try:
			for file in glob.glob(pattern):
				try:
					if os.path.exists(file):
						os.remove(file)
						logging.info(f"Deleted temp file: {file}")
				except Exception as e:
					logging.error(f"Failed to delete temp file {file}: {e}")
			
			# Также проверяем в директории временных файлов
			temp_dir = os.path.join("app", "media", "temp")
			for file in glob.glob(os.path.join(temp_dir, pattern)):
				try:
					if os.path.exists(file):
						os.remove(file)
						logging.info(f"Deleted temp file: {file}")
				except Exception as e:
					logging.error(f"Failed to delete temp file {file}: {e}")
		except Exception as e:
			logging.error(f"Error cleaning up temp files with pattern {pattern}: {e}")

# Функция для периодических задач
async def scheduled_tasks():
	"""
	Выполняет периодические задачи:
	- Оптимизация базы данных каждые 12 часов
	- Очистка временных файлов каждые 6 часов
	"""
	while True:
		try:
			# Ждем 6 часов
			await asyncio.sleep(6 * 60 * 60)
			
			# Очистка временных файлов
			cleanup_temp_files()
			logging.info("Выполнена плановая очистка временных файлов")
			
			# Оптимизация базы данных каждые 12 часов
			if int(time.time()) % (12 * 60 * 60) < 6 * 60 * 60:
				try:
					db.optimize_database()
					logging.info("Выполнена плановая оптимизация базы данных")
				except Exception as e:
					logging.error(f"Ошибка при плановой оптимизации базы данных: {e}")
		except Exception as e:
			logging.error(f"Ошибка в планировщике задач: {e}")
			await asyncio.sleep(60)  # Ждем минуту перед повторной попыткой

async def on_shutdown(dp):
	"""
	Выполняется при остановке бота.
	"""
	# Очистка временных файлов
	cleanup_temp_files()
	
	# Закрытие соединений с базой данных
	try:
		# В модуле database нет метода close(),
		# соединения закрываются автоматически через контекстные менеджеры
		logging.info("Соединения с базой данных будут закрыты автоматически")
	except Exception as e:
		logging.error(f"Ошибка при закрытии соединений с базой данных: {e}")
	
	# Остановка планировщика
	for task in asyncio.all_tasks():
		if task != asyncio.current_task():
			task.cancel()
	
	logging.info("Бот остановлен")

# Инициализация базы данных и оптимизации
async def on_startup(dp):
	# Ensure all required directories exist
	dirs_to_create = [
		os.path.join("app", "media", "fonts"),
		os.path.join("app", "media", "temp"),
		os.path.join("app", "media", "demotivators", "fonts"),
		os.path.join("app", "media", "images"),
		os.path.join("app", "database"),
		os.path.join("app", "logs")
	]
	
	for directory in dirs_to_create:
		try:
			if not os.path.exists(directory):
				os.makedirs(directory, exist_ok=True)
				logging.info(f"Created directory: {directory}")
		except Exception as e:
			logging.error(f"Failed to create directory {directory}: {e}")
	
	# Инициализируем временную директорию для новой библиотеки 
	await init_temp_directories()
	
	# Ensure premium.txt exists
	premium_file = os.path.join("app", "premium.txt")
	if not os.path.exists(premium_file):
		try:
			with open(premium_file, "w") as f:
				f.write("# List of premium chat IDs\n# Add one chat ID per line\n")
			logging.info(f"Created file: {premium_file}")
		except Exception as e:
			logging.error(f"Failed to create premium.txt: {e}")
	
	# Initialize and optimize database
	try:
		db.init_db()
		logging.info("База данных инициализирована")
	except Exception as e:
		logging.error(f"Ошибка инициализации базы данных: {e}")
	
	try:
		db.optimize_database()
		logging.info("Выполнена оптимизация базы данных")
	except Exception as e:
		logging.error(f"Ошибка оптимизации базы данных: {e}")
	
	# Clean up temporary files
	cleanup_temp_files()
	
	# Start scheduled tasks
	asyncio.create_task(scheduled_tasks())
	
	# Register all commands with BotFather
	commands = [
		types.BotCommand(command="help", description="Помощь и список команд"),
		types.BotCommand(command="info", description="Информация о боте"),
		types.BotCommand(command="premium", description="Проверить премиум-статус чата"),
		types.BotCommand(command="settings", description="Настройки бота"),
		types.BotCommand(command="gen", description="Генерация случайной фразы"),
		types.BotCommand(command="gendem", description="Генерация демотиватора"),
		types.BotCommand(command="genmem", description="Генерация мема"),
		types.BotCommand(command="genvoice", description="Генерация голосового сообщения"),
		types.BotCommand(command="genanek", description="Генерация анекдота"),
		types.BotCommand(command="gendialogue", description="Генерация диалога"),
		types.BotCommand(command="genpoem", description="Генерация стихотворения"),
		types.BotCommand(command="genbugurt", description="Генерация бугурта"),
		types.BotCommand(command="gensyntax", description="Генерация с правильным синтаксисом"),
		types.BotCommand(command="gensymbols", description="Генерация текста определенной длины"),
		types.BotCommand(command="genlong", description="Генерация длинного текста"),
		types.BotCommand(command="genpoll", description="Генерация опроса"),
		types.BotCommand(command="quote", description="Создание цитаты"),
		types.BotCommand(command="choice", description="Выбрать один из вариантов"),
		types.BotCommand(command="cont", description="Продолжить фразу"),
		types.BotCommand(command="wipe", description="Очистка базы данных"),
		types.BotCommand(command="checkfonts", description="Проверка доступности шрифтов (админ)"),
	]
	
	try:
		await bot.set_my_commands(commands)
		logging.info("Bot commands have been successfully registered with BotFather")
	except Exception as e:
		logging.error(f"Failed to register bot commands: {e}")
	
	# Get bot info and log startup
	try:
		bot_info = await bot.get_me()
		logging.info(f"Бот запущен: @{bot_info.username}")
	except Exception as e:
		logging.info(f"Бот запущен")
		logging.error(f"Не удалось получить информацию о боте: {e}")

# Инициализировать необходимые директории
async def init_temp_directories():
    """
    Создает необходимые временные директории для работы с демотиваторами, цитатами и т.п.
    """
    temp_dir = os.path.join("app", "media", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

# Другие вспомогательные функции для работы с путями
def get_temp_filename(prefix="temp", extension="jpg"):
    """Создает случайное имя файла для временных изображений"""
    random_id = random.randint(0, 10000000000000000000000000)
    return f"{prefix}_{random_id}.{extension}"

@dp.message_handler(commands="checkfonts", chat_type=["private", "group", "supergroup"])
async def check_fonts(message: types.Message):
	"""
	Команда для проверки доступности шрифтов, используемых в боте.
	Полезна для диагностики проблем с генерацией изображений.
	"""
	if message.from_user.id != admin:
		await message.reply("Эта команда доступна только администратору.")
		return
	
	font_paths = [
		os.path.join(os.path.dirname(os.path.dirname(__file__)), "simpledemotivators_2_0", "Formular-BlackItalic.ttf"),
		os.path.join(os.path.dirname(os.path.dirname(__file__)), "simpledemotivators_2_0", "Formular-Italic.ttf"),
		os.path.join(os.path.dirname(os.path.dirname(__file__)), "simpledemotivators_2_0", "Impact.ttf")
	]
	
	results = []
	for path in font_paths:
		if os.path.exists(path):
			results.append(f"✅ {os.path.basename(path)} - найден")
		else:
			results.append(f"❌ {os.path.basename(path)} - НЕ найден")
	
	# Проверка доступа к директории временных файлов
	temp_dir = os.path.join("app", "media", "temp")
	if os.path.exists(temp_dir) and os.access(temp_dir, os.W_OK):
		results.append(f"✅ Директория для временных файлов доступна для записи: {temp_dir}")
	else:
		results.append(f"❌ Проблема с доступом к директории для временных файлов: {temp_dir}")
	
	await message.reply("\n".join(results))

# Запуск бота
if __name__ == "__main__":
	executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
