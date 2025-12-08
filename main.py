from flask import Flask, request, abort
import os
from telegram import Bot
from telegram.constants import ParseMode
import asyncio
import requests
from io import BytesIO

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # 群组: -1003477037501

if not TOKEN or not CHAT_ID:
    raise RuntimeError("请设置 TELEGRAM_TOKEN 和 TELEGRAM_CHAT_ID")

bot = Bot(token=TOKEN)

# 增强调试版：支持发图片 + 详细日志
async def send_alert(data):
    print(f"[DEBUG] 收到完整数据: {data}")  # 日志1: 看原始数据
    
    # 提取消息和图片 URL（支持多种变量名）
    text = data.get('message', str(data))
    photo_url = (
        data.get('plot_0') or
        data.get('plot_1') or  # 万一不是第0个 plot
        data.get('screenshot') or
        data.get('plot.snapshot') or
        data.get('image') or
        text.split('{{plot_0}}')[1].split('}')[0] if '{{plot_0}}' in text else None  # 从文本提取
    )
    
    print(f"[DEBUG] 提取文本: {text[:200]}...")  # 日志2: 看文本（截断防太长）
    print(f"[DEBUG] 提取图片 URL: {photo_url}")  # 日志3: 看 URL（关键！）
    
    try:
        if photo_url and photo_url.startswith('http'):
            print(f"[DEBUG] 开始下载图片: {photo_url[:100]}...")  # 截断 URL
            # 增强 headers 防 TradingView 限制 + 更大超时
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; TradingViewBot/1.0; +https://tradingview.com)',
                'Referer': 'https://www.tradingview.com/'
            }
            response = requests.get(photo_url, headers=headers, timeout=30)  # 30s 超时
            print(f"[DEBUG] 下载状态码: {response.status_code}, 大小: {len(response.content)} bytes")
            
            if response.status_code == 200 and len(response.content) > 10000:  # 过滤无效/小图
                print("[DEBUG] 发送图片到 Telegram")
                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=BytesIO(response.content),
                    caption=text[:1024],
                    parse_mode='HTML'
                )
                print("[DEBUG] 图片发送成功！")
                return
            else:
                print(f"[DEBUG] 下载失败: 状态 {response.status_code} 或文件太小 (<10KB)")
        else:
            print("[DEBUG] 无有效图片 URL，跳过下载")
    except Exception as e:
        print(f"[DEBUG] 发图异常: {e}，降级发文字")

    # fallback: 发文字 + 开启预览（如果 URL 是链接，会显示缩略图）
    print("[DEBUG] 发送文字到 Telegram")
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text[:4000],
        parse_mode='HTML',
        disable_web_page_preview=False  # 开启预览，链接变小图
    )
    print("[DEBUG] 文字发送成功！")

@app.route('/', methods=['GET'])
def index():
    return "TradingView → Telegram + 调试版自动截图 Bot 运行中"

@app.route('/tv2025', methods=['GET', 'POST'])
def tv2025():  # 改回 def（不加 async）
    if request.method == 'GET':
        return 'OK', 200

    # 密钥校验
    secret = os.getenv("WEBHOOK_SECRET")
    if secret and request.args.get('key') != secret:
        print("[DEBUG] 密钥错误")
        abort(403)

    # 兼容 JSON 和纯文本
    if request.is_json:
        data = request.get_json(force=True, silent=True) or {}
    else:
        raw_text = request.data.decode('utf-8').strip()
        data = {"message": raw_text if raw_text else "TradingView 警报触发"}

    # ========= 强制发图终极版（同步包装）=========
    text = data.get('message', str(data))
    photo_url = data.get('plot_0') or data.get('screenshot') or data.get('plot.snapshot')

    print(f"[DEBUG] 提取到图片链接: {photo_url}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if photo_url and photo_url.startswith('http'):
        try:
            response = requests.get(photo_url, timeout=25)
            if response.status_code == 200 and len(response.content) > 15000:
                loop.run_until_complete(
                    bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=BytesIO(response.content),
                        caption=text[:1024],
                        parse_mode='HTML'
                    )
                )
                print("[DEBUG] 高清图发送成功！")
                loop.close()
                return 'OK', 200
        except Exception as e:
            print(f"[DEBUG] 发图失败: {e}")

    # 没图就发文字
    loop.run_until_complete(
        bot.send_message(
            chat_id=CHAT_ID,
            text=text[:4000],
            parse_mode='HTML',
            disable_web_page_preview=False
        )
    )
    loop.close()
    # ====================================================

    return 'OK', 200
