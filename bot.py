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

# API Endpoints
SMS_BOWER_URL = "https://smsbower.com/stubs/handler_api.php"
SMS_OTPS_URL = "https://smsotps.com/stubs/handler_api.php"

# Popular Country Codes for Telegram
COUNTRIES = {
    "🇺🇸 USA": "187",
    "🇮🇳 India": "22",
    "🇮🇩 Indonesia": "6",
    "🇵🇭 Philippines": "4",
    "🇻🇳 Vietnam": "10",
    "🇷🇺 Russia": "0",
}

user_provider = {}
user_country = {}
active_orders = {}


# Render Web Service Port Dummy Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")


def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()


# API Helper Functions
def get_api_details(user_id):
    provider = user_provider.get(user_id, "SMS Bower")
    if provider == "SMS Bower":
        return SMS_BOWER_URL, SMS_BOWER_API_KEY, "SMS Bower"
    else:
        return SMS_OTPS_URL, SMS_OTPS_API_KEY, "SMS OTPs"


def get_balance(url, api_key):
    try:
        res = requests.get(
            f"{url}?api_key={api_key}&action=getBalance", timeout=5
        )
        if "ACCESS_BALANCE" in res.text:
            return res.text.split(":")[1]
        return "0.00"
    except Exception:
        return "N/A"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id not in user_provider:
        user_provider[user_id] = "SMS Bower"

    url, api_key, provider_name = get_api_details(user_id)
    balance = get_balance(url, api_key)

    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Get Number", callback_data="menu_select_country"
            ),
            InlineKeyboardButton("⚙️ Select Server", callback_data="select_server"),
        ],
        [
            InlineKeyboardButton(
                "📈 Live Traffic", callback_data="live_traffic"
            ),
            InlineKeyboardButton(
                "💳 Balance", callback_data="check_balance"
            ),
        ],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"আসসালামু আলাইকুম, **{user.first_name}**! 👋\n\n"
        f"🤖 **AR TEAM Verification Bot-এ আপনাকে স্বাগতম!**\n\n"
        f"🌐 **বর্তমান সার্ভার:** `{provider_name}`\n"
        f"💰 **অ্যাকাউন্ট ব্যালেন্স:** `{balance} RUB`\n\n"
        f"নিচের মেনু থেকে আপনার সার্ভিস নির্বাচন করুন:"
    )

    if update.message:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )
    else:
        await update.callback_query.message.edit_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "main_menu":
        await start(update, context)

    elif data == "check_balance":
        url, api_key, provider_name = get_api_details(user_id)
        balance = get_balance(url, api_key)
        await query.answer(
            f"💰 {provider_name} Balance: {balance} RUB", show_alert=True
        )

    elif data == "select_server":
        server_keyboard = [
            [
                InlineKeyboardButton(
                    "🔹 SMS Bower", callback_data="set_bower"
                ),
                InlineKeyboardButton("🔸 SMS OTPs", callback_data="set_otps"),
            ],
            [InlineKeyboardButton("🔙 ব্যাক মেনু", callback_data="main_menu")],
        ]
        await query.message.edit_text(
            "আপনার পছন্দের SMS API সার্ভার নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(server_keyboard),
        )

    elif data == "set_bower":
        user_provider[user_id] = "SMS Bower"
        await query.message.edit_text("✅ সার্ভার **SMS Bower** এ সেট করা হয়েছে!")
        await asyncio.sleep(1)
        await start(update, context)

    elif data == "set_otps":
        user_provider[user_id] = "SMS OTPs"
        await query.message.edit_text("✅ সার্ভার **SMS OTPs** এ সেট করা হয়েছে!")
        await asyncio.sleep(1)
        await start(update, context)

    elif data == "menu_select_country":
        country_buttons = []
        for name, code in COUNTRIES.items():
            country_buttons.append(
                [
                    InlineKeyboardButton(
                        f"{name}", callback_data=f"buy_{code}_{name}"
                    )
                ]
            )
        country_buttons.append(
            [InlineKeyboardButton("🔙 ব্যাক মেনু", callback_data="main_menu")]
        )

        await query.message.edit_text(
            "🗺️ **টেলিগ্রাম অ্যাকাউন্টের জন্য দেশ সিলেক্ট করুন:**",
            reply_markup=InlineKeyboardMarkup(country_buttons),
            parse_mode="Markdown",
        )

    elif data.startswith("buy_"):
        _, country_code, country_name = data.split("_", 2)
        url, api_key, provider = get_api_details(user_id)

        await query.message.edit_text(
            f"⏳ `{provider}` থেকে **{country_name}** এর নম্বর অর্ডার করা হচ্ছে..."
        )

        try:
            # Request Number from API
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
                    "start_time": asyncio.get_event_loop().time(),
                }

                action_keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔄 Change Number",
                            callback_data="menu_select_country",
                        ),
                        InlineKeyboardButton(
                            "❌ Cancel", callback_data="cancel_order"
                        ),
                    ]
                ]

                msg = await query.message.reply_text(
                    f"📱 **Service:** Telegram\n"
                    f"🌐 **Provider:** {provider}\n"
                    f"🗺️ **Country:** {country_name}\n"
                    f"📞 **Number:** `{number}`\n\n"
                    f"⏱️ **Elapsed Time:** 00:00s\n"
                    f"⏳ SMS/OTP আসার জন্য অপেক্ষা করা হচ্ছে...",
                    reply_markup=InlineKeyboardMarkup(action_keyboard),
                    parse_mode="Markdown",
                )

                context.job_queue.run_repeating(
                    check_sms_and_timer,
                    interval=5,
                    first=1,
                    data={
                        "msg_id": msg.message_id,
                        "chat_id": query.message.chat_id,
                        "user_id": user_id,
                        "time": 0,
                    },
                    name=str(user_id),
                )
            else:
                await query.message.edit_text(
                    f"❌ **নম্বর পাওয়া যায়নি!**\nকারণ: `{res}`\n\nঅন্য দেশ বা সার্ভার ট্রাই করুন।",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Try Again",
                                    callback_data="menu_select_country",
                                )
                            ]
                        ]
                    ),
                    parse_mode="Markdown",
                )
        except Exception as e:
            await query.message.edit_text(f"❌ API কানেকশনে সমস্যা হয়েছে: {e}")

    elif data == "cancel_order":
        order = active_orders.get(user_id)
        if not order:
            await query.message.edit_text(
                "❌ কোনো রানিং অর্ডার পাওয়া যায়নি।"
            )
            return

        elapsed = (
            asyncio.get_event_loop().time() - order["start_time"]
        )

        # SMS OTPs requires 2 minutes wait before cancellation
        if order["provider"] == "SMS OTPs" and elapsed < 120:
            rem = int(120 - elapsed)
            await query.answer(
                f"⚠️ SMS OTPs-এ নম্বর ক্যানসেল করতে আরও {rem} সেকেন্ড অপেক্ষা করতে হবে (সর্বনিম্ন ২ মিনিট)!",
                show_alert=True,
            )
            return

        # Cancel in API
        try:
            cancel_url = f"{order['url']}?api_key={order['api_key']}&action=setStatus&status=8&id={order['id']}"
            requests.get(cancel_url, timeout=5)
        except Exception:
            pass

        # Stop Timer Jobs
        jobs = context.job_queue.get_jobs_by_name(str(user_id))
        for job in jobs:
            job.schedule_removal()

        del active_orders[user_id]
        await query.message.edit_text(
            "❌ **নম্বর অ্যাক্টিভেশন সফলভাবে বাতিল করা হয়েছে।**"
        )


