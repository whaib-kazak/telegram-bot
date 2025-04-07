import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.filters import Command
from datetime import timedelta
import logging

API_TOKEN = "7659082918:AAFT_OShwmoI_Ig0CZobNdlYSio03XztIfo"
GROUP_ID = -1002546585121  # ID вашей группы
ADMINS = [7110319196, 7544900244]  # ID админов

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

bot_enabled = True
message_count = {}
MESSAGE_LIMIT = 150

# Подсчет сообщений
@dp.message()
async def count_user_messages(message: Message):
    if not bot_enabled or message.chat.id != GROUP_ID:
        return
    user_id = message.from_user.id
    message_count[user_id] = message_count.get(user_id, 0) + 1

# Кнопки для админов
def action_buttons(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠ Варн", callback_data=f"warn_{user_id}")],
        [InlineKeyboardButton(text="🤐 Мут", callback_data=f"mute_{user_id}")],
        [InlineKeyboardButton(text="❌ Кик", callback_data=f"kick_{user_id}")],
        [InlineKeyboardButton(text="✅ Пропустить", callback_data=f"skip_{user_id}")]
    ])

# Команда для проверки активности
@dp.message(Command("check_activity"))
async def check_activity(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("У вас нет прав.")
        return

    if not message_count:
        await message.answer("Нет данных для проверки.")
        return

    for user_id, count in message_count.items():
        if count < MESSAGE_LIMIT:
            try:
                member = await bot.get_chat_member(GROUP_ID, user_id)
                username = member.user.full_name
                await message.answer(
                    f"{username} — {count} сообщений за неделю.",
                    reply_markup=action_buttons(user_id)
                )
            except Exception as e:
                print(f"Ошибка получения пользователя: {e}")

    message_count.clear()

# Обработка кнопок
@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    data = call.data
    action, user_id = data.split("_")
    user_id = int(user_id)
    member = await bot.get_chat_member(GROUP_ID, user_id)
    username = member.user.full_name

    if action == "warn":
        await bot.send_message(GROUP_ID, f"{username} получил предупреждение.")
    elif action == "mute":
        await bot.restrict_chat_member(
            GROUP_ID,
            user_id,
            ChatPermissions(can_send_messages=False),
            until_date=types.datetime.datetime.now() + timedelta(hours=12)
        )
        await bot.send_message(GROUP_ID, f"{username} замьючен на 12 часов.")
    elif action == "kick":
        await bot.ban_chat_member(GROUP_ID, user_id)
        await bot.send_message(GROUP_ID, f"{username} был кикнут.")
    elif action == "skip":
        await bot.send_message(GROUP_ID, f"{username} оставлен без наказания.")

    await call.answer("Готово")

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
