# -*- coding: utf-8 -*-
# Сгенерировано компилятором TeleLang: модуль 'db'
import os
import sys
from pathlib import Path
import aiosqlite
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext

from core import _CtxUser, _CtxMsg, _CtxChat, _DotDict, _TeleStates, DB_PATH, _get_user_db, _set_user_db, _update_user_db

async def add_coins(amount, _msg_target=None, _user=None):
    user = _user if _user is not None else (_CtxUser(_msg_target.from_user) if _msg_target else _CtxUser(None))
    if user.id > 0:
        user.coins = await _get_user_db(user.id, 'coins', 0)
    message = _CtxMsg(_msg_target) if _msg_target else _CtxMsg(None)
    chat = _CtxChat(_msg_target.chat) if _msg_target else _CtxChat(None)
    await _update_user_db(user.id, 'coins', amount)
    await _msg_target.answer(f'✅ Ваш баланс пополнен на {amount} монет!')
