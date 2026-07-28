from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards import main_menu, admin_menu
from database import db
from config import ADMIN_IDS

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    db.get_or_create_user(user.id, user.username or "", user.first_name)

    text = (
        "👋 Добро пожаловать в <b>BRUT Barbershop</b>!\n\n"
        "Премиальный барбершоп в Сызрани.\n"
        "Стрижки, бритьё, оформление бороды.\n\n"
        "Выбери, что нужно:"
    )
    await message.answer(text, reply_markup=main_menu())

@router.callback_query(F.data == "back_menu")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text(
        "Выбери, что нужно:",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Нет доступа", show_alert=True)
        return
    await call.message.edit_text(
        "🛠 <b>Админ-панель</b>\n\nВыбери раздел:",
        reply_markup=admin_menu()
    )

@router.callback_query(F.data == "about")
async def about_callback(call: CallbackQuery):
    text = (
        "ℹ️ <b>О BRUT Barbershop</b>\n\n"
        "BRUT — это место, где мужская стрижка "
        "превращается в ритуал. Горячее полотенце, "
        "опасная бритва, правильный разговор и хороший кофе.\n\n"
        "📍 Сызрань, ул. Ленина, 42\n"
        "⏰ Пн-Пт 9:00–21:00 | Сб 10:00–22:00 | Вс 10:00–20:00"
    )
    await call.message.edit_text(text, reply_markup=main_menu())

@router.callback_query(F.data == "contacts")
async def contacts_callback(call: CallbackQuery):
    text = (
        "📞 <b>Контакты</b>\n\n"
        "📍 ул. Ленина, 42, Сызрань\n"
        "📞 +7 (909) 123-45-67\n"
        "✂️ Запись через бота — 24/7\n\n"
        "Ждём вас в BRUT!"
    )
    await call.message.edit_text(text, reply_markup=main_menu())
