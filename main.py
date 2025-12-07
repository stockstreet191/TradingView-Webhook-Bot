from flask import Flask, request
import telegram
import asyncio
import os

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN") or "1490895893:AAGJ2BT1ar1-2jlfIeMN-4M6LNHnDXzc9h8"  # Render 环境变量或 config.py
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or "-1001234567890"

bot = telegram.Bot(token=TOKEN)

async def send_telegram(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        print(f"Telegram error: {e}")

@app.route('/', methods=['GET'])
def index():
    return "TradingView → Telegram Bot is running!"

@app.route('/', methods=['POST'])
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json(force=True)
        message = str(data.get('message', '') or data)
        asyncio.run(send_telegram(message))
        return 'OK', 200
    return 'Send POST to this URL', 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
