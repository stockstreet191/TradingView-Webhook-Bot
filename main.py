from flask import Flask, request, abort
import os
from telegram import Bot
from telegram.constants import ParseMode
import asyncio
import requests
from io import BytesIO

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("请设置 TOKEN 和 CHAT_ID")

# 关键修复：加大连接池 + 超时，解决 Pool timeout
bot = Bot(token=TOKEN, request_kwargs={'pool_timeout': 60, 'connection_pool_size': 20})

@app.route('/', methods=['GET'])
def index():
    return "TradingView → Telegram 终极版运行中"

@app.route('/tv2025', methods=['GET', 'POST'])
def tv2025():
    if request.method == 'GET':
        return 'OK', 200

    # 密钥校验
    if WEBHOOK_SECRET and request.args.get('key') != WEBHOOK_SECRET:
        abort(403)

    # 兼容 JSON 和纯文本
    if request.is_json:
        data = request.get_json(force=True, silent=True) or {}
    else:
        raw_text = request.data.decode('utf-8', errors='ignore').strip()
        data = {"message": raw_text or "TradingView 警报触发"}

    text = data.get('message', str(data))
    photo_url = data.get('plot_0') or data.get('screenshot') or data.get('plot.snapshot')

    print(f"[INFO] 收到警报: {text[:100]}")
    print(f"[INFO] 图片链接: {photo_url}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if photo_url and photo_url.startswith('http'):
            resp = requests.get(photo_url, timeout=20)
            if resp.status_code == 200 and len(resp.content) > 10000:
                loop.run_until_complete(
                    bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=BytesIO(resp.content),
                        caption=text[:1024],
                        parse_mode='HTML'
                    )
                )
                loop.close()
                return 'OK', 200
    except Exception as e:
        print(f"[ERROR] 发图失败: {e}")

    # 发文字兜底
    try:
        loop.run_until_complete(
            bot.send_message(
                chat_id=CHAT_ID,
                text=text[:4000],
                parse_mode='HTML',
                disable_web_page_preview=False
            )
        )
    except Exception as e:
        print(f"[ERROR] 发文字也失败: {e}")

    loop.close()
    return 'OK', 200
