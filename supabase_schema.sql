-- ==========================================================
-- SmartLocker Database Schema & Initial Seed for Supabase (PostgreSQL)
-- ==========================================================

-- Clean existing tables if re-initializing
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS loans CASCADE;
DROP TABLE IF EXISTS lockers CASCADE;
DROP TABLE IF EXISTS members CASCADE;

-- 1. Members Table (Employees & Hosts)
CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    rfid_uid TEXT UNIQUE NOT NULL,
    reg_no TEXT UNIQUE NOT NULL,
    department TEXT DEFAULT 'Electrical and Electronics Engineering',
    email TEXT,
    role TEXT NOT NULL DEFAULT 'employee' CHECK (role IN ('employee', 'host', 'staff', 'admin')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Lockers Table (Physical Compartments & Inventory)
CREATE TABLE lockers (
    locker_id SERIAL PRIMARY KEY,
    locker_code TEXT UNIQUE NOT NULL,
    book_label TEXT NOT NULL,
    book_author TEXT NOT NULL,
    book_isbn TEXT,
    category TEXT DEFAULT 'Engineering',
    occupancy_status TEXT NOT NULL DEFAULT 'present' CHECK (occupancy_status IN ('present', 'absent')),
    door_status TEXT NOT NULL DEFAULT 'closed' CHECK (door_status IN ('closed', 'open')),
    lock_status TEXT NOT NULL DEFAULT 'locked' CHECK (lock_status IN ('locked', 'unlocked')),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Loans Table (Active & Past Book Borrowings)
CREATE TABLE loans (
    loan_id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    locker_id INTEGER NOT NULL REFERENCES lockers(locker_id) ON DELETE CASCADE,
    borrowed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    due_date TEXT,
    returned_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'returned'))
);

-- 4. Transactions Table (Circulation Audit Log)
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(member_id) ON DELETE SET NULL,
    locker_id INTEGER REFERENCES lockers(locker_id) ON DELETE SET NULL,
    operation TEXT NOT NULL, -- 'borrow', 'return', 'auth', 'maintenance'
    result TEXT NOT NULL,    -- 'success', 'rejected', 'error'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    details TEXT
);

-- Indices for fast lookups
CREATE INDEX idx_members_rfid ON members(rfid_uid);
CREATE INDEX idx_lockers_code ON lockers(locker_code);
CREATE INDEX idx_loans_member_status ON loans(member_id, status);
CREATE INDEX idx_transactions_member ON transactions(member_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp DESC);

-- ==========================================================
-- SEED DATA
-- ==========================================================

-- Seed Members (Hosts)
INSERT INTO members (name, rfid_uid, reg_no, department, email, role, status, avatar_url)
VALUES 
(
    'Manoj',
    '1244001510',
    '1244001510',
    'Electrical and Electronics Engineering',
    NULL,
    'host',
    'active',
    'https://api.dicebear.com/7.x/initials/svg?seed=Manoj&backgroundColor=1e3a8a'
),
(
    'Shanmukh',
    '3677855325',
    '3677855325',
    'Electrical and Electronics Engineering',
    NULL,
    'host',
    'active',
    'https://api.dicebear.com/7.x/initials/svg?seed=Shanmukh&backgroundColor=0284c7'
),
(
    'K. Ramesh',
    'E2:80:68:10',
    'VIT-FAC-019',
    'Electrical and Electronics Engineering',
    NULL,
    'host',
    'active',
    'https://api.dicebear.com/7.x/initials/svg?seed=K+Ramesh&backgroundColor=002549'
);

-- Seed Locker Compartment
INSERT INTO lockers (locker_code, book_label, book_author, book_isbn, category, occupancy_status, door_status, lock_status)
VALUES 
(
    'Locker 01',
    'Modern Control Engineering (5th Edition)',
    'Katsuhiko Ogata',
    '978-0136156734',
    'Control Systems',
    'present',
    'closed',
    'locked'
);
