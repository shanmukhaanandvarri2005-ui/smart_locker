import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_locker.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_reset=False):
    if force_reset and os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = get_db()
    cursor = conn.cursor()

    # Members Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rfid_uid TEXT UNIQUE NOT NULL,
        reg_no TEXT UNIQUE NOT NULL,
        department TEXT DEFAULT 'Electrical and Electronics Engineering',
        email TEXT,
        role TEXT NOT NULL DEFAULT 'employee', -- 'employee' or 'host'
        status TEXT NOT NULL DEFAULT 'active', -- 'active' or 'inactive'
        avatar_url TEXT,
        created_at TEXT NOT NULL
    )
    ''')

    # Lockers / Books Compartments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lockers (
        locker_id INTEGER PRIMARY KEY AUTOINCREMENT,
        locker_code TEXT UNIQUE NOT NULL,
        book_label TEXT NOT NULL,
        book_author TEXT NOT NULL,
        book_isbn TEXT,
        category TEXT DEFAULT 'Engineering',
        occupancy_status TEXT NOT NULL DEFAULT 'present', -- 'present', 'absent'
        door_status TEXT NOT NULL DEFAULT 'closed',       -- 'closed', 'open'
        lock_status TEXT NOT NULL DEFAULT 'locked',       -- 'locked', 'unlocked'
        last_updated TEXT NOT NULL
    )
    ''')

    # Loans Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL REFERENCES members(member_id),
        locker_id INTEGER NOT NULL REFERENCES lockers(locker_id),
        borrowed_at TEXT NOT NULL,
        due_date TEXT NOT NULL,
        returned_at TEXT,
        status TEXT NOT NULL DEFAULT 'active' -- 'active', 'returned'
    )
    ''')

    # Transactions Table (Circulation Audit Log)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER REFERENCES members(member_id),
        locker_id INTEGER REFERENCES lockers(locker_id),
        operation TEXT NOT NULL, -- 'borrow', 'return', 'auth'
        result TEXT NOT NULL,    -- 'success', 'rejected', 'error'
        timestamp TEXT NOT NULL,
        details TEXT
    )
    ''')

    cursor.execute('SELECT COUNT(*) FROM members')
    if cursor.fetchone()[0] == 0:
        seed_clean_data(conn)

    conn.commit()
    conn.close()

def seed_clean_data(conn):
    cursor = conn.cursor()
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    # Production Registered Members (Students & Faculty)
    members = [
        (
            'Varri Shanmukha Anand',
            '12:5E:7B:44',
            '21BEE1001',
            'Electrical and Electronics Engineering',
            None,
            'employee',
            'active',
            'https://api.dicebear.com/7.x/initials/svg?seed=Shanmukha+Anand&backgroundColor=123b67',
            now_str
        ),
        (
            'Ananya Sharma',
            '04:A2:8F:C9',
            '21BEE1048',
            'Electrical and Electronics Engineering',
            None,
            'employee',
            'active',
            'https://api.dicebear.com/7.x/initials/svg?seed=Ananya+Sharma&backgroundColor=2563eb',
            now_str
        ),
        (
            'K. Ramesh',
            'E2:80:68:10',
            'VIT-FAC-019',
            'Electrical and Electronics Engineering',
            None,
            'host',
            'active',
            'https://api.dicebear.com/7.x/initials/svg?seed=K+Ramesh&backgroundColor=002549',
            now_str
        )
    ]
    cursor.executemany('''
    INSERT INTO members (name, rfid_uid, reg_no, department, email, role, status, avatar_url, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', members)

    # Single Physical Locker Prototype Unit (All sensors armed and locked)
    lockers = [
        ('Locker 01', 'Modern Control Engineering (5th Edition)', 'Katsuhiko Ogata', '978-0136156734', 'Control Systems', 'present', 'closed', 'locked', now_str)
    ]
    cursor.executemany('''
    INSERT INTO lockers (locker_code, book_label, book_author, book_isbn, category, occupancy_status, door_status, lock_status, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', lockers)

    conn.commit()

if __name__ == '__main__':
    init_db(force_reset=True)
    print('SmartLocker database cleanly initialized at', DB_PATH)
