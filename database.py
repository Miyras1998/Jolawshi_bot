import aiosqlite
from datetime import datetime
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT,
                role TEXT DEFAULT 'passenger',  -- passenger | driver | both
                is_blocked INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS rides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER NOT NULL,
                from_city TEXT NOT NULL,
                to_city TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                seats INTEGER NOT NULL,
                price INTEGER NOT NULL,
                status TEXT DEFAULT 'active',  -- active | cancelled | completed
                channel_msg_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (driver_id) REFERENCES users(telegram_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ride_id INTEGER NOT NULL,
                passenger_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',  -- pending | accepted | rejected
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ride_id) REFERENCES rides(id),
                FOREIGN KEY (passenger_id) REFERENCES users(telegram_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Default sozlamalar
        defaults = [
            ("rides_open_hour", "6"),
            ("rides_open_minute", "0"),
            ("rides_close_hour", "22"),
            ("rides_close_minute", "0"),
            ("ride_expire_hours", "24"),
            ("channel_id", "@Jolawshi_bot_buyirtpa"),
            ("bot_active", "1"),
        ]
        for key, value in defaults:
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

        await db.execute("""
            CREATE TABLE IF NOT EXISTS passenger_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passenger_id INTEGER NOT NULL,
                from_city TEXT NOT NULL,
                to_city TEXT NOT NULL,
                dep_date TEXT NOT NULL,
                seats INTEGER NOT NULL,
                channel_msg_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (passenger_id) REFERENCES users(telegram_id)
            )
        """)

        await db.commit()


# ─── USERS ───────────────────────────────────────────────────────────────────

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
            return await cur.fetchone()


async def create_or_update_user(telegram_id: int, full_name: str, phone: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, full_name, phone)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET full_name = excluded.full_name
        """, (telegram_id, full_name, phone))
        await db.commit()


async def update_user_phone(telegram_id: int, phone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, telegram_id))
        await db.commit()


async def update_user_role(telegram_id: int, role: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET role = ? WHERE telegram_id = ?", (role, telegram_id))
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY created_at DESC") as cur:
            return await cur.fetchall()


async def block_user(telegram_id: int, blocked: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked = ? WHERE telegram_id = ?", (blocked, telegram_id))
        await db.commit()


# ─── RIDES ───────────────────────────────────────────────────────────────────

async def create_ride(driver_id, from_city, to_city, departure_time, seats, price):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO rides (driver_id, from_city, to_city, departure_time, seats, price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (driver_id, from_city, to_city, departure_time, seats, price))
        await db.commit()
        return cur.lastrowid


async def get_ride(ride_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM rides WHERE id = ?", (ride_id,)) as cur:
            return await cur.fetchone()


async def get_active_rides():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT r.*, u.full_name, u.phone FROM rides r
            JOIN users u ON r.driver_id = u.telegram_id
            WHERE r.status = 'active'
            ORDER BY r.created_at DESC
        """) as cur:
            return await cur.fetchall()


async def get_driver_rides(driver_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM rides WHERE driver_id = ? ORDER BY created_at DESC LIMIT 20
        """, (driver_id,)) as cur:
            return await cur.fetchall()


async def cancel_ride(ride_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE rides SET status = 'cancelled' WHERE id = ?", (ride_id,))
        await db.commit()


async def update_ride_channel_msg(ride_id: int, msg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE rides SET channel_msg_id = ? WHERE id = ?", (msg_id, ride_id))
        await db.commit()


async def get_all_rides_admin():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT r.*, u.full_name, u.phone FROM rides r
            JOIN users u ON r.driver_id = u.telegram_id
            ORDER BY r.created_at DESC LIMIT 50
        """) as cur:
            return await cur.fetchall()


# ─── BOOKINGS ────────────────────────────────────────────────────────────────

async def create_booking(ride_id: int, passenger_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        existing = await db.execute(
            "SELECT id FROM bookings WHERE ride_id=? AND passenger_id=? AND status != 'rejected'",
            (ride_id, passenger_id)
        )
        if await existing.fetchone():
            return None
        cur = await db.execute(
            "INSERT INTO bookings (ride_id, passenger_id) VALUES (?, ?)",
            (ride_id, passenger_id)
        )
        await db.commit()
        return cur.lastrowid


async def get_booking(booking_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)) as cur:
            return await cur.fetchone()


async def update_booking_status(booking_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        await db.commit()


async def get_ride_bookings(ride_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT b.*, u.full_name, u.phone FROM bookings b
            JOIN users u ON b.passenger_id = u.telegram_id
            WHERE b.ride_id = ?
        """, (ride_id,)) as cur:
            return await cur.fetchall()


async def get_passenger_bookings(passenger_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT b.*, r.from_city, r.to_city, r.departure_time, r.price
            FROM bookings b JOIN rides r ON b.ride_id = r.id
            WHERE b.passenger_id = ? ORDER BY b.created_at DESC LIMIT 20
        """, (passenger_id,)) as cur:
            return await cur.fetchall()


# ─── SETTINGS ────────────────────────────────────────────────────────────────

async def get_setting(key: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()


async def get_all_settings() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT key, value FROM settings") as cur:
            rows = await cur.fetchall()
            return {row[0]: row[1] for row in rows}


# ─── STATS ───────────────────────────────────────────────────────────────────

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        total_users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        total_drivers = (await (await db.execute("SELECT COUNT(*) FROM users WHERE role IN ('driver','both')")).fetchone())[0]
        total_rides = (await (await db.execute("SELECT COUNT(*) FROM rides")).fetchone())[0]
        active_rides = (await (await db.execute("SELECT COUNT(*) FROM rides WHERE status='active'")).fetchone())[0]
        total_bookings = (await (await db.execute("SELECT COUNT(*) FROM bookings")).fetchone())[0]
        return {
            "total_users": total_users,
            "total_drivers": total_drivers,
            "total_rides": total_rides,
            "active_rides": active_rides,
            "total_bookings": total_bookings,
        }

# ─── PASSENGER REQUESTS ──────────────────────────────────────────────────────

async def create_passenger_request(passenger_id, from_city, to_city, dep_date, seats):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO passenger_requests (passenger_id, from_city, to_city, dep_date, seats)
            VALUES (?, ?, ?, ?, ?)
        """, (passenger_id, from_city, to_city, dep_date, seats))
        await db.commit()
        return cur.lastrowid


async def get_passenger_request(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT pr.*, u.phone, u.full_name FROM passenger_requests pr "
            "JOIN users u ON pr.passenger_id = u.telegram_id WHERE pr.id = ?",
            (request_id,)
        ) as cur:
            return await cur.fetchone()


async def update_passenger_request_msg(request_id: int, msg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE passenger_requests SET channel_msg_id = ? WHERE id = ?",
            (msg_id, request_id)
        )
        await db.commit()
