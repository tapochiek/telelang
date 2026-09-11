# -*- coding: utf-8 -*-
# Сгенерировано компилятором TeleLang: модуль 'messages'
import os
import sys
from pathlib import Path
import aiosqlite
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext

from core import _CtxUser, _CtxMsg, _CtxChat, _DotDict, _TeleStates, DB_PATH, _get_user_db, _set_user_db, _update_user_db

router = Router(name='messages')

@router.message()
async def _handle_on_message_0(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    if ('помощь' in message.text):
        await _msg_target.answer('💡 Подсказка: Нажмите /start или выберите /shop для просмотра товаров.')
