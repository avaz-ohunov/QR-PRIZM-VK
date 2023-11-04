# Bot.py

from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, EMPTY_KEYBOARD
from vkbottle import PhotoMessageUploader
from vkbottle import BaseStateGroup
from vkbottle import CtxStorage
from BotToken import bot_token
import importlib
import curs, curs_usd
from qrgenerator import qr_generate_transactions, qr_generate_personal
from headline import create_headline
import os
from datetime import datetime


# Регистрация бота
bot = Bot(token = bot_token)
ctx = CtxStorage()


# Кнопка "Создать QR-код"
kb_default = Keyboard()
kb_default.add(Text("Создать свой QR-код"), color = KeyboardButtonColor.PRIMARY)
kb_default.row()
kb_default.add(Text("Создать QR-код для транзакции"))

# Кнопка "Отмена"
kb_cancel = Keyboard()
kb_cancel.add(Text("Отмена"), color = KeyboardButtonColor.NEGATIVE)

# Кнопки "Отмена" и "Пропустить"
kb_cancel_continue = Keyboard()
kb_cancel_continue.add(Text("Отмена"), color = KeyboardButtonColor.NEGATIVE)
kb_cancel_continue.add(Text("Пропустить"))

# Кнопки с выбором валют
kb_currencies = Keyboard()
kb_currencies.add(Text("Ввести в рублях(₽)"), color = KeyboardButtonColor.POSITIVE)
kb_currencies.add(Text("Ввести в долларах($)"), color = KeyboardButtonColor.POSITIVE)
kb_currencies.row()
kb_currencies.add(Text("Отмена"), color = KeyboardButtonColor.NEGATIVE)
kb_currencies.add(Text("Пропустить"))


# Класс состояния генератора личного QR-кода
class GenerateQR(BaseStateGroup):
	get_data = 0


# Класс состояния получения реквизитов
class Requisites(BaseStateGroup):
	address = 1
	public_key = 2
	amount = 3
	amount_dollars = 4
	amount_rubles = 5
	comment = 6


# Состояние получения данных и генерация личного QR-кода
@bot.on.message(state = GenerateQR.get_data)
async def generate_personal_qr(message: Message):
	if message.text == "Отмена":
		await bot.state_dispenser.delete(message.peer_id)
		await message.answer("Создание QR-кода отменено", keyboard = kb_default)

	else:
		await message.answer("QR-код создаётся...", keyboard = EMPTY_KEYBOARD)
		qr_generate_personal(message.text, f"{message.peer_id}.png")

		photo_upd = PhotoMessageUploader(bot.api)
		photo = await photo_upd.upload(f"{message.peer_id}.png")
		await message.answer(attachment = photo, keyboard = kb_default)

		os.remove(f"{message.peer_id}.png")
		await bot.state_dispenser.delete(message.peer_id)


# Получение адреса кошелька
@bot.on.message(state = Requisites.address)
async def get_address(message: Message):
	if message.text == "Отмена":
		await bot.state_dispenser.delete(message.peer_id)
		await message.answer("Создание QR-кода отменено", keyboard = kb_default)

	else:
		ctx.set("address", message.text)
		await bot.state_dispenser.set(message.peer_id, Requisites.public_key)
		await message.answer("Его публичный ключ(Public key)", keyboard = kb_cancel_continue)


# Получение публичного ключа
@bot.on.message(state = Requisites.public_key)
async def get_public_key(message: Message):
	if message.text == "Пропустить":
		ctx.set("pk", "")
		await bot.state_dispenser.set(message.peer_id, Requisites.amount)
		await message.answer("Количество монет(Amount)", keyboard = kb_currencies)

	elif message.text == "Отмена":
		await bot.state_dispenser.delete(message.peer_id)
		await message.answer("Создание QR-кода отменено", keyboard = kb_default)

	else:
		ctx.set("pk", message.text)
		await bot.state_dispenser.set(message.peer_id, Requisites.amount)
		await message.answer("Количество монет(Amount)", keyboard = kb_currencies)


# Получение количества призм
@bot.on.message(state = Requisites.amount)
async def get_amount_prizms(message: Message):
	if message.text == "Пропустить":
		ctx.set("amount", "")
		await bot.state_dispenser.set(message.peer_id, Requisites.comment)
		await message.answer("Комментарий(Comment)", keyboard = kb_cancel_continue)

	elif message.text == "Отмена":
		await bot.state_dispenser.delete(message.peer_id)
		await message.answer("Создание QR-кода отменено", keyboard = kb_default)

	elif message.text == "Ввести в долларах($)":
		await bot.state_dispenser.set(message.peer_id, Requisites.amount_dollars)
		await message.answer("Введите сумму в долларах", keyboard = kb_cancel_continue)

	elif message.text == "Ввести в рублях(₽)":
		await bot.state_dispenser.set(message.peer_id, Requisites.amount_rubles)
		await message.answer("Введите сумму в рублях", keyboard = kb_cancel_continue)

	else:
		ctx.set("amount", message.text)
		await bot.state_dispenser.set(message.peer_id, Requisites.comment)
		await message.answer("Комментарий(Comment)", keyboard = kb_cancel_continue)


