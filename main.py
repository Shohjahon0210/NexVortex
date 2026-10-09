import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    BotCommand,
)
from aiogram.exceptions import TelegramBadRequest
from mcstatus import JavaServer

# ==================== SOZLAMALAR (O'ZGARTIRILMADI) ====================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "TOKEN"

# Server ma'lumotlari
SERVER_DOMAIN = "NexVortex.aternos.me"
SERVER_PORT = 28099
ATERNOS_URL = "https://aternos.org/servers/"

# Kanal va Adminlar sozlamasi
REQUIRED_CHANNEL = "@BaxtiyorovFamily"
CHANNEL_URL = "https://t.me/BaxtiyorovFamily"

# ADMINLAR RO'YXATI
ADMIN_IDS = [
    8497572065,
]

# Server egasi / Admin Telegram kontakti
ADMIN_CONTACT = "@baxtiyorov_admin1"
# =====================================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ----------------- YORDAMCHI FUNKSIYALAR -----------------
async def check_subscription(user_id: int) -> bool:
    """Foydalanuvchi kanalga a'zo bo'lganini tekshirish."""
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True

async def delete_previous_message(message: Message):
    """Eski xabarni o'chirish (Chat toza turishi uchun)."""
    try:
        await message.delete()
    except TelegramBadRequest:
        pass

# ----------------- TUGMALAR (KEYBOARDS) -----------------
def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Foydalanuvchi turiga qarab menyu chiqaradi."""
    keyboard_buttons = []
    
    if user_id in ADMIN_IDS:
        keyboard_buttons.append([KeyboardButton(text="🎮 Serverni yoqish")])

    keyboard_buttons.extend([
        [KeyboardButton(text="📋 Server manzili"), KeyboardButton(text="📊 Holat")],
        [KeyboardButton(text="🛒 OP / Huquq xarid qilish"), KeyboardButton(text="🆘 Yordam")],
    ])

    return ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)

def get_sub_inline_keyboard() -> InlineKeyboardMarkup:
    """Majburiy obuna tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")],
        ]
    )

# ----------------- HANDLERLAR -----------------

