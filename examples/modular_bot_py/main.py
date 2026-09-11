# -*- coding: utf-8 -*-
# Главная точка входа бота 'ModularShopBot'
# Сгенерировано компилятором TeleLang
import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from core import init_db

from commands import router as commands_router
from handlers import router as handlers_router

# Загрузка переменных окружения из .env
load_dotenv()

TOKEN = os.environ.get('BOT_TOKEN', '123456789:ABCdefGHIjklMNOpqrsTUVwxyz')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')
logger = logging.getLogger('ModularShopBot')

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(commands_router)
dp.include_router(handlers_router)

async def on_startup():
    await init_db()
    logger.info('Бот ModularShopBot успешно инициализирован и готов к работе!')

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Бот остановлен.')
