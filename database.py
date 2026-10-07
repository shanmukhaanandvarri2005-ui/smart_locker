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
        # while preserving literal '?' inside single-quoted strings
        parts = query.split("'")
        return "'".join(parts[i].replace('?', '%s') if i % 2 == 0 else parts[i] for i in range(len(parts)))

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


_pg_pool = None

def _get_pg_pool():
    global _pg_pool
    if _pg_pool is None:
        db_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DB_URL')
        if db_url and psycopg2:
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            try:
                from psycopg2.pool import ThreadedConnectionPool
                _pg_pool = ThreadedConnectionPool(1, 15, db_url)
                print("[Database] Initialized PostgreSQL connection pool.")
            except Exception as e:
                print(f"[Database] Could not initialize connection pool: {e}")
    return _pg_pool


class PostgresConnectionWrapper:
    """Wraps a psycopg2 connection to mimic SQLite connection behavior and return to pool on close."""
    def __init__(self, conn, pool=None):
        self._conn = conn
        self._pool = pool
        self._closed = False

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor(cursor_factory=DictCursor))

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        if not self._closed:
            self._closed = True
            if self._pool:
                try:
                    self._conn.rollback()
                    self._pool.putconn(self._conn)
                    return
                except Exception:
                    pass
            try:
                self._conn.close()
            except Exception:
                pass

    def __getattr__(self, name):
        return getattr(self._conn, name)


def is_postgres_configured():
    """Checks whether a PostgreSQL / Supabase connection URL is provided."""
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DB_URL')
    return bool(db_url and psycopg2)


def get_db():
    """Returns an active database connection (Supabase PostgreSQL pool if configured, otherwise local SQLite)."""
    pool = _get_pg_pool()
    if pool:
        try:
            raw_conn = pool.getconn()
            return PostgresConnectionWrapper(raw_conn, pool=pool)
        except Exception as e:
            print(f"[Database] Pool getconn fallback: {e}")

    db_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DB_URL')
    if db_url and psycopg2:
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
            if not force_reset:
                cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'members'")
                if cursor.fetchone():
                    conn.close()
                    print("Supabase PostgreSQL tables already exist. Skipping schema reset.")
                    return
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
        department TEXT DEFAULT '',
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
        cover_image TEXT,
        occupancy_status TEXT NOT NULL DEFAULT 'present', -- 'present', 'absent'
        door_status TEXT NOT NULL DEFAULT 'closed',       -- 'closed', 'open'
        lock_status TEXT NOT NULL DEFAULT 'locked',       -- 'locked', 'unlocked'
        last_updated TEXT NOT NULL
    )
    ''')

    try:
        cursor.execute("ALTER TABLE lockers ADD COLUMN cover_image TEXT")
    except Exception:
        pass

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

    # Production Registered Members (Hosts)
    members = [
        (
            'Manoj',
            '1244001510',
            '002',
            None,
            None,
            'employee',
            'active',
            'https://api.dicebear.com/7.x/initials/svg?seed=Manoj&backgroundColor=1e3a8a',
            now_str
        ),
        (
            'Shanmukh',
            '3677855325',
            '001',
            None,
            None,
            'host',
            'active',
            'https://api.dicebear.com/7.x/initials/svg?seed=Shanmukh&backgroundColor=0284c7',
            now_str
        ),
        (
            'K. Ramesh',
            'E2:80:68:10',
            'VIT-FAC-019',
            None,
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

    # 5 Physical Locker Compartments with Book Covers
    lockers = [
        ('Locker 01', 'Modern Control Engineering', 'Katsuhiko Ogata', '978-0136156734', 'Control Systems', 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&auto=format&fit=crop&q=80', 'present', 'closed', 'locked', now_str),
        ('Locker 02', 'Electric Circuits & Networks', 'James W. Nilsson', '978-0134746968', 'Circuit Theory', 'https://images.unsplash.com/photo-1532012164546-f432f2e37b73?w=400&auto=format&fit=crop&q=80', 'present', 'closed', 'locked', now_str),
        ('Locker 03', 'Signals and Systems', 'Alan V. Oppenheim', '978-0138147570', 'Signal Processing', 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&auto=format&fit=crop&q=80', 'present', 'closed', 'locked', now_str),
        ('Locker 04', 'Power Electronics', 'Muhammad H. Rashid', '978-0133125900', 'Power Engineering', 'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400&auto=format&fit=crop&q=80', 'present', 'closed', 'locked', now_str),
        ('Locker 05', 'Microelectronic Circuits', 'Adel S. Sedra', '978-0190853464', 'Electronics', 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=400&auto=format&fit=crop&q=80', 'present', 'closed', 'locked', now_str)
    ]
    cursor.executemany('''
    INSERT INTO lockers (locker_code, book_label, book_author, book_isbn, category, cover_image, occupancy_status, door_status, lock_status, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', lockers)

    conn.commit()


def sync_sqlite_member_upsert(member_dict):
    """Syncs member creation or update to local SQLite database if present."""
    if not os.path.exists(DB_PATH):
        return
    try:
        s_conn = sqlite3.connect(DB_PATH)
        s_cur = s_conn.cursor()
        s_cur.execute("""
            INSERT INTO members (name, rfid_uid, reg_no, department, email, role, status, avatar_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rfid_uid) DO UPDATE SET
                name = excluded.name,
                reg_no = excluded.reg_no,
                department = excluded.department,
                email = excluded.email,
                role = excluded.role,
                status = excluded.status,
                avatar_url = excluded.avatar_url;
        """, (
            member_dict.get('name'),
            member_dict.get('rfid_uid'),
            member_dict.get('reg_no', member_dict.get('rfid_uid')),
            member_dict.get('department', ''),
            member_dict.get('email', ''),
            member_dict.get('role', 'employee'),
            member_dict.get('status', 'active'),
            member_dict.get('avatar_url', ''),
            member_dict.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ))
        s_conn.commit()
        s_conn.close()
    except Exception as e:
        print(f"Notice: local SQLite sync error (non-fatal): {e}")


def sync_sqlite_member_delete(rfid_uid):
    """Syncs member deletion to local SQLite database if present."""
    if not os.path.exists(DB_PATH):
        return
    try:
        s_conn = sqlite3.connect(DB_PATH)
        s_cur = s_conn.cursor()
        s_cur.execute("DELETE FROM loans WHERE member_id IN (SELECT member_id FROM members WHERE rfid_uid = ?)", (rfid_uid,))
        s_cur.execute("DELETE FROM transactions WHERE member_id IN (SELECT member_id FROM members WHERE rfid_uid = ?)", (rfid_uid,))
        s_cur.execute("DELETE FROM members WHERE rfid_uid = ?", (rfid_uid,))
        s_conn.commit()
        s_conn.close()
    except Exception as e:
        print(f"Notice: local SQLite sync delete error (non-fatal): {e}")


if __name__ == '__main__':
    init_db(force_reset=True)
    if is_postgres_configured():
        print('SmartLocker database cleanly initialized in Supabase PostgreSQL.')
    else:
        print('SmartLocker database cleanly initialized at', DB_PATH)
