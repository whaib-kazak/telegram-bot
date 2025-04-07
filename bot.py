import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.filters import Command
from datetime import timedelta

API_TOKEN = '7659082918:AAFT_OShwmoI_Ig0CZobNdlYSio03XztIfo'
GROUP_ID = -1002546585121
ADMINS = [7544900244, 7110319196]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

message_count = {}
MESSAGE_LIMIT = 150
bot_enabled = False

# Кнопки действий
def get_action_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠ Варн", callback_data=f"warn_{user_id}")],
        [InlineKeyboardButton(text="🤐 Мут", callback_data=f"mute_{user_id}")],
        [InlineKeyboardButton(text="❌ Кик", callback_data=f"kick_{user_id}")],
        [InlineKeyboardButton(text="✅ Оставить", callback_data=f"skip_{user_id}")]
    ])

@dp.message(Command("startbot"))
async def cmd_startbot(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.reply("У вас нет прав.")
        return
    global bot_enabled
    bot_enabled = True
    await message.reply("Бот включен!")

@dp.message(Command("stopbot"))
async def cmd_stopbot(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.reply("У вас нет прав.")
        return
    global bot_enabled
    bot_enabled = False
    await message.reply("Бот выключен.")

@dp.message(F.chat.id == GROUP_ID)
async def count_messages(message: types.Message):
    if not bot_enabled:
        return
    user_id = message.from_user.id
    message_count[user_id] = message_count.get(user_id, 0) + 1

@dp.callback_query(F.data.startswith(("warn_", "mute_", "kick_", "skip_")))
async def process_action(callback: types.CallbackQuery):
    action, user_id = callback.data.split("_")
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
            until_date=timedelta(hours=12)
        )
        await bot.send_message(GROUP_ID, f"{username} замьючен на 12 часов.")
    elif action == "kick":
        await bot.ban_chat_member(GROUP_ID, user_id)
        await bot.send_message(GROUP_ID, f"{username} был удалён из группы.")
    elif action == "skip":
        await bot.send_message(GROUP_ID, f"{username} оставлен без наказания.")

    await callback.answer("Готово")

# Проверка активности (раз в день)
async def check_activity():
    if not bot_enabled or not message_count:
        return
    for admin_id in ADMINS:
        for user_id, count in message_count.items():
            if count < MESSAGE_LIMIT:
                try:
                    member = await bot.get_chat_member(GROUP_ID, user_id)
                    if member.status in ['left', 'kicked']:
                        continue
                    username = member.user.full_name
                    await bot.send_message(
                        admin_id,
                        f"{username} ({count} сообщений за неделю)",
                        reply_markup=get_action_keyboard(user_id)
                    )
                except Exception as e:
                    print(f"Ошибка: {e}")
    message_count.clear()

# Планировщик
async def activity_scheduler():
    while True:
        await asyncio.sleep(86400)  # Раз в день
        await check_activity()

async def main():
    asyncio.create_task(activity_scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
