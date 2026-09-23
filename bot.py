import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

load_dotenv()

BOT_TOKEN = os.8624499142:AAFLy_phYwIuF7t-HcrgphwW81ceCuKf2dg
API_KEY = os.sk_e8b858343e0101783c57b73d4e687d2b7fc7566314eec3d01738aac02378eb42
BASE_URL = os.
[http://203.161.58.20:3001/api/functions/agent-api](http://203.161.58.20:3001/api/functions/agent-api)
    "PANEL_API_URL",
    "http://203.161.58.20:3001/api/functions/agent-api"
).rstrip("/")

if not BOT_TOKEN or not API_KEY:
    raise RuntimeError("Set BOT_TOKEN and PANEL_API_KEY in .env")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

class PanelAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"x-api-key": api_key}

    async def get(self, path, params=None):
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                self.base_url + path,
                headers=self.headers,
                params=params or {}
            ) as r:
                text = await r.text()
                if r.status >= 400:
                    raise RuntimeError(f"API {r.status}: {text[:500]}")
                try:
                    return json.loads(text)
                except Exception:
                    return {"raw": text}

    async def numbers(self, page=1, limit=20, status="assigned"):
        return await self.get("/numbers", {
            "page": page, "limit": limit, "status": status
        })

    async def otp(self, number=None, platform=None, since=None):
        params = {}
        if number: params["number"] = number
        if platform: params["platform"] = platform
        if since: params["since"] = since
        return await self.get("/otp", params)

    async def stats(self):
        return await self.get("/stats")

    async def balance(self):
        return await self.get("/balance")

api = PanelAPI(BASE_URL, API_KEY)

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Get Number", callback_data="numbers"),
         InlineKeyboardButton(text="🔎 Search Number", callback_data="search")],
        [InlineKeyboardButton(text="📊 Live Traffic", callback_data="stats"),
         InlineKeyboardButton(text="💰 Balance", callback_data="balance")],
        [InlineKeyboardButton(text="📨 SMS Status", callback_data="sms"),
         InlineKeyboardButton(text="ℹ️ Help", callback_data="help")]
    ])

def pretty_numbers(payload):
    data = payload.get("data", [])
    if not data:
        return "📱 No numbers were returned by the panel."

    lines = ["📱 <b>Available Numbers</b>", ""]
    for i, item in enumerate(data[:20], 1):
        if isinstance(item, dict):
            number = item.get("number") or item.get("phone") or item.get("msisdn") or "Unknown"
            country = item.get("country") or item.get("country_name") or ""
            platform = item.get("platform") or item.get("service") or ""
            status = item.get("status") or ""
            extra = " • ".join(x for x in [country, platform, status] if x)
            lines.append(f"{i}. <code>{number}</code>" + (f" — {extra}" if extra else ""))
        else:
            lines.append(f"{i}. <code>{item}</code>")
    return "\n".join(lines)

def pretty_stats(payload):
    d = payload.get("data", payload)
    if isinstance(d, list):
        d = d[0] if d else {}
    if not isinstance(d, dict):
        return f"📊 <b>Stats</b>\n<code>{str(d)[:1500]}</code>"

    lines = ["📊 <b>Panel Statistics</b>", ""]
    labels = [
        ("total_sms", "Total SMS"),
        ("today_sms", "Today SMS"),
        ("balance", "Balance"),
        ("numbers", "Numbers"),
        ("users", "Users"),
    ]
    for key, label in labels:
        if key in d:
            lines.append(f"• {label}: <b>{d[key]}</b>")
    if len(lines) == 2:
        lines.append(f"<code>{json.dumps(d, ensure_ascii=False, indent=2)[:2500]}</code>")
    return "\n".join(lines)

@dp.message(CommandStart())
async def start(message: Message):
    text = (
        "🤖 <b>SMS Panel Bot</b>\n\n"
        "Welcome! This bot is connected to your authorized SMS panel API.\n\n"
        "Choose an option below:"
    )
    await message.answer(text, reply_markup=main_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "numbers")
async def cb_numbers(call: CallbackQuery):
    await call.answer()
    try:
        payload = await api.numbers()
        await call.message.answer(pretty_numbers(payload), parse_mode="HTML",
                                  reply_markup=main_keyboard())
    except Exception as e:
        await call.message.answer(f"❌ API error:\n<code>{str(e)[:1000]}</code>",
                                  parse_mode="HTML")

@dp.callback_query(F.data == "stats")
async def cb_stats(call: CallbackQuery):
    await call.answer()
    try:
        payload = await api.stats()
        await call.message.answer(pretty_stats(payload), parse_mode="HTML",
                                  reply_markup=main_keyboard())
    except Exception as e:
        await call.message.answer(f"❌ API error:\n<code>{str(e)[:1000]}</code>",
                                  parse_mode="HTML")

@dp.callback_query(F.data == "balance")
async def cb_balance(call: CallbackQuery):
    await call.answer()
    try:
        payload = await api.balance()
        await call.message.answer(
            "💰 <b>Balance</b>\n\n<code>" +
            json.dumps(payload, ensure_ascii=False, indent=2)[:2500] +
            "</code>",
            parse_mode="HTML", reply_markup=main_keyboard()
        )
    except Exception as e:
        await call.message.answer(f"❌ API error:\n<code>{str(e)[:1000]}</code>",
                                  parse_mode="HTML")

@dp.callback_query(F.data == "sms")
async def cb_sms(call: CallbackQuery):
    await call.answer()
    try:
        payload = await api.otp()
        await call.message.answer(
            "📨 <b>SMS Status</b>\n\n<code>" +
            json.dumps(payload, ensure_ascii=False, indent=2)[:3000] +
            "</code>",
            parse_mode="HTML", reply_markup=main_keyboard()
        )
    except Exception as e:
        await call.message.answer(f"❌ API error:\n<code>{str(e)[:1000]}</code>",
                                  parse_mode="HTML")

@dp.callback_query(F.data == "search")
async def cb_search(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        "🔎 Send a number or keyword to search.\n"
        "Search filtering depends on the fields supported by your panel API.",
        reply_markup=main_keyboard()
    )

@dp.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        "ℹ️ <b>Help</b>\n\n"
        "📱 Get Number — reads assigned numbers from your panel\n"
        "📊 Live Traffic — reads current panel statistics\n"
        "💰 Balance — reads your panel balance\n"
        "📨 SMS Status — reads SMS/OTP records exposed by your API\n\n"
        "Only use the API with numbers/services you are authorized to manage.",
        parse_mode="HTML", reply_markup=main_keyboard()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
