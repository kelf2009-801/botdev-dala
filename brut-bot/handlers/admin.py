from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import (
    admin_menu, admin_services_kb, admin_masters_kb,
    admin_appointments_kb, main_menu
)
from database import db
from config import ADMIN_IDS

router = Router()

class Mailing(StatesGroup):
    text = State()

class EditService(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_duration = State()
    waiting_desc = State()

class EditMaster(StatesGroup):
    waiting_name = State()
    waiting_role = State()
    waiting_desc = State()
    waiting_exp = State()

def is_admin(func):
    async def wrapper(call: CallbackQuery, *args, **kwargs):
        if call.from_user.id not in ADMIN_IDS:
            await call.answer("Нет доступа ✋", show_alert=True)
            return
        return await func(call, *args, **kwargs)
    return wrapper

@router.callback_query(F.data == "admin_panel")
@is_admin
async def admin_panel(call: CallbackQuery):
    await call.message.edit_text(
        "🛠 <b>Админ-панель</b>\n\nВыбери раздел:",
        reply_markup=admin_menu()
    )

@router.callback_query(F.data == "admin_stats")
@is_admin
async def admin_stats(call: CallbackQuery):
    stats = db.get_stats()
    text = (
        "📊 <b>Статистика BRUT</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['users']}</b>\n"
        f"📋 Всего записей: <b>{stats['total']}</b>\n"
        f"🟡 Активных: <b>{stats['active']}</b>\n"
        f"✅ Завершённых: <b>{stats['done']}</b>\n"
        f"❌ Отменённых: <b>{stats['cancelled']}</b>"
    )
    await call.message.edit_text(text, reply_markup=admin_menu())

@router.callback_query(F.data == "admin_appointments")
@is_admin
async def admin_appointments(call: CallbackQuery):
    appointments = db.get_all_appointments(status="active")
    if not appointments:
        await call.message.edit_text("Нет активных записей", reply_markup=admin_menu())
        return
    await call.message.edit_text(
        f"📋 <b>Все записи ({len(appointments)})</b>",
        reply_markup=admin_appointments_kb(appointments)
    )

@router.callback_query(F.data.startswith("aapp_page_"))
@is_admin
async def admin_appointments_page(call: CallbackQuery):
    page = int(call.data.split("_")[2])
    appointments = db.get_all_appointments(status="active")
    await call.message.edit_text(
        f"📋 <b>Все записи ({len(appointments)})</b>",
        reply_markup=admin_appointments_kb(appointments, page)
    )

@router.callback_query(F.data.startswith("aapt_"))
@is_admin
async def admin_appointment_detail(call: CallbackQuery):
    apt_id = int(call.data.split("_")[1])
    appointment = db.conn.execute("""
        SELECT a.*, s.name as service_name, s.price as service_price,
               m.name as master_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN masters m ON a.master_id = m.id
        WHERE a.id=?
    """, (apt_id,)).fetchone()
    if not appointment:
        await call.answer("Запись не найдена", show_alert=True)
        return

    text = (
        f"📋 <b>Запись #{appointment['id']}</b>\n\n"
        f"👤 Клиент: {appointment.get('username','—')}\n"
        f"🆔 ID: {appointment['user_id']}\n"
        f"✂️ Услуга: {appointment['service_name']}\n"
        f"💰 Цена: {appointment['service_price']} ₽\n"
        f"👤 Мастер: {appointment['master_name']}\n"
        f"📅 Дата: {appointment['appointment_date']}\n"
        f"⏰ Время: {appointment['appointment_time']}\n"
        f"📌 Статус: {appointment['status']}\n"
        f"🕐 Создана: {appointment['created_at']}"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"aapt_done_{apt_id}"),
         InlineKeyboardButton(text="❌ Отменить", callback_data=f"aapt_cancel_{apt_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_appointments")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("aapt_done_"))
@is_admin
async def admin_appointment_done(call: CallbackQuery):
    apt_id = int(call.data.split("_")[3])
    db.done_appointment(apt_id)
    await call.answer("✅ Отмечено как выполненное")
    await admin_appointments(call)

