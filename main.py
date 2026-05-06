import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from TTS.api import TTS
from pydub import AudioSegment

# ===== CONFIG =====
BOT_TOKEN = "YOUR_BOT_TOKEN"

# ===== TTS LOAD (1 marta yuklanadi) =====
print("Model yuklanmoqda...")
tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts")
print("Tayyor!")

# ===== USER PAPKA =====
def get_user_dir(user_id):
    path = f"users/{user_id}"
    os.makedirs(path, exist_ok=True)
    return path

# ===== VOICE HANDLER =====
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_dir = get_user_dir(user_id)

    voice = await update.message.voice.get_file()
    ogg_path = os.path.join(user_dir, "voice.ogg")
    wav_path = os.path.join(user_dir, "voice.wav")

    await voice.download_to_drive(ogg_path)

    # OGG → WAV
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(wav_path, format="wav")

    await update.message.reply_text("✅ Ovozingiz saqlandi!\nEndi matn yuboring ✍️")

# ===== TEXT HANDLER =====
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_dir = get_user_dir(user_id)

    wav_path = os.path.join(user_dir, "voice.wav")
    output_path = os.path.join(user_dir, "output.wav")

    if not os.path.exists(wav_path):
        await update.message.reply_text("❗ Avval ovoz yuboring 🎤")
        return

    text = update.message.text

    await update.message.reply_text("⏳ Ovoz yaratilmoqda...")

    try:
        # TTS
        tts.tts_to_file(
            text=text,
            speaker_wav=wav_path,
            language="uz",
            file_path=output_path
        )

        # Yuborish
        await update.message.reply_audio(audio=open(output_path, "rb"))

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot ishlayapti...")
    app.run_polling()

if __name__ == "__main__":
    main()
