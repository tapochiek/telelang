# -*- coding: utf-8 -*-
# Сгенерировано компилятором TeleLang: модуль 'shop'
import os
import sys
from pathlib import Path
import aiosqlite
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext

from core import _CtxUser, _CtxMsg, _CtxChat, _DotDict, _TeleStates, DB_PATH, _get_user_db, _set_user_db, _update_user_db

router = Router(name='shop')

async def show_catalog(_msg_target=None, _user=None):
    user = _user if _user is not None else (_CtxUser(_msg_target.from_user) if _msg_target else _CtxUser(None))
    if user.id > 0:
        user.coins = await _get_user_db(user.id, 'coins', 0)
    message = _CtxMsg(_msg_target) if _msg_target else _CtxMsg(None)
    chat = _CtxChat(_msg_target.chat) if _msg_target else _CtxChat(None)
    await _msg_target.answer('📦 Доступные товары:\n1. 🌟 Премиум доступ — 100 монет\n2. 💎 VIP статус — 500 монет\n\nИспользуйте команду /buy для оформления.')

async def show_balance(_msg_target=None, _user=None):
    user = _user if _user is not None else (_CtxUser(_msg_target.from_user) if _msg_target else _CtxUser(None))
    if user.id > 0:
        user.coins = await _get_user_db(user.id, 'coins', 0)
    message = _CtxMsg(_msg_target) if _msg_target else _CtxMsg(None)
    chat = _CtxChat(_msg_target.chat) if _msg_target else _CtxChat(None)
    await _msg_target.answer(f'💰 Ваш текущий баланс: {user.coins} монет')

@router.message(Command('shop'))
async def _handle_cmd_shop_0(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    await show_catalog(_msg_target=_msg_target, _user=user)

@router.message(Command('balance'))
async def _handle_cmd_balance_1(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    await show_balance(_msg_target=_msg_target, _user=user)
