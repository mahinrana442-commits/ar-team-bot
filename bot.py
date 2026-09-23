import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8624499142:AAFQ1hElEKGZUj9bEn1sZ6qYpiwvTqV6z_A"

SMS_BOWER_API_KEY = "TJkdrZAI28TInbzhJEMYkXGc1n2FJqBt"
SMS_OTPS_API_KEY = (
    "GtwfBfbN04sr2cYJlFaMCwzOlQFtbq0Fef1uOpr40r8g6VYiJhPkhT5X4JJI"
)

SMS_BOWER_URL = "https://smsbower.com/stubs/handler_api.php"
SMS_OTPS_URL = "https://smsotps.com/stubs/handler_api.php"

# Requested Specific Countries (Name, Code, Dial Code, Flag)
TARGET_COUNTRIES = {
    "Colombia": {"code": "33", "dial": "+57", "flag": "🇨🇴"},
    "Chile": {"code": "151", "dial": "+56", "flag": "🇨🇱"},
    "Argentina": {"code": "39", "dial": "+54", "flag": "🇦🇷"},
    "Tajikistan": {"code": "143", "dial": "+992", "flag": "🇹🇯"},
    "Algeria": {"code": "58", "dial": "+213", "flag": "🇩🇿"},
}

user_provider = {}
active_orders = {}


# Render Dummy Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Active")


def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()


def get_api_info(user_id):
    provider = user_provider.get(user_id, "SMS Bower")
    if provider == "SMS Bower":
        return SMS_BOWER_URL, SMS_BOWER_API_KEY, "SMS Bower"
    return SMS_OTPS_URL, SMS_OTPS_API_KEY, "SMS OTPs"


def get_balance(url, api_key):
    try:
        res = requests.get(
            f"{url}?api_key={api_key}&action=getBalance", timeout=5
        ).text
        if "ACCESS_BALANCE" in res:
            return res.split(":")[1]
        return "0.00"
    except Exception:
        return "0.00"


