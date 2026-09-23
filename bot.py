 import os
import json
import asyncio
import aiohttp

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

load_dotenv()

BOT_TOKEN = os.getenv("8624499142:AAFLy_phYwIuF7t-HcrgphwW81ceCuKf2dg")
API_KEY = os.getenv("sk_e8b858343e0101783c57b73d4e687d2b7fc7566314eec3d01738aac02378eb42")

BASE_URL = os.getenv(
    "PANEL_API_URL",
    "[http://203.161.58.20:3001/api/functions/agent-api](http://203.161.58.20:3001/api/functions/agent-api)"
).rstrip("/")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not API_KEY:
    raise RuntimeError("API_KEY is not set")

bot = Bot(token=BOT_TOKEN)
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
            ) as response:

                text = await response.text()

                if response.status >= 400:
                    raise RuntimeError(
                        f"API {response.status}: {text[:500]}"
                    )

                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw": text}

    async def numbers(self, page=1, limit=20, status="assigned"):
        return await self.get(
            "/numbers",
            {
                "page": page,
                "limit": limit,
                "status": status
            }
        )

    async def stats(self):
        return await self.get("/stats")

    async def balance(self):
        return await self.get("/balance")


api = PanelAPI(BASE_URL, API_KEY)


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Get Number",
                    callback_data="numbers"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Statistics",
                    callback_data="stats"
                ),
                InlineKeyboardButton(
                    text="💰 Balance",
                    callback_data="balance"
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🤖 <b>SMS Panel Bot</b>\n\n"
        "Choose an option:",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


@dp.callback_query(F.data == "numbers")
async def cb_numbers(call: CallbackQuery):
    await call.answer()

    try:
        payload = await api.numbers()

        await call.message.answer(
            "<b>📱 Numbers</b>\n\n"
            f"<code>{json.dumps(payload, ensure_ascii=False, indent=2)[:3500]}</code>",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )

    except Exception as e:
        await call.message.answer(
            f"❌ API error:\n<code>{str(e)[:1000]}</code>",
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "stats")
async def cb_stats(call: CallbackQuery):
    await call.answer()

    try:
        payload = await api.stats()

        await call.message.answer(
            "<b>📊 Statistics</b>\n\n"
            f"<code>{json.dumps(payload, ensure_ascii=False, indent=2)[:3500]}</code>",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )

    except Exception as e:
        await call.message.answer(
            f"❌ API error:\n<code>{str(e)[:1000]}</code>",
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "balance")
async def cb_balance(call: CallbackQuery):
    await call.answer()

    try:
        payload = await api.balance()

        await call.message.answer(
            "<b>💰 Balance</b>\n\n"
            f"<code>{json.dumps(payload, ensure_ascii=False, indent=2)[:3500]}</code>",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )

    except Exception as e:
        await call.message.answer(
            f"❌ API error:\n<code>{str(e)[:1000]}</code>",
            parse_mode="HTML"
        )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
