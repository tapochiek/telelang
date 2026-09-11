# -*- coding: utf-8 -*-
# Сгенерировано компилятором TeleLang. Не редактируйте вручную.
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger('MyBot')

router = Router()

@router.message(Command('start'))
async def _handle_cmd_start_0(message: types.Message):
    await message.answer('Привет!')

def create_bot(token: str) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp

async def run_bot(token: str) -> None:
    bot, dp = create_bot(token)
    logger.info('Запуск бота %r в режиме %r...', 'MyBot', 'polling')
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
