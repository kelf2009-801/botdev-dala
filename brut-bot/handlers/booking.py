from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import (
    services_kb, masters_kb, date_kb, time_kb,
    confirm_kb, my_appointments_kb, main_menu
)
from database import db
from datetime import datetime, timedelta

router = Router()

class Booking(StatesGroup):
    service = State()
    master = State()
    date = State()
    time = State()
    phone = State()

def get_next_days(count=7):
    today = datetime.now()
    dates = []
    for i in range(count):
        d = today + timedelta(days=i)
        if d.hour >= 20:
            continue
        dates.append(d)
    return dates[:count]

@router.callback_query(F.data == "booking_start")
async def booking_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    services = db.get_services()
    text = "✂️ <b>Выбери услугу:</b>"
    await call.message.edit_text(text, reply_markup=services_kb(services))

@router.callback_query(F.data.startswith("svc_"))
async def booking_service(call: CallbackQuery, state: FSMContext):
    service_id = int(call.data.split("_")[1])
    service = db.get_service(service_id)
    if not service:
        await call.answer("Услуга недоступна", show_alert=True)
        return
    await state.update_data(service_id=service_id, service_name=service["name"], service_price=service["price"])
    masters = db.get_masters()
    text = f"<b>{service['name']}</b> — {service['price']} ₽\n\nТеперь выбери мастера:"
    await call.message.edit_text(text, reply_markup=masters_kb(masters, service_id))

@router.callback_query(F.data.startswith("mst_"))
async def booking_master(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    master_id = int(parts[1])
    master = db.get_master(master_id)
    if not master:
        await call.answer("Мастер недоступен", show_alert=True)
        return
    await state.update_data(master_id=master_id, master_name=master["name"])

    data = await state.get_data()
    service_id = data.get("service_id")

    dates = get_next_days(7)
    text = f"<b>{master['name']}</b>\n\nВыбери дату:"
    await call.message.edit_text(text, reply_markup=date_kb(dates, master_id, service_id))

@router.callback_query(F.data.startswith("dt_"))
async def booking_date(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    apt_date = parts[1]
    master_id = int(parts[2])
    service_id = int(parts[3])
    await state.update_data(apt_date=apt_date, master_id=master_id, service_id=service_id)

    slots = db.get_available_slots(master_id, apt_date)
    if not slots:
        await call.answer("Нет свободных слотов на эту дату", show_alert=True)
        return

    date_display = datetime.strptime(apt_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    text = f"📅 <b>{date_display}</b>\n\nВыбери время:"
    await call.message.edit_text(text, reply_markup=time_kb(slots, apt_date, master_id, service_id))

@router.callback_query(F.data.startswith("tm_"))
async def booking_time(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    apt_time = parts[1]
    apt_date = parts[2]
    master_id = int(parts[3])
    service_id = int(parts[4])

    await state.update_data(apt_time=apt_time, apt_date=apt_date, master_id=master_id, service_id=service_id)

    service = db.get_service(service_id)
    master = db.get_master(master_id)
    date_display = datetime.strptime(apt_date, "%Y-%m-%d").strftime("%d.%m.%Y")

    text = (
        f"📋 <b>Подтверждение записи</b>\n\n"
        f"✂️ Услуга: {service['name']}\n"
        f"💰 Цена: {service['price']} ₽\n"
        f"👤 Мастер: {master['name']}\n"
        f"📅 Дата: {date_display}\n"
        f"⏰ Время: {apt_time}\n\n"
        f"Всё верно?"
    )
    await call.message.edit_text(text, reply_markup=confirm_kb(service_id, master_id, apt_date, apt_time))

@router.callback_query(F.data.startswith("cfrm_"))
async def booking_confirm(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    service_id = int(parts[1])
    master_id = int(parts[2])
    apt_date = parts[3]
    apt_time = parts[4]

    user = call.from_user
    db.get_or_create_user(user.id, user.username or "", user.first_name)

    data = await state.get_data()
    service_name = data.get("service_name", "—")
    master_name = data.get("master_name", "—")

    apt_id = db.create_appointment(
        user.id, user.username or "", "",
        service_id, master_id, apt_date, apt_time
    )

    date_display = datetime.strptime(apt_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    text = (
        f"✅ <b>Запись подтверждена!</b>\n\n"
        f"✂️ {service_name}\n"
        f"👤 Мастер: {master_name}\n"
        f"📅 {date_display} в {apt_time}\n\n"
        f"Ждём вас в BRUT! 🔥\n"
        f"📍 ул. Ленина, 42"
    )
    await state.clear()
    await call.message.edit_text(text, reply_markup=main_menu())

@router.callback_query(F.data == "my_appointments")
async def my_appts(call: CallbackQuery):
    appointments = db.get_user_appointments(call.from_user.id)
    if not appointments:
        await call.message.edit_text(
            "У тебя пока нет активных записей.\n\n"
            "Хочешь записаться? 👇",
            reply_markup=main_menu()
        )
        return

    text = "📋 <b>Твои записи:</b>\n\n"
    for a in appointments:
        text += f"✂️ {a['service_name']} — {a['master_name']}\n"
        text += f"📅 {a['appointment_date']} в {a['appointment_time']}\n\n"

    await call.message.edit_text(text, reply_markup=my_appointments_kb(appointments))

@router.callback_query(F.data.startswith("cncl_"))
async def cancel_appointment(call: CallbackQuery):
    apt_id = int(call.data.split("_")[1])
    db.cancel_appointment(apt_id, call.from_user.id)
    await call.answer("Запись отменена ✅", show_alert=True)
    appointments = db.get_user_appointments(call.from_user.id)
    if not appointments:
        await call.message.edit_text("Запись отменена. Хочешь записаться снова?", reply_markup=main_menu())
    else:
        text = "📋 <b>Твои записи:</b>\n\n"
        for a in appointments:
            text += f"✂️ {a['service_name']} — {a['master_name']}\n"
            text += f"📅 {a['appointment_date']} в {a['appointment_time']}\n\n"
        await call.message.edit_text(text, reply_markup=my_appointments_kb(appointments))