@router.callback_query(F.data.startswith("aapt_cancel_"))
@is_admin
async def admin_appointment_cancel(call: CallbackQuery):
    apt_id = int(call.data.split("_")[3])
    db.cancel_appointment(apt_id)
    await call.answer("❌ Запись отменена")
    await admin_appointments(call)

# ===== SERVICES EDIT =====
@router.callback_query(F.data == "admin_services")
@is_admin
async def admin_services(call: CallbackQuery):
    services = db.conn.execute("SELECT * FROM services ORDER BY is_active DESC, id").fetchall()
    await call.message.edit_text(
        "✂️ <b>Управление услугами</b>\n\n"
        "Нажми на услугу чтобы изменить.\n"
        "✅ — активно, ❌ — скрыто",
        reply_markup=admin_services_kb(services)
    )

@router.callback_query(F.data.startswith("asvc_"))
@is_admin
async def admin_service_detail(call: CallbackQuery):
    parts = call.data.split("_")
    if parts[1] == "add":
        await call.message.edit_text(
            "➕ <b>Новая услуга</b>\n\n"
            "Введи название услуги:"
        )
        return

    sid = int(parts[1])
    svc = db.get_service(sid)
    if not svc:
        await call.answer("Не найдено", show_alert=True)
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"asvc_edit_{sid}")],
        [InlineKeyboardButton(text="🔄 Скрыть/показать", callback_data=f"asvc_toggle_{sid}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
    ])
    text = (
        f"✂️ <b>{svc['name']}</b>\n"
        f"💰 {svc['price']} ₽\n"
        f"⏱ {svc['duration']} мин\n"
        f"📝 {svc['description'] or '—'}\n"
        f"📌 {'✅ Активна' if svc['is_active'] else '❌ Скрыта'}"
    )
    await call.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("asvc_toggle_"))
@is_admin
async def admin_service_toggle(call: CallbackQuery):
    sid = int(call.data.split("_")[2])
    db.toggle_service(sid)
    await admin_services(call)

# ===== MASTERS EDIT =====
@router.callback_query(F.data == "admin_masters")
@is_admin
async def admin_masters(call: CallbackQuery):
    masters = db.conn.execute("SELECT * FROM masters ORDER BY is_active DESC, id").fetchall()
    await call.message.edit_text(
        "👤 <b>Управление мастерами</b>",
        reply_markup=admin_masters_kb(masters)
    )

@router.callback_query(F.data.startswith("amst_"))
@is_admin
async def admin_master_detail(call: CallbackQuery):
    parts = call.data.split("_")
    if parts[1] == "add":
        await call.message.edit_text(
            "➕ <b>Новый мастер</b>\n\n"
            "Введи имя мастера:"
        )
        return

    mid = int(parts[1])
    m = db.get_master(mid)
    if not m:
        await call.answer("Не найдено", show_alert=True)
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"amst_edit_{mid}")],
        [InlineKeyboardButton(text="🔄 Скрыть/показать", callback_data=f"amst_toggle_{mid}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
    ])
    text = (
        f"👤 <b>{m['name']}</b>\n"
        f"🎭 {m['role'] or '—'}\n"
        f"📝 {m['description'] or '—'}\n"
        f"⭐ Опыт: {m['experience']} лет\n"
        f"📌 {'✅ Активен' if m['is_active'] else '❌ Скрыт'}"
    )
    await call.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("amst_toggle_"))
@is_admin
async def admin_master_toggle(call: CallbackQuery):
    mid = int(call.data.split("_")[2])
    db.toggle_master(mid)
    await admin_masters(call)

# ===== MAILING =====
@router.callback_query(F.data == "admin_mailing")
@is_admin
async def admin_mailing_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(Mailing.text)
    await call.message.edit_text(
        "📢 <b>Рассылка</b>\n\n"
        "Напиши текст для рассылки всем пользователям бота:"
    )

@router.message(Mailing.text)
async def admin_mailing_send(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Нет доступа")
        await state.clear()
        return

    text = message.text
    users = db.get_mailing_users()

    sent = 0
    failed = 0
    for user in users:
        try:
            from bot import bot
            await bot.send_message(
                user["tg_id"],
                f"📢 <b>BRUT Barbershop</b>\n\n{text}",
                parse_mode="HTML"
            )
            sent += 1
        except Exception:
            failed += 1

    await state.clear()
    await message.answer(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}"
    )