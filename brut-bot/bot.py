import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from handlers import start, booking, admin
from database import db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(booking.router)
dp.include_router(admin.router)
# ===== SCHEDULER (reminders) =====
import asyncio
from datetime import datetime, timedelta

REMINDER_HOURS = 2  # remind 2 hours before

async def check_reminders(bot):
    now = datetime.now()
    remind_from = (now + timedelta(hours=REMINDER_HOURS - 0.1)).strftime("%H:%M")
    remind_to = (now + timedelta(hours=REMINDER_HOURS + 0.1)).strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    appointments = db.conn.execute("""
        SELECT a.*, s.name as service_name, m.name as master_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN masters m ON a.master_id = m.id
        WHERE a.appointment_date=? AND a.status='active'
        AND a.appointment_time BETWEEN ? AND ?
        AND a.reminded IS NULL
    """, (today, remind_from, remind_to)).fetchall()

    for a in appointments:
        try:
            await bot.send_message(
                a["user_id"],
                f"⏰ <b>Напоминание!</b>\n\n"
                f"Через 2 часа у тебя:\n"
                f"✂️ {a['service_name']}\n"
                f"👤 Мастер: {a['master_name']}\n"
                f"📅 {a['appointment_date']} в {a['appointment_time']}\n\n"
                f"📍 ул. Ленина, 42, Сызрань\n\n"
                f"Ждём! 🔥"
            )
            db.conn.execute("UPDATE appointments SET reminded=1 WHERE id=?", (a["id"],))
            db.conn.commit()
        except Exception as e:
            print(f"Reminder failed for user {a['user_id']}: {e}")

async def reminder_loop(bot):
    while True:
        try:
            await check_reminders(bot)
        except Exception as e:
            print(f"Reminder check error: {e}")
        await asyncio.sleep(60)  # check every minute

async def main():
    db.get_services()
    print("DB initialized")
    print("BRUT Bot started!")
    asyncio.create_task(reminder_loop(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")