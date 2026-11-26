# -*- coding: utf-8 -*-
# Сгенерировано компилятором TeleLang (Ядро проекта)
import os
import sys
from pathlib import Path
import aiosqlite
from aiogram.fsm.state import State, StatesGroup

# Определение путей базы данных
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'database' / 'bot.db'

class _DotDict(dict):
    def __getattr__(self, name):
        val = self.get(name)
        if isinstance(val, dict):
            return _DotDict(val)
        return val
    def __setattr__(self, name, value):
        self[name] = value

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

class _TeleStates(StatesGroup):
    pass

async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, coins REAL DEFAULT 0, name TEXT DEFAULT '')')
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
        await db.execute('INSERT INTO users (user_id, ' + field + ') VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET ' + field + ' = excluded.' + field, (user_id, value))
        await db.commit()

async def _update_user_db(user_id: int, field: str, delta):
    curr = await _get_user_db(user_id, field, 0)
    await _set_user_db(user_id, field, curr + delta)
