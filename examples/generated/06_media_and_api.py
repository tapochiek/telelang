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
logger = logging.getLogger('MediaAndApiBot')

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

async def _call_api_weather(params: dict) -> _DotDict:
    async with aiohttp.ClientSession() as session:
        url = ''
        headers = {}
        async with session.get(url, params=params, headers=headers) as resp:
            try:
                data = await resp.json()
                return _DotDict(data)
            except Exception:
                text = await resp.text()
                return _DotDict({'text': text})

from aiogram import BaseMiddleware
class _HookMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        _msg_target = event if isinstance(event, types.Message) else getattr(event, 'message', None)
        user = _CtxUser(event.from_user)
        chat = _CtxChat(_msg_target.chat if _msg_target else None)
        _start_time = time.perf_counter()
        logger.info(f'Новый запрос от пользователя {user.id}')
        result = await handler(event, data)
        elapsed_ms = int((time.perf_counter() - _start_time) * 1000)
        logger.info(f'Запрос пользователя {user.id} обработан за {elapsed_ms}ms')
        return result

router.message.middleware(_HookMiddleware())

@router.error()
async def _handle_global_error(event: types.ErrorEvent):
    error = event.exception
    _msg_target = event.update.message if event.update else None
    user = _CtxUser(_msg_target.from_user if _msg_target else None)
    logger.error(error)
    await _msg_target.answer('Произошла ошибка, попробуйте позже.')

@router.message(Command('start'))
async def _handle_cmd_start_0(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    await _msg_target.answer('Привет! Доступные команды:\n/photo — отправить фото\n/circle — отправить видео-кружок\n/doc — отправить документ\n/weather — прогноз погоды')

@router.message(Command('photo'))
async def _handle_cmd_photo_1(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    await _msg_target.answer_photo(FSInputFile('assets/example.jpg'), caption='Демо-изображение из TeleLang')

@router.message(Command('circle'))
async def _handle_cmd_circle_2(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    await _msg_target.answer_video_note(FSInputFile('assets/circle.mp4'))

@router.message(Command('doc'))
async def _handle_cmd_doc_3(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    await _msg_target.answer_document(FSInputFile('assets/document.pdf'), caption='Ваш отчёт')

@router.message(Command('weather'))
async def _handle_cmd_weather_4(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    result = await _call_api_weather({'latitude': '55.75', 'longitude': '37.62', 'current_weather': 'true'})
    await _msg_target.answer('Погода в Москве получена через API!')

def create_bot(token: str) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp

async def run_bot(token: str) -> None:
    await _init_database()
    bot, dp = create_bot(token)
    logger.info('Запуск бота %r в режиме %r...', 'MediaAndApiBot', 'polling')
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
