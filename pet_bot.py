import logging
import json
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

# ========== تنظیمات ==========
BOT_TOKEN = "8864556595:AAFUbKSbXh7kj8ggDqEM1VPGOmrrJj43lys"
DATA_FILE = "users.json"
COOLDOWN_MINUTES = 5
COIN_REWARD = 10

# ========== ساختار حیوانات ==========
PETS = {
    "cat": {
        "name": "گربه 🐱",
        "buy_price": 50,
        "levels": [
            {"name": "گربه معمولی 🐱", "wallet_capacity": 200},
            {"name": "گربه خوشگل 😻", "wallet_capacity": 400, "upgrade_cost": 100},
            {"name": "گربه سلطنتی 👑🐱", "wallet_capacity": 800, "upgrade_cost": 200},
        ]
    },
    "dog": {
        "name": "سگ 🐶",
        "buy_price": 50,
        "levels": [
            {"name": "سگ معمولی 🐶", "wallet_capacity": 200},
            {"name": "سگ باهوش 🦮", "wallet_capacity": 400, "upgrade_cost": 100},
            {"name": "سگ قهرمان 🏆🐶", "wallet_capacity": 800, "upgrade_cost": 200},
        ]
    }
}

# ========== مدیریت داده ==========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "coins": 50,
            "wallet": 0,
            "pet": None,
            "pet_level": 0,
            "last_collect": None
        }
    return data[uid]

def wallet_capacity(user):
    if not user["pet"]:
        return 100
    pet_type = user["pet"]
    level = user["pet_level"]
    return PETS[pet_type]["levels"][level]["wallet_capacity"]

def pet_display_name(user):
    if not user["pet"]:
        return "ندارید ❌"
    pet_type = user["pet"]
    level = user["pet_level"]
    return PETS[pet_type]["levels"][level]["name"]

def name_of(update):
    return update.effective_user.first_name or "دوست"

