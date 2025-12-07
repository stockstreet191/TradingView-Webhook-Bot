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
    return "TradingView → Telegram Bot is running！"

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# 关键修改开始：把原来的两行 @app.route 合并成这一段
@app.route('/webhook', methods=['GET', 'POST'])   # ← 重点：加上 GET！
def webhook():
    # 如果是 GET 请求（Render 健康检查或浏览器访问），直接返回 OK
    if request.method == 'GET':
        return 'OK', 200

    # 下面才是真正的 TradingView POST 警报
    if request.method == 'POST':
        # 密钥校验（你已经设置了 WEBHOOK_SECRET）
        secret = os.getenv("WEBHOOK_SECRET")
        if secret and request.args.get('key') != secret:
            return 'Forbidden', 403

        data = request.get_json(force=True, silent=True)
        if not data:
            return 'Bad request', 400

        # 这里你可以后期改成美化模板，现在先保持原始输出
        message = str(data)
        asyncio.run(send_telegram(message))
        return 'OK', 200
# 关键修改结束
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