# Получение призм в долларах
@bot.on.message(state = Requisites.amount_dollars)
async def get_amount_dollars(message: Message):
	if message.text == "Пропустить":
		ctx.set("amount", "")
		await bot.state_dispenser.set(message.peer_id, Requisites.comment)
		await message.answer("Комментарий(Comment)", keyboard = kb_cancel_continue)

	elif message.text == "Отмена":
		await bot.state_dispenser.delete(message.peer_id)
		await message.answer("Создание QR-кода отменено", reply_markup = kb_default)

	else:
		importlib.reload(curs_usd)
		pzm = message.text
		try:
			amount = float(pzm) / float(curs_usd.pzm_curs)
			amount = round(amount, 2)
			ctx.set("amount", str(amount))
			await message.answer(f"${message.text} = {amount} PZM")
			await message.answer("Комментарий(Comment)")
			await bot.state_dispenser.set(message.peer_id, Requisites.comment)
		except:
			await message.answer("Введите только число")


# Получение призм в рублях
@bot.on.message(state = Requisites.amount_rubles)
async def get_amount_rubles(message: Message):
	if message.text == "Пропустить":
		ctx.set("amount", "")
		await bot.state_dispenser.set(message.peer_id, Requisites.comment)
		await message.answer("Комментарий(Comment)", keyboard = kb_cancel_continue)

	elif message.text == "Отмена":
		await bot.state_dispenser.delete(message.peer_id)
		await message.answer("Создание QR-кода отменено", reply_markup = kb_default)

	else:
		importlib.reload(curs_usd)
		pzm = message.text
		try:
			amount = float(pzm) / float(curs.pzm_curs)
			amount = round(amount, 2)
			ctx.set("amount", str(amount))
			await message.answer(f"₽{message.text} = {amount} PZM")
			await message.answer("Комментарий(Comment)")
			await bot.state_dispenser.set(message.peer_id, Requisites.comment)
		except:
			await message.answer("Введите только число")


# Получение комментария и генерация QR-кода
@bot.on.message(state = Requisites.comment)
async def generate_qr_for_transaction(message: Message):
	if message.text == "Пропустить":
		ctx.set("comment", "")

	elif message.text == "Отмена":
		await bot.state_dispenser.delete(message.peer_id)
		await message.answer("Создание QR-кода отменено", keyboard = kb_default)
		return None

	else:
		ctx.set("comment", message.text)
	
	await message.answer("QR-код создаётся...", keyboard = EMPTY_KEYBOARD)

	data_qr = {
		"address": "",
		"pk": "",
		"amount": "",
		"comment": ""
	}

	data_qr.update({"address": ctx.get("address")})
	data_qr.update({"pk": ctx.get("pk")})
	data_qr.update({"amount": ctx.get("amount")})
	data_qr.update({"comment": ctx.get("comment")})

	pzm_site = "https://wallet.prizm.space/?to="
	
	if data_qr["comment"] == "":
		qr_data = f"{pzm_site}{data_qr['address']}:{data_qr['pk']}:{data_qr['amount']}"
	else:
		qr_data = f"{pzm_site}{data_qr['address']}:{data_qr['pk']}:{data_qr['amount']}:{data_qr['comment']}"

	qr_generate_transactions(qr_data, f"{message.peer_id}.png")
	create_headline(data_qr["address"], message.peer_id)

	photo_upd = PhotoMessageUploader(bot.api)
	photo = await photo_upd.upload(f"{message.peer_id}.png")
	await message.answer(attachment = photo, keyboard = kb_default)


	os.remove(f"{message.peer_id}.png")

	ctx.delete("address")
	ctx.delete("pk")
	ctx.delete("amount")
	ctx.delete("comment")

	await bot.state_dispenser.delete(message.peer_id)


# Основной режим бота
@bot.on.message()
async def default(message: Message):
	if message.text.lower() == "prizm":		
		await message.answer("Бот активирован!", keyboard = kb_default)

	elif message.text == "Создать свой QR-код":
		await message.answer("Пришлите данные", keyboard = kb_cancel)
		await bot.state_dispenser.set(message.peer_id, GenerateQR.get_data)

	elif message.text == "Создать QR-код для транзакции":
		await message.answer("Пришлите адрес кошелька(Address)", keyboard = kb_cancel)
		await bot.state_dispenser.set(message.peer_id, Requisites.address)

	else:
		await message.answer("Пришлите мне одну из команд ниже👇", keyboard = kb_default)


time_now = datetime.today()
print(f"\n[{str(time_now)[:19]}]: Бот успешно запущен")

bot.run_forever()