@dp.message(CommandStart())
async def start_command(message: Message):
    await delete_previous_message(message)

    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(
            "⚠️ **Botdan foydalanish uchun rasmiy kanalimizga obuna bo'ling!**\n\n"
            "Obuna bo'lgach, **\"✅ Obunani tekshirish\"** tugmasini bosing.",
            reply_markup=get_sub_inline_keyboard(),
            parse_mode="Markdown",
        )
        return

    admin_note = " 👑 *(Admin)*" if message.from_user.id in ADMIN_IDS else ""
    await message.answer(
        f"🔥 **Aternos Minecraft Server Botiga xush kelibsiz!**{admin_note}\n\n"
        "Kerakli bo'limni tanlang 👇",
        reply_markup=get_main_keyboard(message.from_user.id),
        parse_mode="Markdown",
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    is_subscribed = await check_subscription(callback.from_user.id)
    if is_subscribed:
        await callback.message.delete()
        await callback.message.answer(
            "✅ **A'zolik tasdiqlandi!** Botdan foydalanishingiz mumkin.",
            reply_markup=get_main_keyboard(callback.from_user.id),
            parse_mode="Markdown",
        )
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

# 🎮 SERVERNI YOQISH (FAQAT ADMINLAR UCHUN)
@dp.message(F.text == "🎮 Serverni yoqish")
async def start_server_action(message: Message):
    await delete_previous_message(message)

    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ **Ushbu bo'lim faqat Server Adminlari uchun!**", parse_mode="Markdown")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Google Brauzerda Aternos Panelini Ochish",
                    url=ATERNOS_URL,
                )
            ]
        ]
    )

    await message.answer(
        "⚡ **Serverni Ishga Tushirish (Admin Paneli)**\n\n"
        "Tugmani bosing, brauzerda Aternos paneli ochiladi. U yerdan **Start** tugmasini bosing.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )

# 📋 SERVER MANZILI (/server buyrug'i yoki tugmasi)
@dp.message(F.text.in_({"📋 Server manzili", "/server"}))
async def show_address_action(message: Message):
    await delete_previous_message(message)

    if not await check_subscription(message.from_user.id):
        await message.answer("⚠️ Avval kanalga obuna bo'ling!", reply_markup=get_sub_inline_keyboard())
        return

    address_text = (
        "🌐 **MINECRAFT SERVER MA'LUMOTLARI** 🌐\n\n"
        f"📌 **Server Nomi:** NexVortex Server\n"
        f"🔗 **IP / Manzil:** `{SERVER_DOMAIN}`\n"
        f"🔌 **Port:** `{SERVER_PORT}`\n"
        f"🎮 **O'yin Versiyasi:** Java va Bedrock Edition\n\n"
        "💡 *Nusxalash uchun IP ustiga bir marta bosing!*"
    )
    await message.answer(address_text, parse_mode="Markdown")

# 📊 HOLAT VA STATISTIKA (/status buyrug'i yoki tugmasi)
@dp.message(F.text.in_({"📊 Holat", "/status"}))
async def show_status_action(message: Message):
    await delete_previous_message(message)

    if not await check_subscription(message.from_user.id):
        await message.answer("⚠️ Avval kanalga obuna bo'ling!", reply_markup=get_sub_inline_keyboard())
        return

    wait_msg = await message.answer("🔎 *Server holati tekshirilmoqda...*", parse_mode="Markdown")

    try:
        server = await JavaServer.async_lookup(SERVER_DOMAIN)
        status = await server.async_status()

        online_players = status.players.online
        max_players = status.players.max
        latency = round(status.latency)

        player_list = ""
        if status.players.sample:
            names = [p.name for p in status.players.sample]
            player_list = "\n\n👥 **Onlayn o'yinchilar:**\n`" + ", ".join(names) + "`"

        status_text = (
            f"🟢 **SERVER ONLAYN!**\n\n"
            f"📊 **O'yinchilar:** {online_players} / {max_players}\n"
            f"⚡ **Ping:** {latency} ms"
            f"{player_list}"
        )
    except Exception:
        status_text = (
            "🔴 **SERVER OFFLINE (O'chiq)**\n\n"
            "Server hozirda o'chirilgan. Yoqish uchun Adminlarga murojaat qiling!"
        )

    await wait_msg.delete()
    await message.answer(status_text, parse_mode="Markdown")

# 🛒 OP / HUQUQ XARID QILISH (/shop buyrug'i yoki tugmasi)
@dp.message(F.text.in_({"🛒 OP / Huquq xarid qilish", "/shop"}))
async def buy_op_action(message: Message):
    await delete_previous_message(message)

    clean_contact = ADMIN_CONTACT.replace("_", "\\_")

    shop_text = (
        "💎 **SERVERDA HUQUQ VA OP XARID QILISH** 💎\n\n"
        "Serverimizda quyidagi maqomlarni xarid qilishingiz mumkin:\n"
        "• 👑 **VIP Admin** - Barcha huquqlar va maxsus buyruqlar.\n"
        "• ⚔️ **OP Maqomi** - Creative va teleport yetakchiliklari.\n"
        "• 📦 **Donat Keyslar** - Noyob resurslar va qurollar.\n\n"
        f"📞 **Sotib olish uchun Admin bilan bog'laning:** {clean_contact}"
    )
    await message.answer(shop_text, parse_mode="Markdown")

# 🆘 YORDAM (/help buyrug'i yoki tugmasi)
@dp.message(F.text.in_({"🆘 Yordam", "/help"}))
async def help_action(message: Message):
    await delete_previous_message(message)

    clean_contact = ADMIN_CONTACT.replace("_", "\\_")

    help_text = (
        "❓ **KO'P BERILADIGAN SAVOLLAR VA YORDAM**\n\n"
        "1️⃣ **Serverga qanday kiriladi?**\n"
        f"   Minecraft -> MultiPlayer -> Add Server -> IP o'rniga `{SERVER_DOMAIN}` va Portga `{SERVER_PORT}` kiriting.\n\n"
        "2️⃣ **Server kirmayapti (Can't connect)?**\n"
        "   Server o'chiq bo'lishi mumkin. **📊 Holat** bo'limidan server yoqilganini tekshiring.\n\n"
        "3️⃣ **Serverni kim yoqa oladi?**\n"
        "   Serverni faqat tayinlangan Adminlar Aternos paneli orqali yoqa oladi.\n\n"
        f"📩 **Boshqa savol yoki yordam kerak bo'lsa, adminga yozing:** {clean_contact}"
    )
    await message.answer(help_text, parse_mode="Markdown")

# ----------------- MAIN RUNNER -----------------
async def main():
    if TOKEN == "BOT_TOKENINGIZNI_SHUYERGA_YOZING" or not TOKEN:
        print("XATO: Bot token kiritilmagan!")
        return

    # Bot menyusiga buyruqlarni avtomatik joylash
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="server", description="Server IP va Port ma'lumotlari"),
        BotCommand(command="status", description="Server holati va onlaynlar"),
        BotCommand(command="help", description="Yordam va qo'llab-quvvatlash"),
        BotCommand(command="shop", description="OP va donat xarid qilish"),
    ]
    await bot.set_my_commands(commands)

    print("🔥 NexVortex Server Boti muvaffaqiyatli ishga tushdi...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
