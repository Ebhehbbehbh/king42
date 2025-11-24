import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import replicate

# التكوين الثابت
BOT_TOKEN = "8236056575:AAHI0JHvTGdJiu92sDXiv7dbWMJLxvMY_x4"
REPLICATE_TOKEN = "r8_4TXR4S4VdzZrX36QFNafizPkXKEVQ8E18bl9f"

# إعداد Replicate
replicate_client = replicate.Client(api_token=REPLICATE_TOKEN)

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    
    welcome_text = f"""
🎨 **مرحباً {user.first_name} في فنان الذكاء الاصطناعي!**

✨ **ماذا يمكنني فعلة:**
• تحويل أي وصف إلى لوحات فنية
• 4 أنماط فنية مختلفة
• جودة عالية 1024x1024 بكسل
• ❌ **لا توجد حدود للاستخدام!**

🎭 **الأوامر المتاحة:**
/start - بدء الاستخدام
/styles - عرض الأنماط الفنية
/help - المساعدة والدعم

📝 **اكتب لي وصفاً للصورة التي تريدها!**
    """
    update.message.reply_text(welcome_text)

def show_styles(update: Update, context: CallbackContext):
    styles_text = """
🎨 **الأنماط الفنية المتاحة:**

1. **🖼 واقعي** - صور فوتوغرافية واقعية
2. **🎎 أنيمي** - رسوم أنيمي يابانية  
3. **🖌 فني** - لوحات فنية كلاسيكية
4. **💻 رقمي** - فن رقمي حديث

**طريقة الاستخدام:**
- اكتب الوصف فقط
- أو أضف رقم النمط قبل الوصف
- مثال: "2 فتاة أنيمي بشعر أزرق"
    """
    update.message.reply_text(styles_text)

def help_command(update: Update, context: CallbackContext):
    help_text = """
📖 **دليل الاستخدام:**

**أمثلة:**
- "قطة بيضاء تلعب في الحديقة"
- "2 فتاة أنيمي بشعر أزرق" 
- "4 مدينة مستقبلية تحت المطر"

⏱ **مدة الإنشاء:** 20-30 ثانية
🎉 **لا توجد حدود للاستخدام!**
    """
    update.message.reply_text(help_text)

def generate_image(prompt):
    """دالة إنشاء الصورة"""
    try:
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "num_outputs": 1
            }
        )
        return output[0]
    except Exception as e:
        logger.error(f"Replicate error: {e}")
        return None

def handle_message(update: Update, context: CallbackContext):
    user_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not user_text:
        update.message.reply_text("⚠️ الرجاء كتابة وصف للصورة!")
        return
    
    # إرسال رسالة الانتظار
    wait_msg = update.message.reply_text("🔮 الجني الفني يعمل على صورتك...")
    
    def generate_and_send():
        try:
            image_url = generate_image(user_text)
            
            if image_url:
                context.bot.send_photo(
                    chat_id=user_id,
                    photo=image_url,
                    caption=f"🎨 '{user_text}'"
                )
                context.bot.delete_message(chat_id=user_id, message_id=wait_msg.message_id)
            else:
                context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=wait_msg.message_id,
                    text="❌ فشل في إنشاء الصورة. حاول مرة أخرى!"
                )
                
        except Exception as e:
            logger.error(f"Error: {e}")
            context.bot.edit_message_text(
                chat_id=user_id,
                message_id=wait_msg.message_id,
                text="❌ حدث خطأ. حاول مرة أخرى!"
            )
    
    thread = threading.Thread(target=generate_and_send)
    thread.start()

def setup_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("styles", show_styles))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    return updater

@app.route('/')
def home():
    return "🎨 AI Artist Bot is Running!"

def run_bot():
    updater = setup_bot()
    updater.start_polling()
    logger.info("🤖 Bot started!")
    updater.idle()

if __name__ == '__main__':
    run_bot()
