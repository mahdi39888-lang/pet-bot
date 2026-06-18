import logging
import os
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# ========== تنظیمات ==========
BOT_TOKEN = "8864556595:AAFUbKSbXh7kj8ggDqEM1VPGOmrrJj43lys"
GROQ_API_KEY = "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"
GROQ_MODEL = "llama3-70b-8192"

# ========== سیستم پرامپت ==========
SYSTEM_PROMPT = """You are GameMaster AI 🎮, a professional game guide assistant. You help players with ANY game in the world.

RULES:
- Always respond in the same language the user writes in (Persian/Farsi or English)
- For Persian questions → answer in Persian
- For English questions → answer in English
- Always provide DNS codes when relevant (use real gaming DNS servers)
- Be detailed, helpful and professional
- Use gaming emojis appropriately
- Format answers clearly with sections

DNS CODES FOR GAMING (always provide when asked about connection/lag/ping):
🌐 Shecan (Iran): 178.22.122.100 / 185.51.200.2
🌐 403 (Iran): 10.202.10.202 / 10.202.10.102  
🌐 Begzar (Iran): 185.55.226.26 / 185.55.225.25
🌐 Cloudflare: 1.1.1.1 / 1.0.0.1
🌐 Google: 8.8.8.8 / 8.8.4.4
🌐 OpenDNS: 208.67.222.222 / 208.67.220.220

When providing DNS:
- Primary DNS: [number]
- Secondary DNS: [number]
- Explain how to set it up briefly

Always structure long answers with:
• Clear sections with emojis
• Step by step when needed
• Tips and tricks section when relevant"""

# ========== تابع AI ==========
async def ask_groq(user_message: str, chat_history: list = None) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if chat_history:
        messages.extend(chat_history[-6:])
    
    messages.append({"role": "user", "content": user_message})
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]

# ========== ذخیره تاریخچه ==========
chat_histories = {}

def get_history(user_id):
    return chat_histories.get(str(user_id), [])

def add_to_history(user_id, role, content):
    uid = str(user_id)
    if uid not in chat_histories:
        chat_histories[uid] = []
    chat_histories[uid].append({"role": role, "content": content})
    if len(chat_histories[uid]) > 20:
        chat_histories[uid] = chat_histories[uid][-20:]

# ========== منوی اصلی ==========
def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎮 راهنمای بازی", callback_data="guide"),
            InlineKeyboardButton("🌐 کدهای DNS", callback_data="dns")
        ],
        [
            InlineKeyboardButton("⚡ کاهش پینگ", callback_data="ping"),
            InlineKeyboardButton("🏆 تاپ بازی‌ها", callback_data="topgames")
        ],
        [
            InlineKeyboardButton("❓ راهنمای ربات", callback_data="help"),
            InlineKeyboardButton("🗑 پاک کردن چت", callback_data="clear")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== دستور استارت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "گیمر"
    
    text = (
        f"╔══════════════════╗\n"
        f"║   🎮 GAMEMASTER AI   ║\n"
        f"╚══════════════════╝\n\n"
        f"سلام **{name}** عزیز! 👋\n\n"
        f"🤖 من یه هوش مصنوعی تخصصی برای بازی‌ام!\n"
        f"می‌تونم درباره **هر بازی در دنیا** کمکت کنم.\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **چی می‌تونم بکنم:**\n"
        f"🕹 راهنمای کامل هر بازی\n"
        f"🌐 کدهای DNS برای گیم بهتر\n"
        f"⚡ کاهش پینگ و لگ\n"
        f"🏆 معرفی بهترین بازی‌ها\n"
        f"💡 ترفندها و چیت‌کدها\n"
        f"🔧 حل مشکلات تکنیکی\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👇 از منو استفاده کن یا سوالت رو بنویس!"
    )
    
    await update.message.reply_text(
        text, 
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

# ========== دستور هلپ ==========
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔══════════════════╗\n"
        "║   ❓ راهنمای ربات   ║\n"
        "╚══════════════════╝\n\n"
        "🎮 **نحوه استفاده:**\n\n"
        "1️⃣ **سوال مستقیم بپرس:**\n"
        "   مثال: چطور در GTA V پول بدست بیارم؟\n\n"
        "2️⃣ **DNS بخواه:**\n"
        "   مثال: DNS برای بازی Fortnite بده\n\n"
        "3️⃣ **راهنمای بازی:**\n"
        "   مثال: راهنمای کامل Minecraft بده\n\n"
        "4️⃣ **مشکل تکنیکی:**\n"
        "   مثال: چرا پینگم بالاست؟\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📌 **دستورات:**\n"
        "/start — صفحه اصلی\n"
        "/dns — کدهای DNS\n"
        "/ping — کاهش پینگ\n"
        "/clear — پاک کردن تاریخچه\n"
        "/help — این صفحه\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💬 هر سوالی داری بپرس، من اینجام! 🤖"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== دستور DNS ==========
async def dns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔══════════════════╗\n"
        "║   🌐 کدهای DNS گیمینگ   ║\n"
        "╚══════════════════╝\n\n"
        "🇮🇷 **برای کاربران ایران:**\n\n"
        "🔷 **Shecan (شکن)**\n"
        "   Primary: `178.22.122.100`\n"
        "   Secondary: `185.51.200.2`\n\n"
        "🔷 **403**\n"
        "   Primary: `10.202.10.202`\n"
        "   Secondary: `10.202.10.102`\n\n"
        "🔷 **Begzar (بگذر)**\n"
        "   Primary: `185.55.226.26`\n"
        "   Secondary: `185.55.225.25`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🌍 **بین‌المللی:**\n\n"
        "⚡ **Cloudflare (سریع‌ترین)**\n"
        "   Primary: `1.1.1.1`\n"
        "   Secondary: `1.0.0.1`\n\n"
        "🔵 **Google**\n"
        "   Primary: `8.8.8.8`\n"
        "   Secondary: `8.8.4.4`\n\n"
        "🟠 **OpenDNS**\n"
        "   Primary: `208.67.222.222`\n"
        "   Secondary: `208.67.220.220`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 برای DNS اختصاصی یه بازی خاص بپرس!"
    )
    
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")

# ========== دستور پینگ ==========
async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔══════════════════╗\n"
        "║   ⚡ کاهش پینگ و لگ   ║\n"
        "╚══════════════════╝\n\n"
        "🔧 **روش‌های کاهش پینگ:**\n\n"
        "1️⃣ **تغییر DNS**\n"
        "   از Cloudflare استفاده کن:\n"
        "   `1.1.1.1` و `1.0.0.1`\n\n"
        "2️⃣ **اینترنت کابلی**\n"
        "   بجای WiFi از کابل LAN استفاده کن\n\n"
        "3️⃣ **بستن برنامه‌های پس‌زمینه**\n"
        "   Chrome, Discord, آپدیت‌ها رو ببند\n\n"
        "4️⃣ **انتخاب سرور نزدیک**\n"
        "   سرور ایران یا خاورمیانه انتخاب کن\n\n"
        "5️⃣ **بهینه‌سازی ویندوز**\n"
        "   Game Mode رو فعال کن\n"
        "   تنظیمات → Gaming → Game Mode\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💬 برای راهنمای اختصاصی یه بازی خاص بپرس!"
    )
    
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")

