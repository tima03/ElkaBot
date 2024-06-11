from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from create_bot import bot, pg_db

start_router = Router()


@start_router.message()
async def bot_get_user_id(message: Message):
    user_ID = message.from_user.id
    user_NAME = message.from_user.username
    user_ISADMIN = False
    admin_list = await bot.get_chat_administrators(message.chat.id)
    for admin in admin_list:
        if (admin.user.id == user_ID):
            user_ISADMIN = True
            break
        else:
            user_ISADMIN = False
    if await pg_db.connect_by_link(): print("БД подключена")

    if await pg_db.disconnect(): print("БД отключена")

@start_router.message(F.text == '---sms')
async def bot_delete_message(message: Message):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
    await message.delete()