import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import replicate

# التكوين
BOT_TOKEN = "8236056575:AAHI0JHvTGdJiu92sDXiv7dbWMJLxvMY_x4"
REPLICATE_TOKEN = "r8_4TXR4S4VdzZrX36QFNafizPkXKEVQ8E18bl9f"

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🎨 مرحباً! أنا بوت توليد الصور. اكتب وصفاً للصورة التي تريدها!")

def handle_message(update: Update, context: CallbackContext):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    if not user_text.strip():
        update.message.reply_text("⚠️ الرجاء كتابة وصف للصورة!")
        return
    
    # رسالة الانتظار
    wait_msg = update.message.reply_text("🔄 جاري إنشاء صورتك...")
    
    try:
        # توليد الصورة
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": user_text,
                "width": 1024,
                "height": 1024
            }
        )
        
        # إرسال الصورة
        update.message.bot.send_photo(
            chat_id=user_id,
            photo=output[0],
            caption=f"🎨 {user_text}"
        )
        
        # حذف رسالة الانتظار
        update.message.bot.delete_message(chat_id=user_id, message_id=wait_msg.message_id)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.bot.edit_message_text(
            chat_id=user_id,
            message_id=wait_msg.message_id,
            text="❌ فشل في إنشاء الصورة. حاول مرة أخرى!"
        )

def setup_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    return updater

@app.route('/')
def home():
    return "🤖 Bot is running!"

# تشغيل البوت
if __name__ == '__main__':
    updater = setup_bot()
    
    # على Render استخدم Webhook
    if 'RENDER' in os.environ:
        PORT = int(os.environ.get('PORT', 5000))
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"https://your-app-name.onrender.com/{BOT_TOKEN}"
        )
    else:
        # للتطوير المحلي
        updater.start_polling()
    
    updater.idle()
