# -*- coding: utf-8 -*-
# Сгенерировано компилятором TeleLang: модуль 'start'
import os
import sys
from pathlib import Path
import aiosqlite
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext

from core import _CtxUser, _CtxMsg, _CtxChat, _DotDict, _TeleStates, DB_PATH, _get_user_db, _set_user_db, _update_user_db

router = Router(name='start')

@router.message(Command('start'))
async def _handle_cmd_start_0(message: types.Message, state: FSMContext = None):
    _msg_target = message
    user = _CtxUser(message.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(message.chat)
    _kb_builder = []
    _kb_builder.append([InlineKeyboardButton(text='🛒 Каталог товаров', callback_data='btn_show_catalog_3')])
    _kb_builder.append([InlineKeyboardButton(text='💰 Мой баланс', callback_data='btn_show_balance_4')])
    _kb_builder.append([InlineKeyboardButton(text='🌐 Telegram', url='https://telegram.org')])
    _keyboard = InlineKeyboardMarkup(inline_keyboard=_kb_builder)
    await _msg_target.answer(f'👋 Привет, {user.name}!\nДобро пожаловать в модульный магазин на TeleLang.', reply_markup=_keyboard)

@router.callback_query(F.data == 'btn_show_catalog_1')
async def _cb_btn_show_catalog_1(callback: types.CallbackQuery, state: FSMContext = None):
    await callback.answer()
    _msg_target = callback.message
    user = _CtxUser(callback.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(callback.message.chat if callback.message else None)
    await show_catalog(_msg_target=_msg_target, _user=user)

@router.callback_query(F.data == 'btn_show_balance_2')
async def _cb_btn_show_balance_2(callback: types.CallbackQuery, state: FSMContext = None):
    await callback.answer()
    _msg_target = callback.message
    user = _CtxUser(callback.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(callback.message.chat if callback.message else None)
    await show_balance(_msg_target=_msg_target, _user=user)

@router.callback_query(F.data == 'btn_show_catalog_3')
async def _cb_btn_show_catalog_3(callback: types.CallbackQuery, state: FSMContext = None):
    await callback.answer()
    _msg_target = callback.message
    user = _CtxUser(callback.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(callback.message.chat if callback.message else None)
    await show_catalog(_msg_target=_msg_target, _user=user)

@router.callback_query(F.data == 'btn_show_balance_4')
async def _cb_btn_show_balance_4(callback: types.CallbackQuery, state: FSMContext = None):
    await callback.answer()
    _msg_target = callback.message
    user = _CtxUser(callback.from_user)
    user.coins = await _get_user_db(user.id, 'coins', 0)
    chat = _CtxChat(callback.message.chat if callback.message else None)
    await show_balance(_msg_target=_msg_target, _user=user)
