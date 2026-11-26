# -*- coding: utf-8 -*-
# Агрегатор роутеров для пакета 'commands'
from aiogram import Router
from .shop import router as shop_router
from .start import router as start_router

router = Router(name='commands')
router.include_router(shop_router)
router.include_router(start_router)

__all__ = ['router']