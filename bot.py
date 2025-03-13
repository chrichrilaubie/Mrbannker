import logging 
import os
import requests
import time
import string
import random
import yaml
import asyncio
import re

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import Throttled
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from bs4 import BeautifulSoup as bs

# Configure vars get from env or config.yml
CONFIG = yaml.load(open('config.yml', 'r'), Loader=yaml.SafeLoader)
TOKEN = os.getenv('TOKEN', CONFIG['token'])
BLACKLISTED = os.getenv('BLACKLISTED', CONFIG['blacklisted']).split()
PREFIX = os.getenv('PREFIX', CONFIG['prefix'])
OWNER = int(os.getenv('OWNER', CONFIG['owner']))
ANTISPAM = int(os.getenv('ANTISPAM', CONFIG['antispam']))

# Initialize bot and dispatcher (Ensure this happens before handlers)
storage = MemoryStorage()
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)

# Configure logging
logging.basicConfig(level=logging.INFO)

# BOT INFO
loop = asyncio.get_event_loop()

bot_info = loop.run_until_complete(bot.get_me())
BOT_USERNAME = bot_info.username
BOT_NAME = bot_info.first_name
BOT_ID = bot_info.id

# Your other code below (handlers, functions, etc.)
# For example:
@dp.message_handler(commands=['start', 'help'], commands_prefix=PREFIX)
async def helpstr(message: types.Message):
    # await message.answer_chat_action('typing')
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    btns = types.InlineKeyboardButton("Bot Source", url="https://github.com/chrichrilaubie/Mrbannker")
    keyboard_markup.row(btns)
    FIRST = message.from_user.first_name
    MSG = f'''
Hello {FIRST}, Im {BOT_NAME}
U can find my Boss  <a href="tg://user?id={OWNER}">HERE</a>
Cmds /chk /info /bin'''
    await message.answer(MSG, reply_markup=keyboard_markup,
                        disable_web_page_preview=True)

# Example /chk command handler
@dp.message_handler(commands=['chk'], commands_prefix=PREFIX)
async def ch(message: types.Message):
    await message.answer_chat_action('typing')
    tic = time.perf_counter()
    ID = message.from_user.id
    FIRST = message.from_user.first_name
    s = requests.Session()
    try:
        await dp.throttle('chk', rate=ANTISPAM)
    except Throttled:
        await message.reply('<b>Too many requests!</b>\n'
                            f'Blocked For {ANTISPAM} seconds')
    else:
        # Your card checking code here
        pass

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, loop=loop)
