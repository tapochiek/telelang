# -*- coding: utf-8 -*-
# Агрегатор роутеров для пакета 'handlers'
from aiogram import Router
from .messages import router as messages_router

router = Router(name='handlers')
router.include_router(messages_router)

__all__ = ['router']