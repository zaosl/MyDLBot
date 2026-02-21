import telebot
import yt_dlp
import os
import threading
import time
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '8517195431:AAEkGqP7XA16CgFqvlujl357YeyABWyCH1s'
bot = telebot.TeleBot(TOKEN)

# دیتابیس موقت زبان کاربران
USER_LANGS = {}

TEXTS = {
    'en': {
        'welcome': "🌍 **Welcome to VIP Downloader!**\nSend me a link from **YouTube, Instagram, or TikTok** and I'll grab the video for you! 📥",
        'wait': "⏳ **Processing...** Please wait while I extract the video.",
        'uploading': "✅ **Found it!** Uploading to Telegram now...",
        'error': "❌ **Error!** The video might be too large (over 50MB) or the link is private/invalid.",
        'invalid': "⚠️ **Invalid Link!** Please send a valid YouTube, IG, or TikTok URL.",
        'lang_select': "Please select your language:"
    },
    'ru': {
        'welcome': "🌍 **Добро пожаловать в VIP Downloader!**\nОтправьте ссылку из **YouTube, Instagram или TikTok**, и я скачаю видео для вас! 📥",
        'wait': "⏳ **Обработка...** Пожалуйста, подождите, пока я извлеку видео.",
        'uploading': "✅ **Найдено!** Загрузка в Telegram...",
        'error': "❌ **Ошибка!** Видео может быть слишком большим (более 50 МБ) или ссылка недействительна.",
        'invalid': "⚠️ **Неверная ссылка!** Пожалуйста, отправьте рабочую ссылку.",
        'lang_select': "Пожалуйста, выберите ваш язык:"
    },
    'ar': {
        'welcome': "🌍 **مرحباً بك في VIP Downloader!**\nأرسل لي رابطاً من **YouTube أو Instagram أو TikTok** وسأقوم بتنزيله لك! 📥",
        'wait': "⏳ **جاري المعالجة...** يرجى الانتظار حتى يتم استخراج الفيديو.",
        'uploading': "✅ **تم العثور عليه!** جارٍ الرفع إلى تلغرام...",
        'error': "❌ **خطأ!** قد يكون الفيديو كبيراً جداً (أكثر من 50 ميجابايت) أو الرابط غير صالح.",
        'invalid': "⚠️ **رابط غير صالح!** يرجى إرسال رابط صحيح من يوتيوب أو إنستا أو تيك توك.",
        'lang_select': "يرجى اختيار لغتك:"
    }
}

# --- وب‌سرور ضد خواب ---
app = Flask(__name__)
@app.route('/')
def home(): return "🤖 Multi-lang Downloader is running!"
def run_web(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): threading.Thread(target=run_web).start()

if not os.path.exists('downloads'): os.makedirs('downloads')

@bot.message_handler(commands=['start'])
def start_lang(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru"),
        InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar")
    )
    bot.send_message(message.chat.id, "🌍 Select Language / Выберите язык / اختر اللغة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
def handle_lang(call):
    lang = call.data.split('_')[1]
    USER_LANGS[call.from_user.id] = lang
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, TEXTS[lang]['welcome'], parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_urls(message):
    user_id = message.from_user.id
    lang = USER_LANGS.get(user_id, 'en') # زبان پیش‌فرض انگلیسی
    t = TEXTS[lang]
    url = message.text.strip()
    
    if any(domain in url for domain in ['instagram.com', 'youtube.com', 'youtu.be', 'tiktok.com']):
        msg_wait = bot.reply_to(message, t['wait'], parse_mode='Markdown')
        file_name = f"downloads/vid_{user_id}_{int(time.time())}.mp4"
        
        try:
            ydl_opts = {
                'outtmpl': file_name,
                'format': 'best[ext=mp4][filesize<45M]/best[filesize<45M]',
                'noplaylist': True, 'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            bot.edit_message_text(t['uploading'], chat_id=message.chat.id, message_id=msg_wait.message_id, parse_mode='Markdown')
            
            with open(file_name, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=f"🎯 Shared via @{bot.get_me().username}")
            
            os.remove(file_name)
            bot.delete_message(chat_id=message.chat.id, message_id=msg_wait.message_id)
            
        except Exception:
            bot.edit_message_text(t['error'], chat_id=message.chat.id, message_id=msg_wait.message_id, parse_mode='Markdown')
            if os.path.exists(file_name): os.remove(file_name)
    else:
        bot.reply_to(message, t['invalid'], parse_mode='Markdown')

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)