def get_country_price(url, api_key, country_code):
    try:
        res = requests.get(
            f"{url}?api_key={api_key}&action=getPrices&service=tg&country={country_code}",
            timeout=5,
        ).json()
        if country_code in res and "tg" in res[country_code]:
            prices = list(res[country_code]["tg"].keys())
            if prices:
                return f"${prices[0]}"
    except Exception:
        pass
    return "$0.02"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id not in user_provider:
        user_provider[user_id] = "SMS Bower"

    url, api_key, provider = get_api_info(user_id)
    balance = get_balance(url, api_key)

    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Get Number", callback_data="show_services"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Live Traffic", callback_data="check_balance"
            ),
            InlineKeyboardButton(
                "💳 Balance", callback_data="check_balance"
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Switch Provider", callback_data="switch_provider"
            )
        ],
    ]

    welcome_text = (
        f"🔥 **AR TEAM / SMSly Bot-e Swagotom!**\n\n"
        f"Ekhane kaj kore khub sohojei Verification OTP nite parben.\n"
        f"💰 **Current Balance:** `{balance} RUB`\n"
        f"🌐 **Current Provider:** `{provider}`\n\n"
        f"👉 Shuru koralar jonno **Get Number** button-e click korun!"
    )

    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    else:
        await update.callback_query.message.edit_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    url, api_key, provider = get_api_info(user_id)

    if data == "main_menu":
        await start(update, context)

    elif data == "check_balance":
        balance = get_balance(url, api_key)
        await query.answer(
            f"💰 {provider} Balance: {balance} RUB", show_alert=True
        )

    elif data == "switch_provider":
        p_kb = [
            [
                InlineKeyboardButton(
                    "🔹 SMS Bower", callback_data="set_bower"
                ),
                InlineKeyboardButton("🔸 SMS OTPs", callback_data="set_otps"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ]
        await query.message.edit_text(
            "Select API Provider:", reply_markup=InlineKeyboardMarkup(p_kb)
        )

    elif data == "set_bower":
        user_provider[user_id] = "SMS Bower"
        await start(update, context)

    elif data == "set_otps":
        user_provider[user_id] = "SMS OTPs"
        await start(update, context)

    elif data == "show_services":
        s_kb = [
            [
                InlineKeyboardButton(
                    "✈️ Telegram", callback_data="select_country"
                )
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
        ]
        await query.message.edit_text(
            "Select a service below:", reply_markup=InlineKeyboardMarkup(s_kb)
        )

    elif data == "select_country":
        buttons = []
        for c_name, c_info in TARGET_COUNTRIES.items():
            price = get_country_price(url, api_key, c_info["code"])
            btn_text = (
                f"{c_info['flag']} {c_name} ({c_info['dial']}) | {price}/OTP"
            )
            buttons.append(
                [
                    InlineKeyboardButton(
                        btn_text, callback_data=f"buy_{c_info['code']}_{c_name}"
                    )
                ]
            )

        buttons.append(
            [InlineKeyboardButton("🔙 Back", callback_data="show_services")]
        )
        await query.message.edit_text(
            "**Available countries:**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )

    elif data.startswith("buy_"):
        _, country_code, country_name = data.split("_", 2)
        c_info = TARGET_COUNTRIES[country_name]

        await query.message.edit_text(
            f"⏳ Requesting number for **{country_name}**..."
        )

        try:
            req_url = f"{url}?api_key={api_key}&action=getNumber&service=tg&country={country_code}"
            res = requests.get(req_url, timeout=10).text

            if "ACCESS_NUMBER" in res:
                parts = res.split(":")
                tz_id = parts[1]
                number = parts[2]

                active_orders[user_id] = {
                    "id": tz_id,
                    "number": number,
                    "provider": provider,
                    "url": url,
                    "api_key": api_key,
                    "country": country_name,
                    "flag": c_info["flag"],
                    "dial": c_info["dial"],
                    "start_time": asyncio.get_event_loop().time(),
                }

                action_kb = [
                    [
                        InlineKeyboardButton(
                            f"✈️ {c_info['flag']} +{number}",
                            callback_data="copy_num",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Change Country", callback_data="select_country"
                        ),
                        InlineKeyboardButton(
                            "🔄 Change Number",
                            callback_data=f"buy_{country_code}_{country_name}",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Cancel", callback_data="cancel_order"
                        )
                    ],
                ]

                msg = await query.message.reply_text(
                    f"🔄 These numbers are activated and ready to receive SMS.\n\n"
                    f"🔹 **Service:** Telegram\n"
                    f"🌐 **Country:** {c_info['flag']} {country_name} ({c_info['dial']})\n"
                    f"📞 **Number:** `+{number}`\n\n"
                    f"⏳ Waiting for OTP...",
                    reply_markup=InlineKeyboardMarkup(action_kb),
                    parse_mode="Markdown",
                )

                context.job_queue.run_repeating(
                    check_sms_status,
                    interval=5,
                    first=1,
                    data={
                        "msg_id": msg.message_id,
                        "chat_id": query.message.chat_id,
                        "user_id": user_id,
                    },
                    name=str(user_id),
                )
            else:
                await query.message.edit_text(
                    f"❌ No number available for {country_name} right now.\nReason: `{res}`",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Try Again",
                                    callback_data="select_country",
                                )
                            ]
                        ]
                    ),
                    parse_mode="Markdown",
                )
        except Exception as e:
            await query.message.edit_text(f"❌ Connection Error: {e}")

    elif data == "cancel_order":
        order = active_orders.get(user_id)
        if not order:
            await query.message.edit_text("❌ No active order found.")
            return

        elapsed = asyncio.get_event_loop().time() - order["start_time"]

        # 2 Minute rule for SMS OTPs
        if order["provider"] == "SMS OTPs" and elapsed < 120:
            rem = int(120 - elapsed)
            await query.answer(
                f"⚠️ Please wait {rem} seconds more before canceling on SMS OTPs (2-min rule)!",
                show_alert=True,
            )
            return

        try:
            cancel_url = f"{order['url']}?api_key={order['api_key']}&action=setStatus&status=8&id={order['id']}"
            requests.get(cancel_url, timeout=5)
        except Exception:
            pass

        jobs = context.job_queue.get_jobs_by_name(str(user_id))
        for j in jobs:
            j.schedule_removal()

        del active_orders[user_id]
        await query.message.edit_text(
            "❌ **Number activation successfully canceled.**"
        )


async def check_sms_status(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.data["user_id"]
    order = active_orders.get(user_id)

    if not order:
        job.schedule_removal()
        return

    try:
        check_url = f"{order['url']}?api_key={order['api_key']}&action=getStatus&id={order['id']}"
        res = requests.get(check_url, timeout=5).text

        if "STATUS_OK" in res:
            code = res.split(":")[1]
            job.schedule_removal()
            del active_orders[user_id]

            await context.bot.send_message(
                chat_id=job.data["chat_id"],
                text=f"🎉 **OTP Received!**\n\n"
                f"📞 **Number:** `+{order['number']}`\n"
                f"🔑 **Code:** `{code}`",
                parse_mode="Markdown",
            )
            return
    except Exception:
        pass


def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    print("SMSly Bot Style System Active...")
    app.run_polling()


if __name__ == "__main__":
    main()
