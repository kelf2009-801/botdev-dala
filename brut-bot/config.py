import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
DATABASE_PATH = os.getenv("DATABASE_PATH", "brut.db")
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))

SERVICES_DEFAULT = [
    {"name": "Мужская стрижка", "price": 1200, "duration": 45, "desc": "Мытьё головы, стрижка машинкой и ножницами, укладка."},
    {"name": "Стрижка + борода", "price": 1800, "duration": 60, "desc": "Комплекс: стрижка + оформление бороды + горячее полотенце."},
    {"name": "Оформление бороды", "price": 900, "duration": 30, "desc": "Моделирование бороды, подбривание, масло."},
    {"name": "Королевское бритьё", "price": 1500, "duration": 40, "desc": "Бритьё опасной бритвой. Горячий компресс, лосьон."},
    {"name": "Стрижка машинкой", "price": 800, "duration": 20, "desc": "Быстрая стрижка под насадку."},
    {"name": "Детская стрижка", "price": 1000, "duration": 30, "desc": "Для мальчиков до 14 лет."},
]

MASTERS_DEFAULT = [
    {"name": "Артём", "role": "Топ-мастер", "desc": "Специалист по сложным переходам, фейдам.", "exp": 8},
    {"name": "Максим", "role": "Мастер бритвы", "desc": "Королевское бритьё, оформление бороды.", "exp": 7},
    {"name": "Сергей", "role": "Креативный стилист", "desc": "Классика, креатив, детские стрижки.", "exp": 6},
]

WORK_HOURS = list(range(9, 21))  # 9:00 - 20:00