# ========== پاک کردن تاریخچه ==========
async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    chat_histories.pop(uid, None)
    
    text = "🗑 **تاریخچه چت پاک شد!**\n\nمی‌تونی یه مکالمه جدید شروع کنی. 🎮"
    
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")

# ========== کالبک منو ==========
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "dns":
        await dns_cmd(update, context)
    
    elif query.data == "ping":
        await ping_cmd(update, context)
    
    elif query.data == "clear":
        await clear_cmd(update, context)
    
    elif query.data == "help":
        text = (
            "╔══════════════════╗\n"
            "║   ❓ راهنمای ربات   ║\n"
            "╚══════════════════╝\n\n"
            "🎮 **نحوه استفاده:**\n\n"
            "1️⃣ سوالت رو مستقیم بنویس\n"
            "2️⃣ از منوی پایین استفاده کن\n"
            "3️⃣ اسم بازی رو بنویس\n\n"
            "💡 **مثال سوالات:**\n"
            "• چطور در Minecraft خانه بسازم؟\n"
            "• DNS برای PUBG چیه؟\n"
            "• بهترین تاکتیک در Valorant؟\n"
            "• چرا بازی کرش میکنه؟\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🤖 هر سوالی داری بپرس!"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif query.data == "guide":
        text = (
            "🎮 **راهنمای بازی**\n\n"
            "اسم بازی مورد نظرت رو بنویس!\n\n"
            "مثال:\n"
            "• راهنمای GTA V\n"
            "• راهنمای Minecraft\n"
            "• راهنمای PUBG\n"
            "• راهنمای Fortnite\n\n"
            "🤖 من درباره هر بازی در دنیا اطلاعات دارم!"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif query.data == "topgames":
        text = (
            "╔══════════════════╗\n"
            "║   🏆 برترین بازی‌ها   ║\n"
            "╚══════════════════╝\n\n"
            "🥇 **محبوب‌ترین بازی‌های آنلاین:**\n"
            "1. 🔫 Valorant\n"
            "2. 🪂 PUBG\n"
            "3. ⚽ FIFA 25\n"
            "4. 🏰 Fortnite\n"
            "5. ⚔️ League of Legends\n\n"
            "🎯 **بازی‌های داستانی:**\n"
            "1. 🕷 Spider-Man 2\n"
            "2. 🧟 The Last of Us\n"
            "3. ⚔️ God of War\n"
            "4. 🌍 GTA V\n"
            "5. 🗡 Elden Ring\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💬 برای راهنمای هر کدوم بپرس!"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

# ========== پردازش پیام ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # نمایش تایپینگ
    await update.message.chat.send_action("typing")
    
    try:
        history = get_history(user_id)
        response = await ask_groq(user_message, history)
        
        add_to_history(user_id, "user", user_message)
        add_to_history(user_id, "assistant", response)
        
        # اضافه کردن فوتر
        final_response = (
            f"{response}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎮 *GameMaster AI* | سوال دیگه‌ای داری؟"
        )
        
        await update.message.reply_text(
            final_response,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        
    except Exception as e:
        await update.message.reply_text(
            "⚠️ **خطا در اتصال به AI**\n\n"
            "لطفاً چند ثانیه صبر کن و دوباره امتحان کن.\n"
            "اگه مشکل ادامه داشت /start بزن.",
            parse_mode="Markdown"
        )

# ========== اجرا ==========
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("dns", dns_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🎮 GameMaster AI Bot شروع به کار کرد! ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
