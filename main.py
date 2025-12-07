from flask import Flask, request, abort
import os
from telegram import Bot
from telegram.constants import ParseMode
import asyncio
import requests
from io import BytesIO

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # 群组用 -1003477037501，私聊用 510572692
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("请设置 TELEGRAM_TOKEN 和 TELEGRAM_CHAT_ID")

bot = Bot(token=TOKEN)

# 新增：支持发图片的异步函数
async def send_alert(data):
    # 优先取 TradingView 官方变量
    text = data.get('message', str(data))
    photo_url = (
        data.get('plot_0') or
        data.get('screenshot') or
        data.get('plot.snapshot') or
        data.get('image')
    )

    try:
        if photo_url and photo_url.startswith('http'):
            # 下载图片
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(photo_url, headers=headers, timeout=15)
            if response.status_code == 200 and len(response.content) > 10000:  # 过滤无效小图
                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=BytesIO(response.content),
                    caption=text[:1024],
                    parse_mode='HTML'
                )
                return
    except Exception as e:
        print(f"发图失败，降级发文字: {e}")

    # 发图失败或无图 → 发文字
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text[:4000],
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

@app.route('/', methods=['GET'])
def index():
    return "TradingView → Telegram + 自动截图 Bot 运行中"

@app.route('/tv2025', methods=['GET', 'POST'])
def tv2025():
    if request.method == 'GET':
        return 'OK', 200

    # 密钥校验
    secret = os.getenv("WEBHOOK_SECRET")
    if secret and request.args.get('key') != secret:
        abort(403)

    # 兼容 JSON 和纯文本
    if request.is_json:
        data = request.get_json(force=True, silent=True) or {}
    else:
        raw_text = request.data.decode('utf-8').strip()
        data = {"message": raw_text if raw_text else "TradingView 警报触发"}

    # 发送（自动带图）
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_alert(data))

    return 'OK', 200

# requirements.txt 需要加这两行：
# requests
# pillow
