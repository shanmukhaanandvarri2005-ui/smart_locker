import sqlite3
import os
from datetime import datetime, timedelta

# Automatically load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try importing PostgreSQL / Supabase driver
try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_locker.db')


class RowWrapper(dict):
    """A dictionary that also supports integer indexing like sqlite3.Row."""
    def __init__(self, raw_dict, raw_values):
        super().__init__(raw_dict)
        self._values = list(raw_values)

    def __getitem__(self, k):
        if isinstance(k, int):
            return self._values[k]
        return super().__getitem__(k)


def _format_row(row):
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (datetime, timedelta)):
            d[k] = v.strftime('%Y-%m-%d %H:%M:%S')
    raw_vals = [d[k] for k in d.keys()]
    return RowWrapper(d, raw_vals)


class PostgresCursorWrapper:
    """Wraps a psycopg2 DictCursor to provide seamless cross-compatibility with SQLite queries."""
    def __init__(self, cursor):
        self._cursor = cursor

    def _convert_query(self, query):
        # Translate SQLite '?' positional placeholders to PostgreSQL '%s'
        return query.replace('?', '%s')

    def execute(self, query, params=None):
        sql = self._convert_query(query)
        if params is not None:
            return self._cursor.execute(sql, params)
        return self._cursor.execute(sql)

    def executemany(self, query, seq_of_params):
        sql = self._convert_query(query)
        return self._cursor.executemany(sql, seq_of_params)

    def fetchone(self):
        return _format_row(self._cursor.fetchone())

    def fetchall(self):
        return [_format_row(r) for r in self._cursor.fetchall()]

    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size) if size is not None else self._cursor.fetchmany()
        return [_format_row(r) for r in rows]

    def __iter__(self):
        for r in self._cursor:
            yield _format_row(r)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PostgresConnectionWrapper:
    """Wraps a psycopg2 connection to mimic SQLite connection behavior."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor(cursor_factory=DictCursor))

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def is_postgres_configured():
    """Checks whether a PostgreSQL / Supabase connection URL is provided."""
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DB_URL')
    return bool(db_url and psycopg2)


def get_db():
    """Returns an active database connection (Supabase PostgreSQL if configured, otherwise local SQLite)."""
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DB_URL')
    if db_url and psycopg2:
        # Handle Supabase pooler / standard URL (convert postgres:// to postgresql:// if needed)
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        raw_conn = psycopg2.connect(db_url)
        return PostgresConnectionWrapper(raw_conn)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def init_db(force_reset=False):
    """Initializes tables and seeds base records."""
    if is_postgres_configured():
        # PostgreSQL / Supabase initialization via supabase_schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'supabase_schema.sql')
        if os.path.exists(schema_path):
            conn = get_db()
            cursor = conn.cursor()
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            cursor.execute(schema_sql)
            conn.commit()
            conn.close()
            print("Successfully initialized Supabase PostgreSQL database schema and seed data.")
        return

    # Local SQLite fallback
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

    # Production Registered Members (Employees & Hosts)
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
    if is_postgres_configured():
        print('SmartLocker database cleanly initialized in Supabase PostgreSQL.')
    else:
        print('SmartLocker database cleanly initialized at', DB_PATH)
