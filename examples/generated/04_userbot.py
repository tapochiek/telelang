# -*- coding: utf-8 -*-
# Сгенерировано компилятором TeleLang (Userbot / Telethon). Не редактируйте вручную.
import asyncio
import logging
import os
import sys
from pathlib import Path
from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger('MyUserbot')

api_id = 123456
api_hash = '0123456789abcdef0123456789abcdef'
session_path = 'sessions/my_account'
Path(session_path).parent.mkdir(parents=True, exist_ok=True)
client = TelegramClient(session_path, api_id, api_hash)

# Контекстные классы для юзербота
class _CtxUser:
    def __init__(self, sender):
        self.id = sender.id if sender else 0
        first_name = getattr(sender, 'first_name', '') or ''
        last_name = getattr(sender, 'last_name', '') or ''
        self.name = f'{first_name} {last_name}'.strip()
        self.username = getattr(sender, 'username', '') or ''
        self.is_premium = bool(getattr(sender, 'premium', False))
    def __str__(self):
        return self.name

class _CtxMsg:
    def __init__(self, event):
        self.id = event.id if event else 0
        self.text = event.raw_text or ''
    def __str__(self):
        return self.text

@client.on(events.NewMessage)
async def _handle_on_message_0(event):
    _event = event
    sender = await event.get_sender()
    user = _CtxUser(sender)
    message = _CtxMsg(event)
    if (message.text == 'ping'):
        await _event.respond('pong')
    else:
        if (message.text == 'время'):
            await _event.respond('Бот на связи!')

async def run_userbot():
    logger.info('Запуск юзербота %r (Telethon MTProto)...', 'MyUserbot')
    await client.start()
    logger.info('Юзербот успешно подключён к Telegram!')
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(run_userbot())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Юзербот остановлен.')
