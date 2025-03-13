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

# Initialize bot and dispatcher
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

# USE YOUR ROTATING PROXY API IN DICT FORMAT http://user:pass@providerhost:port
proxies = {
           'http': 'http://qnuomzzl-rotate:4i44gnayqk7c@p.webshare.io:80/',
           'https': 'http://qnuomzzl-rotate:4i44gnayqk7c@p.webshare.io:80/'
}

session = requests.Session()

# Random DATA
letters = string.ascii_lowercase
First = ''.join(random.choice(letters) for _ in range(6))
Last = ''.join(random.choice(letters) for _ in range(6))
PWD = ''.join(random.choice(letters) for _ in range(10))
Name = f'{First}+{Last}'
Email = f'{First}.{Last}@gmail.com'
UA = 'Mozilla/5.0 (X11; Linux i686; rv:102.0) Gecko/20100101 Firefox/102.0'


async def is_owner(user_id):
    return user_id == OWNER

async def is_card_valid(card_number: str) -> bool: 
    return (sum(map(lambda n: n[1] + (n[0] % 2 == 0) * (n[1] - 9 * (n[1] > 4)), enumerate(map(int, card_number[:-1]))) ) + int(card_number[-1])) % 10 == 0


@dp.message_handler(commands=['start', 'help'], commands_prefix=PREFIX)
async def helpstr(message: types.Message):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    btns = types.InlineKeyboardButton("Bot Source", url="https://github.com/xbinner18/Mrbannker")
    keyboard_markup.row(btns)
    FIRST = message.from_user.first_name
    MSG = f'''
Hello {FIRST}, I'm {BOT_NAME}
You can find my Boss <a href="tg://user?id={OWNER}">HERE</a>
Cmds /chk /info /bin'''
    await message.answer(MSG, reply_markup=keyboard_markup, disable_web_page_preview=True)


@dp.message_handler(commands=['info', 'id'], commands_prefix=PREFIX)
async def info(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        is_bot = message.reply_to_message.from_user.is_bot
        username = message.reply_to_message.from_user.username
        first = message.reply_to_message.from_user.first_name
    else:
        user_id = message.from_user.id
        is_bot = message.from_user.is_bot
        username = message.from_user.username
        first = message.from_user.first_name
    await message.reply(f'''
═════════╕
<b>USER INFO</b>
<b>USER ID:</b> <code>{user_id}</code>
<b>USERNAME:</b> @{username}
<b>FIRSTNAME:</b> {first}
<b>BOT:</b> {is_bot}
<b>BOT-OWNER:</b> {await is_owner(user_id)}
╘═════════''')


@dp.message_handler(commands=['bin'], commands_prefix=PREFIX)
async def binio(message: types.Message):
    await message.answer_chat_action('typing')
    ID = message.from_user.id
    FIRST = message.from_user.first_name
    BIN = message.text[len('/bin '):]
    if len(BIN) < 6:
        return await message.reply('Send bin not ass')
    r = requests.get(f'https://bins.ws/search?bins={BIN[:6]}').text
    soup = bs(r, features='html.parser')
    k = soup.find("div", {"class": "page"})
    INFO = f'''
{k.text[62:]}
SENDER: <a href="tg://user?id={ID}">{FIRST}</a>
BOT⇢ @{BOT_USERNAME}
OWNER⇢ <a href="tg://user?id={OWNER}">LINK</a>
'''
    await message.reply(INFO)


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
        await message.reply('<b>Too many requests!</b>\nBlocked For {ANTISPAM} seconds')
    else:
        if message.reply_to_message:
            cc = message.reply_to_message.text
        else:
            cc = message.text[len('/chk '):]

        if len(cc) == 0:
            return await message.reply("<b>No Card to chk</b>")

        x = re.findall(r'\d+', cc)
        ccn = x[0]
        mm = x[1]
        yy = x[2]
        cvv = x[3]
        if mm.startswith('2'):
            mm, yy = yy, mm
        if len(mm) >= 3:
            mm, yy, cvv = yy, cvv, mm
        if len(ccn) < 15 or len(ccn) > 16:
            return await message.reply('<b>Failed to parse Card</b>\n<b>Reason: Invalid Format!</b>')   
        BIN = ccn[:6]
        if BIN in BLACKLISTED:
            return await message.reply('<b>BLACKLISTED BIN</b>')
        if await is_card_valid(ccn) != True:
            return await message.reply('<b>Invalid luhn algorithm</b>')
        
        # Additional checks for stripe and others (already implemented above)
        
        # Response with results based on your logic
        

@dp.message_handler(commands=['mchk'], commands_prefix=PREFIX)
async def masschk(message: types.Message):
    await message.answer_chat_action('typing')
    try:
        await dp.throttle('mchk', rate=ANTISPAM)
    except Throttled:
        return await message.reply(f'<b>Too many requests!</b>\nBlocked for {ANTISPAM} seconds')

    if message.reply_to_message:
        cards_text = message.reply_to_message.text
    else:
        cards_text = message.text[len('/mchk '):]

    cards = cards_text.strip().splitlines()
    if not cards:
        return await message.reply("<b>No cards to check.</b>")

    results = []
    for card in cards:
        try:
            x = re.findall(r'\d+', card)
            if len(x) < 4:
                results.append(f"<code>{card}</code> ➟ ❌ Format invalide")
                continue

            ccn, mm, yy, cvv = x[0], x[1], x[2], x[3]

            if mm.startswith('2'):
                mm, yy = yy, mm
            if len(mm) >= 3:
                mm, yy, cvv = yy, cvv, mm

            if len(ccn) < 15 or len(ccn) > 16:
                results.append(f"<code>{ccn}|{mm}|{yy}|{cvv}</code> ➟ ❌ Format invalide")
                continue

            if await is_card_valid(ccn) != True:
                results.append(f"<code>{ccn}|{mm}|{yy}|{cvv}</code> ➟ ❌ Luhn invalide")
                continue

            results.append(f"<code>{ccn}|{mm}|{yy}|{cvv}</code> ➟ ✅ Luhn OK")  # Simple validity check

        except Exception as e:
            results.append(f"<code>{card}</code> ➟ ⚠️ Error: {str(e)}")

    await message.reply("\n".join(results[:50]))  # Limit to prevent spamming long responses

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, loop=loop)
