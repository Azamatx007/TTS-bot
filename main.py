import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

from TTS.api import TTS
from pydub import AudioSegment

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== TTS LOAD =====
print("AI Model yuklanmoqda...")
# RAMni tejash uchun gpu=False (Railway uchun mos)
tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", gpu=False)
print("Tayyor!")

# ===== USER PAPKA =====
def get_user_dir(user_id):
    path = f"users/{user_id}"
    os.makedirs(path, exist_ok=True)
    return path

# ===== START KOMANDASI =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Assalomu alaykum! Men Ovoz Klonlash botiman.**\n\n"
        "Men sizning ovozingizni o'rganib, siz yozgan matnni o'sha ovozda o'qib bera olaman.\n\n"
        "**Qanday ishlatiladi?**\n"
        "1️⃣ Menga ovozli xabar yoki audio fayl yuboring 🎤\n"
        "2️⃣ Men uni tahlil qilaman.\n"
        "3️⃣ Keyin matn yuboring va natijani MP3 holatida oling! ✍️"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# ===== AUDIO/VOICE HANDLER =====
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_dir = get_user_dir(user_id)
    
    # Voice yoki Audio ekanligini aniqlash
    if update.message.voice:
        audio_file = await update.message.voice.get_file()
        ext = "ogg"
    else:
        audio_file = await update.message.audio.get_file()
        ext = update.message.audio.file_name.split('.')[-1]

    input_path = os.path.join(user_dir, f"input.{ext}")
    wav_path = os.path.join(user_dir, "voice.wav")

    await audio_file.download_to_drive(input_path)

    # Har qanday formatni WAV ga o'tkazish (TTS talabi)
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(wav_path, format="wav")
        os.remove(input_path) # Keraksiz faylni o'chirish
        await update.message.reply_text("✅ Ovoz namunasi qabul qilindi! Endi matn yuboring.")
    except Exception as e:
        await update.message.reply_text("❌ Audioni qayta ishlashda xatolik yuz berdi.")

# ===== TEXT HANDLER =====
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_dir = get_user_dir(user_id)
    wav_path = os.path.join(user_dir, "voice.wav")
    output_mp3 = os.path.join(user_dir, "output.mp3")
    output_wav = os.path.join(user_dir, "output.wav")

    if not os.path.exists(wav_path):
        await update.message.reply_text("🎤 Avval ovoz namunangizni yuboring!")
        return

    text = update.message.text
    wait_msg = await update.message.reply_text("⏳ AI ishlamoqda, kuting...")

    try:
        # TTS orqali WAV yaratish
        tts.tts_to_file(
            text=text,
            speaker_wav=wav_path,
            language="en", # 'en' yoki 'tr' o'zbekchaga o'xshashroq chiqadi
            file_path=output_wav
        )

        # WAV ni MP3 ga o'tkazish
        audio = AudioSegment.from_wav(output_wav)
        audio.export(output_mp3, format="mp3")

        # MP3 yuborish
        with open(output_mp3, "rb") as f:
            await update.message.reply_audio(audio=f, filename="voice_cloned.mp3", title="Sizning ovozingiz")

        await wait_msg.delete()
        # Tozalash
        if os.path.exists(output_wav): os.remove(output_wav)
        if os.path.exists(output_mp3): os.remove(output_mp3)

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

# ===== MAIN =====
def main():
    if not BOT_TOKEN:
        print("Xatolik: BOT_TOKEN o'rnatilmagan!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # Ovozli xabar va audio fayllarni ushlash
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot polling rejimida ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
