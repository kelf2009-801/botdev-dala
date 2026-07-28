import sqlite3
import json
from datetime import datetime, date, timedelta
from config import DATABASE_PATH, SERVICES_DEFAULT, MASTERS_DEFAULT

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        self._seed_data()

    def _init_tables(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                duration INTEGER NOT NULL,
                description TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS masters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT DEFAULT '',
                description TEXT DEFAULT '',
                experience INTEGER DEFAULT 0,
                photo TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                service_id INTEGER NOT NULL,
                master_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now', '+3 hours')),
                reminded INTEGER DEFAULT 0,
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (master_id) REFERENCES masters(id)
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', '+3 hours'))
            );
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                master_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                start_hour INTEGER DEFAULT 9,
                end_hour INTEGER DEFAULT 21,
                is_working INTEGER DEFAULT 1,
                FOREIGN KEY (master_id) REFERENCES masters(id)
            );
        """)
        self.conn.commit()

    def _seed_data(self):
        c = self.conn.cursor()
        if not c.execute("SELECT COUNT(*) FROM services").fetchone()[0]:
            for s in SERVICES_DEFAULT:
                c.execute("INSERT INTO services (name, price, duration, description) VALUES (?,?,?,?)",
                          (s["name"], s["price"], s["duration"], s["desc"]))
        if not c.execute("SELECT COUNT(*) FROM masters").fetchone()[0]:
            for m in MASTERS_DEFAULT:
                c.execute("INSERT INTO masters (name, role, description, experience) VALUES (?,?,?,?)",
                          (m["name"], m["role"], m["desc"], m["exp"]))
        if not c.execute("SELECT COUNT(*) FROM schedule").fetchone()[0]:
            for mid in range(1, 4):
                for dow in range(7):
                    if dow == 6:  # sunday
                        c.execute("INSERT INTO schedule (master_id, day_of_week, start_hour, end_hour) VALUES (?,?,10,20)", (mid, dow))
                    elif dow == 5:  # saturday
                        c.execute("INSERT INTO schedule (master_id, day_of_week, start_hour, end_hour) VALUES (?,?,10,22)", (mid, dow))
                    else:
                        c.execute("INSERT INTO schedule (master_id, day_of_week, start_hour, end_hour) VALUES (?,?,9,21)", (mid, dow))
        self.conn.commit()

    # ---- SERVICES ----
    def get_services(self):
        return self.conn.execute("SELECT * FROM services WHERE is_active=1").fetchall()

    def get_service(self, sid):
        return self.conn.execute("SELECT * FROM services WHERE id=?", (sid,)).fetchone()

    def update_service(self, sid, name, price, duration, description):
        self.conn.execute("UPDATE services SET name=?, price=?, duration=?, description=? WHERE id=?",
                          (name, price, duration, description, sid))
        self.conn.commit()

    def toggle_service(self, sid):
        c = self.conn.execute("SELECT is_active FROM services WHERE id=?", (sid,)).fetchone()
        if c:
            self.conn.execute("UPDATE services SET is_active=? WHERE id=?", (0 if c["is_active"] else 1, sid))
            self.conn.commit()

    def add_service(self, name, price, duration, description):
        c = self.conn.execute("INSERT INTO services (name, price, duration, description) VALUES (?,?,?,?)",
                              (name, price, duration, description))
        self.conn.commit()
        return c.lastrowid

    # ---- MASTERS ----
    def get_masters(self):
        return self.conn.execute("SELECT * FROM masters WHERE is_active=1").fetchall()

    def get_master(self, mid):
        return self.conn.execute("SELECT * FROM masters WHERE id=?", (mid,)).fetchone()

    def update_master(self, mid, name, role, description, experience):
        self.conn.execute("UPDATE masters SET name=?, role=?, description=?, experience=? WHERE id=?",
                          (name, role, description, experience, mid))
        self.conn.commit()

    def toggle_master(self, mid):
        c = self.conn.execute("SELECT is_active FROM masters WHERE id=?", (mid,)).fetchone()
        if c:
            self.conn.execute("UPDATE masters SET is_active=? WHERE id=?", (0 if c["is_active"] else 1, mid))
            self.conn.commit()

    def add_master(self, name, role, description, experience):
        c = self.conn.execute("INSERT INTO masters (name, role, description, experience) VALUES (?,?,?,?)",
                              (name, role, description, experience))
        self.conn.commit()
        return c.lastrowid

    # ---- APPOINTMENTS ----
    def create_appointment(self, user_id, username, phone, service_id, master_id, apt_date, apt_time):
        c = self.conn.execute(
            "INSERT INTO appointments (user_id, username, phone, service_id, master_id, appointment_date, appointment_time) VALUES (?,?,?,?,?,?,?)",
            (user_id, username, phone, service_id, master_id, apt_date, apt_time))
        self.conn.commit()
        return c.lastrowid

    def get_user_appointments(self, user_id, status="active"):
        rows = self.conn.execute("""
            SELECT a.*, s.name as service_name, s.price, m.name as master_name
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN masters m ON a.master_id = m.id
            WHERE a.user_id=? AND a.status=?
            ORDER BY a.appointment_date, a.appointment_time
        """, (user_id, status)).fetchall()
        return rows

    def get_all_appointments(self, status=None):
        query = """
            SELECT a.*, s.name as service_name, s.price, m.name as master_name
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN masters m ON a.master_id = m.id
        """
        if status:
            query += " WHERE a.status=?"
            return self.conn.execute(query + " ORDER BY a.appointment_date, a.appointment_time", (status,)).fetchall()
        return self.conn.execute(query + " ORDER BY a.appointment_date, a.appointment_time").fetchall()

    def cancel_appointment(self, apt_id, user_id=None):
        if user_id:
            self.conn.execute("UPDATE appointments SET status='cancelled' WHERE id=? AND user_id=?", (apt_id, user_id))
        else:
            self.conn.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (apt_id,))
        self.conn.commit()

    def done_appointment(self, apt_id):
        self.conn.execute("UPDATE appointments SET status='done' WHERE id=?", (apt_id,))
        self.conn.commit()

    # ---- AVAILABLE SLOTS ----
    def get_available_slots(self, master_id, target_date):
        dow = datetime.strptime(target_date, "%Y-%m-%d").weekday()
        sched = self.conn.execute(
            "SELECT start_hour, end_hour FROM schedule WHERE master_id=? AND day_of_week=? AND is_working=1",
            (master_id, dow)).fetchone()
        if not sched:
            return []

        busy = self.conn.execute(
            "SELECT appointment_time FROM appointments WHERE master_id=? AND appointment_date=? AND status='active'",
            (master_id, target_date)).fetchall()
        busy_times = {b["appointment_time"] for b in busy}

        slots = []
        for h in range(sched["start_hour"], sched["end_hour"]):
            t = f"{h:02d}:00"
            if t not in busy_times:
                slots.append(t)
        return slots

    # ---- USERS ----
    def get_or_create_user(self, tg_id, username="", first_name=""):
        u = self.conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if u:
            if username and username != u["username"]:
                self.conn.execute("UPDATE users SET username=? WHERE tg_id=?", (username, tg_id))
                self.conn.commit()
            return u
        c = self.conn.execute("INSERT INTO users (tg_id, username, first_name) VALUES (?,?,?)",
                              (tg_id, username, first_name))
        self.conn.commit()
        return self.conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()

    def get_all_users(self):
        return self.conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()

    def update_user_phone(self, tg_id, phone):
        self.conn.execute("UPDATE users SET phone=? WHERE tg_id=?", (phone, tg_id))
        self.conn.commit()

    # ---- STATS ----
    def get_stats(self):
        total = self.conn.execute("SELECT COUNT(*) as c FROM appointments").fetchone()["c"]
        active = self.conn.execute("SELECT COUNT(*) as c FROM appointments WHERE status='active'").fetchone()["c"]
        done = self.conn.execute("SELECT COUNT(*) as c FROM appointments WHERE status='done'").fetchone()["c"]
        cancelled = self.conn.execute("SELECT COUNT(*) as c FROM appointments WHERE status='cancelled'").fetchone()["c"]
        users = self.conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        return {"total": total, "active": active, "done": done, "cancelled": cancelled, "users": users}

    # ---- MAILING ----
    def get_mailing_users(self):
        return self.conn.execute("SELECT tg_id FROM users").fetchall()

db = Database()
