from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from create_bot import bot, pg_db
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
import re

start_router = Router()


def CheckIfUserIdInDB(user_ID):
    global temp_user_name
    global temp_user_isadmin
    if pg_db.connect_by_link(): print("БД подключена")
    try:
        pg_db.cursor.execute("""SELECT * FROM users WHERE userid = %s;""", [user_ID])
        record = pg_db.cursor.fetchone()
        if record is None:
            if pg_db.disconnect(): print("БД отключена")
            return False
        else:
            temp_user_name = record[1]
            temp_user_isadmin = record[2]
            if pg_db.disconnect(): print("БД отключена")
            return True
    except Exception as _ex:
        if pg_db.disconnect(): print("[INFO] Ошибка проверки ID пользователя в базе данных")
        return False


def CheckIfUserNameInDB(user_name):
    global temp_user_id
    if pg_db.connect_by_link(): print("БД подключена")
    try:
        pg_db.cursor.execute("""SELECT * FROM users WHERE LOWER(username) = LOWER(%s);""", [user_name])
        record = pg_db.cursor.fetchone()
        if record is None:
            if pg_db.disconnect(): print("БД отключена")
            return False
        else:
            temp_user_id = record[0]
            if pg_db.disconnect(): print("БД отключена")
            return True
    except Exception as _ex:
        if pg_db.disconnect(): print("[INFO] Ошибка проверки ника пользователя в базе данных")
        return False


async def extract_nickname_ban(text, chat_id):
    result = re.search(r'ban\s+@(\w+)', text, re.IGNORECASE)
    if result:
        nickname = result.group(1)
        if nickname.isalnum():
            if nickname.isdigit():
                if (CheckIfUserIdInDB(nickname)):
                    await bot.ban_chat_member(chat_id, nickname)
                    return str(nickname) + " is banned"
            else:
                if (CheckIfUserNameInDB(nickname)):
                    await bot.ban_chat_member(chat_id, temp_user_id)
                    return str(nickname) + " is banned"
        else:
            return "Nickname can contain only latter's and digits"
    else:
        return "No nickname found in the text"


async def extract_nickname_unban(text, chat_id):
    result = re.search(r'unban\s+@(\w+)', text, re.IGNORECASE)
    if result:
        nickname = result.group(1)
        if nickname.isalnum():
            if nickname.isdigit():
                if (CheckIfUserIdInDB(nickname)):
                    await bot.unban_chat_member(chat_id, nickname)
                    return str(nickname) + " is unbanned"
            else:
                if (CheckIfUserNameInDB(nickname)):
                    await bot.unban_chat_member(chat_id, temp_user_id)
                    return str(nickname) + " is unbanned"
        else:
            return "Nickname can contain only latter's and digits"
    else:
        return "No nickname found in the text"


def RequestFromAdmin(userid):
    if pg_db.connect_by_link(): print("БД подключена")
    try:
        pg_db.cursor.execute("""SELECT * FROM users WHERE userid = %s;""", [userid])
        record = pg_db.cursor.fetchone()
        if record[2]:
            if pg_db.disconnect(): print("БД отключена")
            return True
        else:
            if pg_db.disconnect(): print("БД отключена")
            return False
    except Exception as _ex:
        if pg_db.disconnect(): print("[INFO] Ошибка в определении прав администратора")
        return False


def InsertNewUserInDB(user_ID, user_NAME, user_ISADMIN):
    if pg_db.connect_by_link(): print("БД подключена")
    pg_db.conn.autocommit = True
    sql_insert_query = """INSERT INTO users (userid, username, userisadmin) VALUES (%s, %s, %s); """
    insert_tuple = (user_ID, user_NAME, user_ISADMIN)
    try:
        pg_db.cursor.execute(sql_insert_query, insert_tuple)
        if pg_db.disconnect(): print("БД отключена")
    except Exception as _ex:
        if pg_db.disconnect(): print("[INFO] Ошибка добавления пользователя в базу данных")


def UpdateUserInDatabase(user_id, user_name, user_isadmin):
    if pg_db.connect_by_link(): print("БД подключена")
    pg_db.conn.autocommit = True
    sql_insert_query = """UPDATE users SET username = %s, userisadmin = %s WHERE userid = %s; """
    insert_tuple = (user_name, user_isadmin, user_id)
    try:
        pg_db.cursor.execute(sql_insert_query, insert_tuple)
        temp_user_name = None
        temp_user_isadmin = None
        if pg_db.disconnect(): print("Бд отключена")
    except Exception as _ex:
        if pg_db.disconnect(): print("[INFO] Ошибка обновления данных пользователя в бд")


@start_router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def new_member(event: ChatMemberUpdated):
    await event.answer(f"<b>Hi, {event.new_chat_member.user.first_name}!</b>",
                       parse_mode="HTML")
    user_ID = event.new_chat_member.user.id
    user_NAME = event.new_chat_member.user.username
    if user_NAME == None:
        user_NAME = str(user_ID)
    user_ISADMIN = False
    admin_list = await bot.get_chat_administrators(event.chat.id)
    for admin in admin_list:
        if (admin.user.id == user_ID):
            user_ISADMIN = True
            break
        else:
            user_ISADMIN = False
    if not CheckIfUserIdInDB(user_ID):
        InsertNewUserInDB(user_ID, user_NAME, user_ISADMIN)
    else:
        if (temp_user_name != user_NAME or temp_user_isadmin != user_ISADMIN):
            UpdateUserInDatabase(user_ID, user_NAME, user_ISADMIN)


@start_router.message(F.text == '-sms')
async def sms_delete(message: Message):
    if RequestFromAdmin(message.from_user.id):
        await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
        await message.delete()


@start_router.message(F.text.startswith('ban') | F.text.startswith('!ban') | F.text.startswith('Ban'))
async def user_ban(message: Message):
    if RequestFromAdmin(message.from_user.id):
        try:
            await message.answer(await extract_nickname_ban(message.text, message.chat.id))
        except Exception as _ex:
            print("Возможно, такого пользователя нет в бд или другая ошибка")


@start_router.message(F.text.startswith('unban') | F.text.startswith('!unban') | F.text.startswith('Unban'))
async def user_unban(message: Message):
    if RequestFromAdmin(message.from_user.id):
        try:
            await message.answer(await extract_nickname_unban(message.text, message.chat.id))
        except Exception as _ex:
            print("Возможно, такого пользователя нет в бд или другая ошибка")


@start_router.message()
async def bot_get_user_id(message: Message):
    user_ID = message.from_user.id
    user_NAME = message.from_user.username
    if user_NAME == None:
        user_NAME = str(user_ID)
    user_ISADMIN = False
    admin_list = await bot.get_chat_administrators(message.chat.id)
    for admin in admin_list:
        if (admin.user.id == user_ID):
            user_ISADMIN = True
            break
        else:
            user_ISADMIN = False
    if not CheckIfUserIdInDB(user_ID):
        InsertNewUserInDB(user_ID, user_NAME, user_ISADMIN)
    else:
        if (temp_user_name != user_NAME or temp_user_isadmin != user_ISADMIN):
            UpdateUserInDatabase(user_ID, user_NAME, user_ISADMIN)
