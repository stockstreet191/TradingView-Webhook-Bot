from flask import Flask, request, abort
import os
from telegram import Bot
from telegram.constants import ParseMode
import asyncio

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # 现在是 510572692（你的私聊）


if not TOKEN or not CHAT_ID:
    raise RuntimeError("请设置 TELEGRAM_TOKEN 和 TELEGRAM_CHAT_ID")

bot = Bot(token=TOKEN)

async def send_message(text: str):
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text[:4000],
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

@app.route('/', methods=['GET'])
def index():
    return "Bot 运行中 ✅"

@app.route('/tv2025', methods=['GET', 'POST'])   # 改成这个新名字！
def tv2025():   # 原来是 def webhook():
    if request.method == 'GET':
        return 'OK', 200

 # 密钥校验 —— 必须完整保留这三行！！！
    secret = os.getenv("WEBHOOK_SECRET")
    if secret and request.args.get('key') != secret:
        abort(403)

    data = request.get_json(force=True, silent=True)
    if not data:
        abort(400)

    message = f"TradingView 警报已触发！\n时间：{data.get('time', '')}\n内容：{str(data)}"

    # 关键：用 get_event_loop 代替 asyncio.run（Render 环境下唯一稳发方式）
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_message(message))

    return 'OK', 200

# Render 用 gunicorn 启动，不需要这几行
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 10000))
#     app.run(host='0.0.0.0', port=port)
