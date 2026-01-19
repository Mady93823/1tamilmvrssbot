import os
import time
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import logging
import asyncio
import threading
from pyrogram import Client
from .downloader import download_and_upload


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
# ============ WOODctaft =================
TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
TAMILMV_URL = os.getenv('TAMILMV_URL', 'https://www.1tamilmv.do')
PORT = int(os.getenv('PORT', 3000))
# ========================================
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# Flask app
app = Flask(__name__)

# Global variables
movie_list = []
real_dict = {}

# Global variables
movie_list = []
real_dict = {}

# Initialize Pyrogram
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
p_client = None
pyro_loop = asyncio.new_event_loop()


def start_pyro_thread():
    asyncio.set_event_loop(pyro_loop)
    global p_client
    if api_id and api_hash:
        try:
            p_client = Client(
                "my_bot",
                api_id=api_id,
                api_hash=api_hash,
                bot_token=TOKEN)
            pyro_loop.run_until_complete(p_client.start())
            logger.info("Pyrogram Client Started in Background Loop")
        except Exception as e:
            logger.error(f"Pyrogram Error: {e}")
    pyro_loop.run_forever()


# Start Async Worker Thread
threading.Thread(target=start_pyro_thread, daemon=True).start()

# /start command


@bot.message_handler(commands=['start'])
def random_answer(message):
    text_message = """<b>Hello 👋</b>

<blockquote><b>🎬 Get latest Movies from 1Tamilmv</b></blockquote>

⚙️ <b>How to use me??</b> 🤔

✯ Please enter /view command and you'll get magnet link as well as link to torrent file 😌

<blockquote><b>🔗 Share and Support 💝</b></blockquote>"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            '🔗 GitHub 🔗',
            url='https://github.com/SudoR2spr'),
        types.InlineKeyboardButton(
            text="⚡ Powered By",
            url='https://t.me/Opleech_WD'))

    bot.send_photo(
        chat_id=message.chat.id,
        photo='https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg',
        caption=text_message,
        reply_markup=keyboard
    )

# /view command


@bot.message_handler(commands=['view'])
def start(message):
    bot.send_message(message.chat.id, "<b>🧲 Please wait for 10 ⏰ seconds</b>")
    global movie_list, real_dict
    movie_list, real_dict = tamilmv()

    combined_caption = """<b><blockquote>🔗 Select a Movie from the list 🎬</blockquote></b>\n\n🔘 Please select a movie:"""
    keyboard = makeKeyboard(movie_list)

    bot.send_photo(
        chat_id=message.chat.id,
        photo='https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg',
        caption=combined_caption,
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global real_dict

    # Handle Download Button
    if call.data.startswith('down_'):
        if not p_client:
            bot.answer_callback_query(
                call.id, "❌ Auto-upload not configured properly.")
            return

        try:
            _, movie_idx, link_idx = call.data.split('_')
            movie_idx = int(movie_idx)
            link_idx = int(link_idx)

            movie_title = movie_list[movie_idx]
            magnet_link = real_dict[movie_title][link_idx]['magnet']

            bot.answer_callback_query(
                call.id, "✅ Starting Download & Upload...")
            msg = bot.send_message(
                call.message.chat.id,
                "<b>Please Wait... Connecting to Server...</b>")

            # Start background task in the Pyrogram loop
            asyncio.run_coroutine_threadsafe(
                download_and_upload(
                    magnet_link,
                    msg,
                    p_client,
                    call.message.chat.id),
                pyro_loop)

        except Exception as e:
            logger.error(f"Download Callback Error: {e}")
            bot.answer_callback_query(call.id, "❌ Error starting download.")
        return

    # Handle Movie Selection
    for key, value in enumerate(movie_list):
        if call.data == f"{key}":
            if value in real_dict.keys():
                for idx, item in enumerate(real_dict[value]):
                    # Create Download Button
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(
                        text="📥 Download & Upload to Telegram",
                        callback_data=f"down_{key}_{idx}"
                    ))

                    bot.send_message(
                        call.message.chat.id,
                        text=item['message'],
                        reply_markup=markup
                    )


def makeKeyboard(movie_list):
    markup = types.InlineKeyboardMarkup()
    for key, value in enumerate(movie_list):
        markup.add(
            types.InlineKeyboardButton(
                text=value,
                callback_data=f"{key}"))
    return markup


def tamilmv():
    mainUrl = TAMILMV_URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    movie_list = []
    real_dict = {}

    try:
        web = requests.get(mainUrl, headers=headers)
        web.raise_for_status()
        soup = BeautifulSoup(web.text, 'lxml')

        temps = soup.find_all('div', {'class': 'ipsType_break ipsContained'})

        if len(temps) < 15:
            logger.warning("Not enough movies found on the page")
            return [], {}

        for i in range(15):
            title = temps[i].findAll('a')[0].text.strip()
            link = temps[i].find('a')['href']
            movie_list.append(title)

            movie_details = get_movie_details(link)
            real_dict[title] = movie_details

        return movie_list, real_dict
    except Exception as e:
        logger.error(f"Error in tamilmv function: {e}")
        return [], {}


def get_movie_details(url):
    try:
        html = requests.get(url, timeout=15)
        html.raise_for_status()
        soup = BeautifulSoup(html.text, 'lxml')

        mag = [a['href'] for a in soup.find_all(
            'a', href=True) if 'magnet:' in a['href']]
        filelink = [a['href'] for a in soup.find_all(
            'a', {"data-fileext": "torrent", 'href': True})]

        movie_details = []
        movie_title = soup.find('h1').text.strip(
        ) if soup.find('h1') else "Unknown Title"

        for p in range(len(mag)):
            torrent_link = filelink[p] if p < len(filelink) else None
            if torrent_link and not torrent_link.startswith('http'):
                torrent_link = f'{TAMILMV_URL}{torrent_link}'

            message = f"""
<b>📂 Movie Title:</b>
<blockquote>{movie_title}</blockquote>

🧲 <b>Magnet Link:</b>
<pre>{mag[p]}</pre>
"""
            if torrent_link:
                message += f"""
📥 <b>Download Torrent:</b>
<a href="{torrent_link}">🔗 Click Here</a>
"""
            else:
                message += """
📥 <b>Torrent File:</b> Not Available
"""

            movie_details.append({
                'message': message,
                'magnet': mag[p]
            })

        return movie_details
    except Exception as e:
        logger.error(f"Error retrieving movie details: {e}")
        return []


@app.route('/')
def health_check():
    return "Angel Bot Healthy", 200


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403


if __name__ == "__main__":
    # Remove any previous webhook
    bot.remove_webhook()
    time.sleep(1)

    # Set webhook
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

    # Start Flask app
    app.run(host='0.0.0.0', port=PORT)