# ========== دستورات ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)
    save_data(data)
    n = name_of(update)

    cap = wallet_capacity(user)
    bar_filled = int((user["wallet"] / cap) * 8) if cap > 0 else 0
    bar = "🟨" * bar_filled + "⬜" * (8 - bar_filled)

    text = (
        f"🎮 *سلام {n}! به دنیای حیوانات خوش اومدی!*\n"
        f"{'─' * 25}\n\n"
        f"💰 سکه: *{user['coins']}*\n"
        f"👜 کیف پول: *{user['wallet']}* / {cap}\n"
        f"{bar}\n"
        f"🐾 حیوان: {pet_display_name(user)}\n\n"
        f"{'─' * 25}\n"
        f"📋 *دستورات:*\n"
        f"🛒 /shop — خرید حیوان\n"
        f"⬆️ /upgrade — ارتقا\n"
        f"👜 /wallet — کیف پول\n"
        f"💸 /collect — برداشت سکه\n"
        f"🐱 /miow — سکه بگیر (گربه)\n"
        f"🐶 /hap — سکه بگیر (سگ)\n"
        f"🏆 /top — برترین بازیکنان"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)
    save_data(data)

    if user["pet"]:
        await update.message.reply_text(
            f"🐾 تو قبلاً *{pet_display_name(user)}* داری!\n"
            f"برای ارتقا: /upgrade",
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton(f"🐱 گربه — {PETS['cat']['buy_price']} سکه", callback_data="buy_cat")],
        [InlineKeyboardButton(f"🐶 سگ — {PETS['dog']['buy_price']} سکه", callback_data="buy_dog")],
    ]
    text = (
        f"🛒 *فروشگاه حیوانات*\n"
        f"{'─' * 20}\n\n"
        f"💰 سکه‌های تو: *{user['coins']}*\n\n"
        f"یه همراه برای خودت انتخاب کن! 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user = get_user(data, query.from_user.id)

    pet_type = query.data.replace("buy_", "")
    price = PETS[pet_type]["buy_price"]

    if user["pet"]:
        await query.edit_message_text("🐾 قبلاً یه حیوان داری!")
        return

    if user["coins"] < price:
        await query.edit_message_text(
            f"❌ سکه کافی نداری!\n💰 داری: {user['coins']} | نیاز: {price}"
        )
        return

    user["coins"] -= price
    user["pet"] = pet_type
    user["pet_level"] = 0
    save_data(data)

    cmd = "/miow" if pet_type == "cat" else "/hap"
    await query.edit_message_text(
        f"🎉 *{PETS[pet_type]['name']} رو خریدی!*\n\n"
        f"👜 ظرفیت کیف پول: {wallet_capacity(user)} سکه\n\n"
        f"⏱ هر {COOLDOWN_MINUTES} دقیقه {cmd} بزن تا سکه بگیری!",
        parse_mode="Markdown"
    )

async def collect_coins(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    data = load_data()
    user = get_user(data, update.effective_user.id)
    n = name_of(update)

    if not user["pet"]:
        await update.message.reply_text("❌ اول یه حیوان بخر! /shop")
        return

    if command == "miow" and user["pet"] != "cat":
        await update.message.reply_text("🐶 تو سگ داری! از /hap استفاده کن!")
        return
    if command == "hap" and user["pet"] != "dog":
        await update.message.reply_text("🐱 تو گربه داری! از /miow استفاده کن!")
        return

    now = datetime.now()
    if user["last_collect"]:
        last = datetime.fromisoformat(user["last_collect"])
        diff = now - last
        if diff < timedelta(minutes=COOLDOWN_MINUTES):
            remaining = timedelta(minutes=COOLDOWN_MINUTES) - diff
            mins = int(remaining.total_seconds() // 60)
            secs = int(remaining.total_seconds() % 60)
            await update.message.reply_text(
                f"⏳ *{n}* صبر کن!\n"
                f"🕐 {mins} دقیقه و {secs} ثانیه دیگه می‌تونی سکه بگیری.",
                parse_mode="Markdown"
            )
            return

    cap = wallet_capacity(user)
    if user["wallet"] >= cap:
        await update.message.reply_text(
            f"👜 کیف پولت *پره!* ({user['wallet']}/{cap})\n"
            f"💸 با /collect سکه‌هاتو بردار\n"
            f"⬆️ یا با /upgrade ظرفیت رو بیشتر کن!",
            parse_mode="Markdown"
        )
        return

    added = min(COIN_REWARD, cap - user["wallet"])
    user["wallet"] += added
    user["last_collect"] = now.isoformat()
    save_data(data)

    cap2 = wallet_capacity(user)
    bar_filled = int((user["wallet"] / cap2) * 8)
    bar = "🟨" * bar_filled + "⬜" * (8 - bar_filled)

    if command == "miow":
        emoji = "🐱 *میووو!*"
    else:
        emoji = "🐶 *هاپ هاپ!*"

    await update.message.reply_text(
        f"{emoji}\n\n"
        f"🪙 *+{added} سکه* به کیف پولت اضافه شد!\n"
        f"👜 {user['wallet']} / {cap2}\n{bar}",
        parse_mode="Markdown"
    )

async def miow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await collect_coins(update, context, "miow")

async def hap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await collect_coins(update, context, "hap")

async def wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)
    save_data(data)

    cap = wallet_capacity(user)
    bar_filled = int((user["wallet"] / cap) * 10) if cap > 0 else 0
    bar = "🟨" * bar_filled + "⬜" * (10 - bar_filled)
    percent = int((user["wallet"] / cap) * 100) if cap > 0 else 0

    text = (
        f"👜 *کیف پول*\n"
        f"{'─' * 20}\n\n"
        f"{bar} {percent}%\n"
        f"💰 {user['wallet']} / {cap} سکه\n\n"
        f"🪙 سکه‌های آزاد: *{user['coins']}*\n"
        f"🐾 حیوان: {pet_display_name(user)}\n\n"
        f"💸 برداشت: /collect\n"
        f"⬆️ ارتقا: /upgrade"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)

    if user["wallet"] == 0:
        await update.message.reply_text(
            "👜 کیف پولت خالیه!\n"
            "🐱 /miow یا 🐶 /hap بزن تا سکه جمع کنی."
        )
        return

    amount = user["wallet"]
    user["coins"] += amount
    user["wallet"] = 0
    save_data(data)

    await update.message.reply_text(
        f"✅ *{amount} سکه* برداشت شد!\n"
        f"💰 موجودی کل: *{user['coins']}* سکه 🎉",
        parse_mode="Markdown"
    )

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)
    save_data(data)

    if not user["pet"]:
        await update.message.reply_text("❌ اول یه حیوان بخر! /shop")
        return

    pet_type = user["pet"]
    level = user["pet_level"]
    max_level = len(PETS[pet_type]["levels"]) - 1

    if level >= max_level:
        await update.message.reply_text(
            f"✨ *{pet_display_name(user)}* بیشترین سطح رو داره!\n"
            f"👜 ظرفیت کیف پول: {wallet_capacity(user)} سکه",
            parse_mode="Markdown"
        )
        return

    next_level = PETS[pet_type]["levels"][level + 1]
    cost = next_level["upgrade_cost"]

    keyboard = [[InlineKeyboardButton(f"⬆️ ارتقا — {cost} سکه", callback_data="upgrade_confirm")]]
    text = (
        f"⬆️ *ارتقای حیوان*\n"
        f"{'─' * 20}\n\n"
        f"📍 فعلی: {pet_display_name(user)}\n"
        f"🎯 بعدی: {next_level['name']}\n"
        f"👜 ظرفیت جدید: {next_level['wallet_capacity']} سکه\n\n"
        f"💰 موجودی: *{user['coins']}* | هزینه: *{cost}*"
    )
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def upgrade_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user = get_user(data, query.from_user.id)

    pet_type = user["pet"]
    level = user["pet_level"]
    max_level = len(PETS[pet_type]["levels"]) - 1

    if level >= max_level:
        await query.edit_message_text("✨ حیوانت قبلاً بیشترین سطح رو داره!")
        return

    next_level = PETS[pet_type]["levels"][level + 1]
    cost = next_level["upgrade_cost"]

    if user["coins"] < cost:
        await query.edit_message_text(
            f"❌ سکه کافی نداری!\n💰 داری: {user['coins']} | نیاز: {cost}"
        )
        return

    user["coins"] -= cost
    user["pet_level"] += 1
    save_data(data)

    await query.edit_message_text(
        f"🎉 *ارتقا موفق!*\n\n"
        f"🐾 {pet_display_name(user)}\n"
        f"👜 ظرفیت جدید کیف پول: *{wallet_capacity(user)}* سکه",
        parse_mode="Markdown"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("هنوز کسی بازی نکرده! 🎮")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1].get("coins", 0) + x[1].get("wallet", 0), reverse=True)
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    text = f"🏆 *برترین بازیکنان*\n{'─' * 20}\n\n"
    for i, (uid, u) in enumerate(sorted_users[:5]):
        total = u.get("coins", 0) + u.get("wallet", 0)
        pet = pet_display_name(u)
        medal = medals[i] if i < len(medals) else f"{i+1}."
        text += f"{medal} کاربر {uid[:6]}... | 💰 {total} | {pet}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ========== اجرا ==========
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("wallet", wallet_cmd))
    app.add_handler(CommandHandler("collect", collect))
    app.add_handler(CommandHandler("upgrade", upgrade))
    app.add_handler(CommandHandler("miow", miow))
    app.add_handler(CommandHandler("hap", hap))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(upgrade_confirm, pattern="^upgrade_confirm$"))

    print("ربات شروع به کار کرد! ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
