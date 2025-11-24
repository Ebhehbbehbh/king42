import os
import logging
import time
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from replicate import Client

# التكوين الثابت
BOT_TOKEN = "8236056575:AAHI0JHvTGdJiu92sDXiv7dbWMJLxvMY_x4"
REPLICATE_TOKEN = "r8_4TXR4S4VdzZrX36QFNafizPkXKEVQ8E18bl9f"

# إعداد Replicate Client
replicate_client = Client(api_token=REPLICATE_TOKEN)

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
• سرعة إنشاء 20-30 ثانية
• ❌ **لا توجد حدود للاستخدام!**

🎭 **الأوامر المتاحة:**
/start - بدء الاستخدام
/styles - عرض الأنماط الفنية
/help - المساعدة والدعم

📝 **اكتب لي وصفاً للصورة التي تريدها!**

🔥 **استخدم كما تريد بدون قيود!**
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
- اكتب الوصف فقط لأفضل نمط تلقائي
- أو أضف رقم النمط قبل الوصف
- مثال: "2 فتاة أنيمي بشعر أزرق"
    """
    update.message.reply_text(styles_text)

def help_command(update: Update, context: CallbackContext):
    help_text = """
📖 **دليل الاستخدام الكامل:**

**1. الإنشاء العادي:**
اكتب وصف الصورة مباشرة
مثال: "قصر أبيض على جزيرة استوائية"

**2. الإنشاء بنمط محدد:**
اكتب رقم النمط ثم الوصف
مثال: "3 منظر غروب شمس على البحر"

**3. أمثلة إبداعية:**
- "فارس يركب تنيناً في سماء النجوم"
- "1 قطة بيضاء تلعب في الحديقة"
- "4 مدينة مستقبلية تحت المطر"

⏱ **مدة الإنشاء:** 20-30 ثانية
🎉 **لا توجد حدود للاستخدام!**
    """
    update.message.reply_text(help_text)

def generate_image(prompt, style="auto"):
    """دالة إنشاء الصورة باستخدام Replicate"""
    
    style_presets = {
        "1": "realistic, photorealistic, high detail, 4K",
        "2": "anime style, manga style, Japanese animation, vibrant colors",
        "3": "oil painting, artistic, classic art, masterpiece", 
        "4": "digital art, futuristic, cyberpunk, neon colors"
    }
    
    # إعداد ال prompt النهائي
    final_prompt = prompt
    if style in style_presets:
        final_prompt = f"{style_presets[style]}, {prompt}"
    
    try:
        # استخدام نموذج SDXL الأحدث
        output = replicate_client.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": final_prompt,
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 30,
                "refine": "expert_ensemble_refiner"
            }
        )
        return output[0]  # رابط الصورة
        
    except Exception as e:
        logger.error(f"Replicate error: {e}")
        return None

def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    user_text = update.message.text.strip()
    user_id = user.id
    
    if not user_text:
        update.message.reply_text("⚠️ الرجاء كتابة وصف للصورة!")
        return
    
    # تحليل النص
    style = "auto"
    prompt = user_text
    
    # التحقق إذا بدأ برقم النمط
    if user_text[0] in ['1', '2', '3', '4'] and len(user_text) > 2 and user_text[1] in [' ', '.', '-']:
        style = user_text[0]
        prompt = user_text[2:].strip()
    
    # إرسال رسالة الانتظار
    wait_msg = update.message.reply_text(f"""
🔮 **الجني الفني يعمل على صورتك...**

⏱ المدة المتوقعة: 20-30 ثانية
📝 الوصف: {prompt[:50] + "..." if len(prompt) > 50 else prompt}
    """)

    # إنشاء الصورة في thread منفصل
    def generate_and_send():
        try:
            image_url = generate_image(prompt, style)
            
            if image_url:
                # إرسال الصورة
                context.bot.send_photo(
                    chat_id=user_id,
                    photo=image_url,
                    caption=f"🎨 '{prompt}'\n\n✅ تم الإنشاء بنجاح!"
                )
                
                # حذف رسالة الانتظار
                context.bot.delete_message(chat_id=user_id, message_id=wait_msg.message_id)
                
            else:
                context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=wait_msg.message_id,
                    text="❌ فشل في إنشاء الصورة. حاول مرة أخرى!"
                )
                
        except Exception as e:
            logger.error(f"Generation error: {e}")
            context.bot.edit_message_text(
                chat_id=user_id,
                message_id=wait_msg.message_id,
                text="❌ حدث خطأ غير متوقع. حاول مرة أخرى!"
            )
    
    # تشغيل عملية الإنشاء في thread منفصل
    thread = threading.Thread(target=generate_and_send)
    thread.start()

def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Error: {context.error}")

def setup_bot():
    """إعداد وتشغيل البوت"""
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # إضافة handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("styles", show_styles))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error_handler)
    
    return updater

@app.route('/')
def home():
    return "🎨 AI Artist Bot is Running!"

@app.route('/health')
def health():
    return "✅ Bot is Healthy"

def run_bot():
    """تشغيل البوت في thread منفصل"""
    updater = setup_bot()
    updater.start_polling()
    logger.info("🤖 Bot started successfully!")
    updater.idle()

if __name__ == '__main__':
    # تشغيل البوت في production
    run_bot()