async def check_sms_and_timer(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    job.data["time"] += 5
    elapsed = job.data["time"]
    user_id = job.data["user_id"]
    order = active_orders.get(user_id)

    if not order:
        job.schedule_removal()
        return

    # Check OTP Status via API
    try:
        check_url = f"{order['url']}?api_key={order['api_key']}&action=getStatus&id={order['id']}"
        res = requests.get(check_url, timeout=5).text

        if "STATUS_OK" in res:
            code = res.split(":")[1]
            job.schedule_removal()
            del active_orders[user_id]

            await context.bot.send_message(
                chat_id=job.data["chat_id"],
                text=f"🎉 **আপনার OTP মেসেজ এসে গেছে!**\n\n"
                f"📞 **Number:** `{order['number']}`\n"
                f"🔑 **Verification Code:** `{code}`",
                parse_mode="Markdown",
            )
            return
    except Exception:
        pass

    # Timeout 20 minutes
    if elapsed >= 1200:
        job.schedule_removal()
        if user_id in active_orders:
            del active_orders[user_id]
        await context.bot.edit_message_text(
            chat_id=job.data["chat_id"],
            message_id=job.data["msg_id"],
            text="⏰ সময় শেষ হয়ে গেছে! অর্ডার বাতিল করা হলো।",
        )
        return

    minutes = elapsed // 60
    seconds = elapsed % 60
    time_str = f"{minutes:02d}:{seconds:02d}"

    action_keyboard = [
        [
            InlineKeyboardButton(
                "🗺️ Change Country", callback_data="menu_select_country"
            ),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_order"),
        ]
    ]

    try:
        await context.bot.edit_message_text(
            chat_id=job.data["chat_id"],
            message_id=job.data["msg_id"],
            text=f"📱 **Service:** Telegram\n"
            f"🌐 **Provider:** {order['provider']}\n"
            f"📞 **Number:** `{order['number']}`\n\n"
            f"⏱️ **Elapsed Time:** {time_str}\n"
            f"⏳ SMS/OTP এর জন্য অপেক্ষা করা হচ্ছে...",
            reply_markup=InlineKeyboardMarkup(action_keyboard),
            parse_mode="Markdown",
        )
    except Exception:
        pass


def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("AR Team Bot Active and Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
