from app import app, run_bot
import threading

# تشغيل البوت في thread منفصل
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
