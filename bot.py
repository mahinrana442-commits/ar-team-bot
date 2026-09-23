import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==================== CONFIGURATION ====================
BOT_TOKEN = 8624499142:AAEQF1q96dzUKBNnHcqQiKp8Lbp2IL7nCVU # এখানে BotFather থেকে পাওয়া টোকেন দিন

SMS_BOWER_API_KEY = "TJkdrZAI28TInbzhJEMYkXGc1n2FJqBt"
SMS_OTPS_API_KEY = (
    "GtwfBfbN04sr2cYJlFaMCwzOlQFtbq0Fef1uOpr40r8g6VYiJhPkhT5X4JJI"
)

user_provider = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_provider:
        user_provider[user_id] = "SMS Bower"

    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Get Number", callback_data="menu_get_number"
            ),
            InlineKeyboardButton("⚙️ Select Server", callback_data="select_server"),
        ],
        [
            InlineKeyboardButton(
                "📈 Live Traffic", callback_data="live_traffic"
            ),
            InlineKeyboardButton("💳 Balance", callback_data="balance"),
        ],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"🤖 **AR Team Bot-এ স্বাগতম!**\n\n"
        f"বর্তমান সার্ভার: **{user_provider[user_id]}**\n"
        f"নিচের মেনু থেকে আপনার পছন্দমতো অপশন সিলেক্ট করুন:"
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

    if data == "select_server":
        server_keyboard = [
            [
                InlineKeyboardButton(
                    "🔹 SMS Bower", callback_data="set_bower"
                ),
                InlineKeyboardButton("🔸 SMS OTPs", callback_data="set_otps"),
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")],
        ]
        await query.message.edit_text(
            "আপনার পছন্দের SMS API সার্ভার নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(server_keyboard),
        )

    elif data == "set_bower":
        user_provider[user_id] = "SMS Bower"
        await query.message.edit_text("✅ আপনার সার্ভার **SMS Bower** এ সেট করা হয়েছে!")
        await asyncio.sleep(1)
        await start(update, context)

    elif data == "set_otps":
        user_provider[user_id] = "SMS OTPs"
        await query.message.edit_text("✅ আপনার সার্ভার **SMS OTPs** এ সেট করা হয়েছে!")
        await asyncio.sleep(1)
        await start(update, context)

    elif data == "main_menu":
        await start(update, context)

    elif data == "menu_get_number":
        provider = user_provider.get(user_id, "SMS Bower")

        await query.message.edit_text(f"⏳ {provider} থেকে নম্বর আনা হচ্ছে...")

        action_keyboard = [
            [
                InlineKeyboardButton(
                    "🗺️ Change Country", callback_data="change_country"
                ),
                InlineKeyboardButton(
                    "🔄 Change Number", callback_data="menu_get_number"
                ),
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_activation")],
        ]

        msg = await query.message.reply_text(
            f"📱 **Service:** Telegram\n"
            f"🌐 **Provider:** {provider}\n"
            f"📞 **Number:** `+22896653643`\n\n"
            f"⏱️ **Elapsed Time:** 00:00s\n"
            f"⏳ SMS এর জন্য অপেক্ষা করা হচ্ছে...",
            reply_markup=InlineKeyboardMarkup(action_keyboard),
            parse_mode="Markdown",
        )

        context.job_queue.run_repeating(
            update_timer,
            interval=5,
            first=1,
            data={"msg_id": msg.message_id, "chat_id": query.message.chat_id, "time": 0},
            name=str(msg.message_id),
        )

    elif data == "cancel_activation":
        jobs = context.job_queue.get_jobs_by_name(str(query.message.message_id))
        for job in jobs:
            job.schedule_removal()

        await query.message.edit_text("❌ নম্বর অ্যাক্টিভেশন বাতিল করা হয়েছে।")


async def update_timer(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    job.data["time"] += 5
    elapsed = job.data["time"]

    if elapsed >= 1200:
        job.schedule_removal()
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
            InlineKeyboardButton("🗺️ Change Country", callback_data="change_country"),
            InlineKeyboardButton("🔄 Change Number", callback_data="menu_get_number"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_activation")],
    ]

    try:
        await context.bot.edit_message_text(
            chat_id=job.data["chat_id"],
            message_id=job.data["msg_id"],
            text=f"📱 **Service:** Telegram\n"
            f"📞 **Number:** `+22896653643`\n\n"
            f"⏱️ **Elapsed Time:** {time_str}\n"
            f"⏳ SMS এর জন্য অপেক্ষা করা হচ্ছে...",
            reply_markup=InlineKeyboardMarkup(action_keyboard),
            parse_mode="Markdown",
        )
    except Exception:
        pass


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
