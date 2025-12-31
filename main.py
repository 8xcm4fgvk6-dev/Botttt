from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

TOKEN = "BOT_TOKENINGNI_BU_YERGA_QOY"
ADMIN_ID = 123456789  # o'zingni Telegram ID
CHANNEL_ID = "@kanal_username"  # majburiy obuna kanali

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ===== DATABASE =====
conn = sqlite3.connect("movies.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    code TEXT PRIMARY KEY,
    file_id TEXT,
    views INTEGER DEFAULT 0
)
""")
conn.commit()

# ===== BUTTONS =====
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎬 Kino kodlari", callback_data="list"),
        InlineKeyboardButton("➕ Admin", callback_data="admin")
    )
    return kb

# ===== START =====
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, msg.from_user.id)
        if member.status in ["left", "kicked"]:
            await msg.answer(f"❗ Avval kanalga obuna bo‘ling:\n{CHANNEL_ID}")
            return
    except:
        pass

    await msg.answer(
        "🎥 Kino botga xush kelibsiz!\n\n"
        "📌 Kino kodini yuboring",
        reply_markup=main_menu()
    )

# ===== CALLBACKS =====
@dp.callback_query_handler()
async def callbacks(call: types.CallbackQuery):
    if call.data == "list":
        cursor.execute("SELECT code FROM movies")
        rows = cursor.fetchall()
        if not rows:
            await call.message.answer("❌ Hali kino yo‘q")
        else:
            text = "🎬 Mavjud kodlar:\n\n" + "\n".join([r[0] for r in rows])
            await call.message.answer(text)

    elif call.data == "admin":
        if call.from_user.id != ADMIN_ID:
            await call.message.answer("❌ Siz admin emassiz")
            return
        await call.message.answer(
            "📥 Kino qo‘shish:\n"
            "Videoga reply qilib:\n"
            "`/save KOD` deb yozing",
            parse_mode="Markdown"
        )

# ===== SAVE MOVIE =====
@dp.message_handler(commands=["save"])
async def save_movie(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return

    if not msg.reply_to_message or not msg.reply_to_message.video:
        await msg.answer("❌ Videoga reply qiling")
        return

    try:
        code = msg.text.split()[1]
    except:
        await msg.answer("❌ Kod yozilmadi. Masalan: /save A12")
        return

    file_id = msg.reply_to_message.video.file_id
    cursor.execute(
        "INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)",
        (code, file_id)
    )
    conn.commit()

    await msg.answer(f"✅ Kino saqlandi!\nKod: {code}")

# ===== USER SEND CODE =====
@dp.message_handler()
async def send_movie(msg: types.Message):
    code = msg.text.strip()
    cursor.execute("SELECT file_id FROM movies WHERE code=?", (code,))
    row = cursor.fetchone()

    if row:
        await msg.answer_video(row[0])
        cursor.execute("UPDATE movies SET views = views + 1 WHERE code=?", (code,))
        conn.commit()
    else:
        await msg.answer("❌ Bunday kod topilmadi")

if __name__ == "__main__":
    executor.start_polling(dp)
