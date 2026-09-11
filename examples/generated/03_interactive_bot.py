# -*- coding: utf-8 -*-
# Сгенерировано компилятором TeleLang. Не редактируйте вручную.
import asyncio
import logging
import os
import sys
import time
from pathlib import Path
import aiohttp
import aiosqlite
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger('InteractiveBot')

router = Router()

# Утилиты данных и DotDict для API
class _DotDict(dict):
    def __getattr__(self, name):
        val = self.get(name)
        if isinstance(val, dict):
            return _DotDict(val)
        return val
    def __setattr__(self, name, value):
        self[name] = value

# Вспомогательные классы контекста TeleLang
class _CtxUser:
    def __init__(self, u):
        self.id = u.id if u else 0
        self.name = (u.full_name or '') if u else ''
        self.username = (u.username or '') if u else ''
        self.language = (u.language_code or '') if u else ''
        self.is_premium = bool(u.is_premium) if u else False
        self.coins = 0
    def __str__(self):
        return self.name

class _CtxMsg:
    def __init__(self, m):
        self.id = m.message_id if m else 0
        self.text = (m.text or '') if m else ''
        self.photo = bool(m.photo) if m else False
    def __str__(self):
        return self.text

class _CtxChat:
    def __init__(self, c):
        self.id = c.id if c else 0
        self.type = c.type if c else 'private'
    def __str__(self):
        return str(self.id)

DB_PATH = Path('database/bot.db')
async def _init_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, coins REAL DEFAULT 0, name TEXT DEFAULT \'\')')
        await db.execute('CREATE TABLE IF NOT EXISTS user_roles (user_id INTEGER, role TEXT, PRIMARY KEY(user_id, role))')
        await db.commit()

async def _get_user_db(user_id: int, field: str, default=0):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cur:
            row = await cur.fetchone()
            if row and field in row.keys():
                return row[field]
    return default

async def _set_user_db(user_id: int, field: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO users (user_id) VALUES (?) ON CONFLICT(user_id) DO NOTHING', (user_id,))
        await db.execute(f'UPDATE users SET {field} = ? WHERE user_id = ?', (value, user_id))
        await db.commit()

async def _update_user_db(user_id: int, field: str, delta):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO users (user_id) VALUES (?) ON CONFLICT(user_id) DO NOTHING', (user_id,))
        await db.execute(f'UPDATE users SET {field} = COALESCE({field}, 0) + ? WHERE user_id = ?', (delta, user_id))
        await db.commit()

async def show_profile(_msg_target=None, _user=None):
    user = _user if _user is not None else (_CtxUser(_msg_target.from_user) if _msg_target else _CtxUser(None))
    if user.id > 0:
        user.coins = await _get_user_db(user.id, 'coins', 0)
    message = _CtxMsg(_msg_target) if _msg_target else _CtxMsg(None)
    chat = _CtxChat(_msg_target.chat) if _msg_target else _CtxChat(None)
    await _msg_target.answer(f'👤 Твой профиль:\nИмя: {user.name}\nID: {user.id}\nUsername: @{user.username}')

async def show_shop(_msg_target=None, _user=None):
    user = _user if _user is not None else (_CtxUser(_msg_target.from_user) if _msg_target else _CtxUser(None))
    if user.id > 0:
        user.coins = await _get_user_db(user.id, 'coins', 0)
    message = _CtxMsg(_msg_target) if _msg_target else _CtxMsg(None)
    chat = _CtxChat(_msg_target.chat) if _msg_target else _CtxChat(None)
    await _msg_target.answer('🛒 Каталог товаров пока наполняется. Загляни позже!')

@router.message(Command('start'))
async def _handle_cmd_start_0(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    _kb_builder = []
    _kb_builder.append([InlineKeyboardButton(text='👤 Мой профиль', callback_data='btn_show_profile_1')])
    _kb_builder.append([InlineKeyboardButton(text='🛒 Магазин', callback_data='btn_show_shop_2')])
    _kb_builder.append([InlineKeyboardButton(text='🌐 Официальный сайт', url='https://telegram.org')])
    _keyboard = InlineKeyboardMarkup(inline_keyboard=_kb_builder)
    await _msg_target.answer(f'Привет, {user.name}! Выбери действие ниже:', reply_markup=_keyboard)

@router.message()
async def _handle_on_message_0(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    if (message.text == 'ping'):
        await _msg_target.answer('pong')
    else:
        if ('привет' in message.text):
            await _msg_target.answer(f'И тебе привет, {user.name}!')
        else:
            await _msg_target.answer(f'Ты написал: {message.text}')

@router.callback_query(F.data == 'btn_show_profile_1')
async def _cb_btn_show_profile_1(callback: types.CallbackQuery, state: FSMContext = None):
    await callback.answer()
    _msg_target = callback.message
    user = _CtxUser(callback.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(callback.message.chat if callback.message else None)
    await show_profile(_msg_target, _user=user)

@router.callback_query(F.data == 'btn_show_shop_2')
async def _cb_btn_show_shop_2(callback: types.CallbackQuery, state: FSMContext = None):
    await callback.answer()
    _msg_target = callback.message
    user = _CtxUser(callback.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(callback.message.chat if callback.message else None)
    await show_shop(_msg_target, _user=user)

def create_bot(token: str) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp

async def run_bot(token: str) -> None:
    await _init_database()
    bot, dp = create_bot(token)
    logger.info('Запуск бота %r в режиме %r...', 'InteractiveBot', 'polling')
    await dp.start_polling(bot)

if __name__ == '__main__':
    token = os.environ.get('BOT_TOKEN', '')
    if not token:
        logger.error('Переменная окружения BOT_TOKEN не найдена.')
        sys.exit(1)
    try:
        asyncio.run(run_bot(token))
    except (KeyboardInterrupt, SystemExit):
        logger.info('Работа бота остановлена.')
