import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
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

# ==================== SOZLAMALAR ====================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Server ma'lumotlari
SERVER_DOMAIN = "NexVortex.aternos.me"
SERVER_PORT = 28099
ATERNOS_URL = "https://aternos.org/servers/"

# Kanal va Adminlar sozlamasi
REQUIRED_CHANNEL = "@BaxtiyorovFamily"
CHANNEL_URL = "https://t.me/BaxtiyorovFamily"

# Asosiy (Bosh) Admin ID si va .env manzili
MAIN_ADMIN_ID = 8497572065
ENV_FILE_PATH = ".env"

# Server egasi / Admin Telegram kontakti
ADMIN_CONTACT = "@baxtiyorov_admin1"
# =====================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ----------------- ADMINLARNI DIYNAMIK O'QISH VA SAQLASH -----------------
def get_admin_ids() -> list[int]:
    """.env fayli va os.environ dan barcha admin ID larini o'qib oladi."""
    admins = {MAIN_ADMIN_ID}  # Asosiy admin har doim ro'yxatda bo'ladi
    
    # Muhit o'zgaruvchisidan o'qish
    raw_admins = os.getenv("ADMIN_IDS", "")
    for aid in raw_admins.split(","):
        if aid.strip().isdigit():
            admins.add(int(aid.strip()))
            
    # .env faylidan ham qo'shimcha tekshirib o'qish
    if os.path.exists(ENV_FILE_PATH):
        try:
            with open(ENV_FILE_PATH, "r") as f:
                for line in f:
                    if line.startswith("ADMIN_IDS="):
                        val = line.strip().split("=", 1)[1].strip('"\'')
                        for aid in val.split(","):
                            if aid.strip().isdigit():
                                admins.add(int(aid.strip()))
        except Exception:
            pass
            
    return list(admins)

def save_admin_ids(admin_list: list[int]):
    """.env fayliga barcha admin ID larini saqlaydi."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", TOKEN or "")
    unique_admins = list(set(admin_list))
    admin_str = ",".join(map(str, unique_admins))
    
    # OS Muhitini yangilash
    os.environ["ADMIN_IDS"] = admin_str
    
    # .env faylga yozish
    try:
        with open(ENV_FILE_PATH, "w") as f:
            f.write(f'TELEGRAM_BOT_TOKEN="{token}"\n')
            f.write(f'ADMIN_IDS="{admin_str}"\n')
    except Exception as e:
        print(f".env faylga saqlashda xatolik: {e}")

# ----------------- YORDAMCHI FUNKSIYALAR -----------------
async def check_subscription(user_id: int) -> bool:
    """Foydalanuvchi kanalga a'zo bo'lganini tekshirish."""
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True

async def delete_previous_message(message: Message):
    """Eski xabarni o'chirish."""
    try:
        await message.delete()
    except TelegramBadRequest:
        pass

# ----------------- TUGMALAR (KEYBOARDS) -----------------
def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Foydalanuvchi turiga qarab menyu chiqaradi."""
    keyboard_buttons = []
    
    if user_id in get_admin_ids():
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

    admin_note = " 👑 *(Admin)*" if message.from_user.id in get_admin_ids() else ""
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

# 👥 ADMINLAR RO'YXATI VA SONI (/admins)
@dp.message(Command("admins"))
async def list_admins_command(message: Message):
    admins = get_admin_ids()
    if message.from_user.id not in admins:
        return

    text = f"👑 **ADMINLAR BOSHQARUVI**\n\n"
    text += f"📊 **Jami adminlar soni:** {len(admins)} ta\n\n"
    text += "📋 **Adminlar Telegram ID lari:**\n"
    for aid in admins:
        crown = " ⭐️ (Bosh admin)" if aid == MAIN_ADMIN_ID else ""
        text += f"• `{aid}`{crown}\n"

    text += "\n➕ *Yangi admin qo'shish uchun:* `/addadmin TELEGRAM_ID`"
    await message.answer(text, parse_mode="Markdown")

# ➕ YANGI ADMIN QO'SHISH (/addadmin 123456789)
@dp.message(Command("addadmin"))
async def add_admin_command(message: Message):
    admins = get_admin_ids()
    if message.from_user.id not in admins:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer("⚠️ **Xato format!**\nIshlatilishi: `/addadmin 123456789`", parse_mode="Markdown")
        return

    new_admin_id = int(args[1].strip())
    if new_admin_id in admins:
        await message.answer("ℹ️ Bu foydalanuvchi allaqachon adminlar ro'yxatida mavjud.")
        return

    admins.append(new_admin_id)
    save_admin_ids(admins)

    await message.answer(
        f"✅ **Muvaffaqiyatli!**\n`{new_admin_id}` ID egasi admin qilib qo'shildi va `.env` fayliga saqlandi.",
        parse_mode="Markdown",
    )

# 🎮 SERVERNI YOQISH (FAQAT ADMINLAR UCHUN)
@dp.message(F.text == "🎮 Serverni yoqish")
async def start_server_action(message: Message):
    await delete_previous_message(message)

    if message.from_user.id not in get_admin_ids():
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

# 📋 SERVER MANZILI
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

# 📊 HOLAT VA STATISTIKA
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

# 🛒 OP / HUQUQ XARID QILISH
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

# 🆘 YORDAM
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
    if not TOKEN:
        print("XATO: Bot token kiritilmagan!")
        return

    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="server", description="Server IP va Port ma'lumotlari"),
        BotCommand(command="status", description="Server holati va onlaynlar"),
        BotCommand(command="admins", description="Adminlar ro'yxati va soni"),
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
