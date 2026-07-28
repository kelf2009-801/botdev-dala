from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = [
        [InlineKeyboardButton(text="✂️ Записаться", callback_data="booking_start")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_appointments")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def services_kb(services):
    kb = []
    for s in services:
        kb.append([InlineKeyboardButton(
            text=f"{s['name']} — {s['price']} ₽",
            callback_data=f"svc_{s['id']}"
        )])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def masters_kb(masters, selected_service=None):
    kb = []
    for m in masters:
        kb.append([InlineKeyboardButton(
            text=f"{m['name']} — {m['role']} (опыт {m['experience']} лет)",
            callback_data=f"mst_{m['id']}" + (f"_{selected_service}" if selected_service else "")
        )])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="booking_start")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def date_kb(dates, master_id, service_id):
    kb = []
    import locale
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    for d in dates:
        weekday = d.strftime("%a").capitalize()
        date_str = d.strftime("%d.%m")
        text = f"{date_str}, {weekday}"
        kb.append([InlineKeyboardButton(text=text, callback_data=f"dt_{d.strftime('%Y-%m-%d')}_{master_id}_{service_id}")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="booking_start")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def time_kb(slots, apt_date, master_id, service_id):
    kb = []
    row = []
    for i, s in enumerate(slots):
        row.append(InlineKeyboardButton(text=s, callback_data=f"tm_{s}_{apt_date}_{master_id}_{service_id}"))
        if len(row) == 3 or i == len(slots) - 1:
            kb.append(row)
            row = []
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"mst_{master_id}_{service_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_kb(service_id, master_id, apt_date, apt_time):
    kb = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"cfrm_{service_id}_{master_id}_{apt_date}_{apt_time}")],
        [InlineKeyboardButton(text="🔄 Заново", callback_data="booking_start")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"dt_{apt_date}_{master_id}_{service_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def my_appointments_kb(appointments):
    kb = []
    for a in appointments[:5]:
        kb.append([InlineKeyboardButton(
            text=f"❌ Отменить {a['appointment_date']} {a['appointment_time']} — {a['service_name']}",
            callback_data=f"cncl_{a['id']}"
        )])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_menu():
    kb = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📋 Все записи", callback_data="admin_appointments")],
        [InlineKeyboardButton(text="✂️ Услуги (ред.)", callback_data="admin_services")],
        [InlineKeyboardButton(text="👤 Мастера (ред.)", callback_data="admin_masters")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_mailing")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_services_kb(services):
    kb = []
    for s in services:
        status = "✅" if s["is_active"] else "❌"
        kb.append([InlineKeyboardButton(
            text=f"{status} {s['name']} — {s['price']}₽",
            callback_data=f"asvc_{s['id']}"
        )])
    kb.append([InlineKeyboardButton(text="➕ Добавить услугу", callback_data="asvc_add")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_masters_kb(masters):
    kb = []
    for m in masters:
        status = "✅" if m["is_active"] else "❌"
        kb.append([InlineKeyboardButton(
            text=f"{status} {m['name']} — {m['role']}",
            callback_data=f"amst_{m['id']}"
        )])
    kb.append([InlineKeyboardButton(text="➕ Добавить мастера", callback_data="amst_add")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_appointments_kb(appointments, page=0):
    kb = []
    start = page * 5
    for a in appointments[start:start+5]:
        status_icon = "✅" if a["status"] == "done" else ("❌" if a["status"] == "cancelled" else "🟡")
        kb.append([InlineKeyboardButton(
            text=f"{status_icon} {a['appointment_date']} {a['appointment_time']} — {a.get('service_name','')}",
            callback_data=f"aapt_{a['id']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"aapp_page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{max(1,(len(appointments)-1)//5+1)}", callback_data="none"))
    if start+5 < len(appointments):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"aapp_page_{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)