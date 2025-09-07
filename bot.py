import re
import asyncio
import requests
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from ayarlar import api_id, api_hash, group_ids, bot_token, chat_ids_file

client = TelegramClient('oran_session', api_id, api_hash)

def extract_oran(mesaj):
    oranlar = re.findall(r'(\d+(?:[.,]\d+)?)\s*Oran', mesaj, re.IGNORECASE)
    return max(map(float, oranlar)) if oranlar else 0

def temizle_mesaj(mesaj):
    return mesaj.strip()

def herkese_mesaj_gonder(mesaj, foto=None):
    try:
        with open(chat_ids_file, 'r') as f:
            ids = f.read().splitlines()
        for chat_id in ids:
            if foto:
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendPhoto",
                    data={"chat_id": chat_id, "caption": f"📣 Yeni Oran Paylaşıldı:\n\n{mesaj}"},
                    files={"photo": foto}
                )
            else:
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    data={"chat_id": chat_id, "text": f"📣 Yeni Oran Paylaşıldı:\n\n{mesaj}"}
                )
    except Exception as e:
        print("Mesaj gönderim hatası:", e)

@client.on(events.NewMessage(chats=group_ids))
async def handler(event):
    mesaj = event.raw_text
    oran = extract_oran(mesaj)
    if oran >= 50:
        print(f"[+] {oran} oran bulundu, mesaj gönderiliyor... (kanal: {event.chat_id})")
        temiz = temizle_mesaj(mesaj)

        foto = None
        if event.photo:
            foto = await event.download_media(file=bytes)

        herkese_mesaj_gonder(temiz, foto)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    try:
        with open(chat_ids_file, 'r') as f:
            ids = f.read().splitlines()
    except FileNotFoundError:
        ids = []
    if user_id not in ids:
        with open(chat_ids_file, 'a') as f:
            f.write(f"{user_id}\n")
    await update.message.reply_text("🎉 Merhaba! Bildirim sistemine katıldın. 50+ oran olduğunda sana haber vereceğim. 🍀")

async def main():
    print("🤖 Bot başlatılıyor...")

    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))

    await client.start()
    print("✅ Telegram bot aktif.")

    telethon_task = asyncio.create_task(client.run_until_disconnected())

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    await telethon_task

if __name__ == "__main__":
    asyncio.run(main())
