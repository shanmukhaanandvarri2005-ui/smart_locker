from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
import platform
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime, timedelta
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database import get_db, init_db, sync_sqlite_member_upsert, sync_sqlite_member_delete
from hardware import hardware

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smart_locker_enterprise_secure_key')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Ensure database is initialized
init_db()

@app.context_processor
def inject_global_data():
    """Injects current hardware status and session info into all templates."""
    hw_status = hardware.read_sensors()
    current_user = None
    if 'member_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE member_id = ?", (session['member_id'],))
        row = cursor.fetchone()
        if not row and 'rfid_uid' in session:
            cursor.execute("SELECT * FROM members WHERE rfid_uid = ?", (session['rfid_uid'],))
            row = cursor.fetchone()
            if row:
                session['member_id'] = row['member_id']
                session['name'] = row['name']
                session['role'] = row['role']
        conn.close()
        if row:
            current_user = dict(row)
        else:
            session.clear()
    return {
        "hardware_status": hw_status,
        "current_user": current_user,
        "now": datetime.now()
    }

@app.before_request
def enforce_inactivity_timeout():
    """Enforces 30-second inactivity session timeout across authenticated pages (Employees only; Host has no timeout)."""
    if 'member_id' in session:
        # Host / Staff accounts have NO TIMEOUT
        if session.get('role') in ('staff', 'admin', 'host'):
            return
        if request.endpoint in ('logout', 'static'):
            return
        last_active = session.get('last_active')
        now = datetime.now().timestamp()
        # 30-second inactivity limit with 5-second grace window
        if last_active and (now - last_active > 35):
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({
                    "success": False,
                    "message": "Session expired due to 30 seconds of inactivity.",
                    "timeout": True
                }), 401
            return redirect(url_for('auth_page', timeout='1'))
        session['last_active'] = now

# ----------------- PAGE ROUTES ----------------- #

@app.route('/')
def auth_page():
    """RFID Card Tap / Employee Login Portal."""
    if 'member_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('auth.html')

@app.route('/dashboard')
def dashboard_page():
    """Member Dashboard — Vending Machine Interface."""
    if 'member_id' not in session:
        return redirect(url_for('auth_page'))
    
    conn = get_db()
    cursor = conn.cursor()

    is_host = session.get('role') in ('staff', 'admin', 'host')

    # Active loans for current member
    cursor.execute('''
    SELECT l.*, b.book_label, b.book_author, b.book_isbn, b.locker_code, b.category, b.cover_image
    FROM loans l
    JOIN lockers b ON l.locker_id = b.locker_id
    WHERE l.member_id = ? AND l.status = 'active'
    ORDER BY l.borrowed_at DESC
    ''', (session['member_id'],))
    active_loans = [dict(row) for row in cursor.fetchall()]

    # All lockers (5 vending books)
    cursor.execute('SELECT * FROM lockers ORDER BY locker_code ASC')
    all_lockers = [dict(row) for row in cursor.fetchall()]
    available_lockers = [l for l in all_lockers if l['occupancy_status'] == 'present']

    conn.close()

    single_locker = all_lockers[0] if all_lockers else None

    return render_template('dashboard.html',
                           active_loans=active_loans,
                           available_lockers=available_lockers,
                           all_lockers=all_lockers,
                           single_locker=single_locker,
                           is_host=is_host)

@app.route('/borrow')
def borrow_page():
    """Redirect to dashboard where in-place unlocking and dispensing occurs."""
    if 'member_id' not in session:
        return redirect(url_for('auth_page'))
    return redirect(url_for('dashboard_page'))

@app.route('/return')
def return_page():
    """Redirect to dashboard where in-place unlocking and returning occurs."""
    if 'member_id' not in session:
        return redirect(url_for('auth_page'))
    return redirect(url_for('dashboard_page'))

@app.route('/status')
def status_page():
    """Redirect to dashboard."""
    if 'member_id' not in session:
        return redirect(url_for('auth_page'))
    return redirect(url_for('dashboard_page'))

@app.route('/users')
def users_page():
    """User Management & RFID Registration (Host Only)."""
    if 'member_id' not in session:
        return redirect(url_for('auth_page'))
    if session.get('role') not in ('staff', 'admin', 'host'):
        return redirect(url_for('dashboard_page'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT m.*, 
           (SELECT COUNT(*) FROM loans WHERE member_id = m.member_id AND status = 'active') as active_loans_count,
           (SELECT COUNT(*) FROM transactions WHERE member_id = m.member_id) as total_transactions
    FROM members m
    ORDER BY m.member_id ASC
    ''')
    all_members = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template('users.html', all_members=all_members)

@app.route('/activity')
def activity_page():
    """All Member Activity History (Host Only) — Feature to see all activities of every person."""
    if 'member_id' not in session:
        return redirect(url_for('auth_page'))
    if session.get('role') not in ('staff', 'admin', 'host'):
        return redirect(url_for('dashboard_page'))
    
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT t.*, 
           m.name as member_name, m.reg_no as member_reg_no, m.rfid_uid as member_rfid, 
           m.avatar_url as member_avatar, m.role as member_role,
           b.book_label, b.locker_code
    FROM transactions t
    LEFT JOIN members m ON t.member_id = m.member_id
    LEFT JOIN lockers b ON t.locker_id = b.locker_id
    ORDER BY t.timestamp DESC
    ''')
    all_activities = [dict(row) for row in cursor.fetchall()]

    # Quick overview metrics for host
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_activities_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE operation = 'borrow' AND result = 'success'")
    total_borrows_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE operation = 'return' AND result = 'success'")
    total_returns_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT member_id) FROM loans WHERE status = 'active'")
    active_borrowers_count = cursor.fetchone()[0]

    conn.close()

    return render_template('activity.html',
                           all_activities=all_activities,
                           total_activities_count=total_activities_count,
                           total_borrows_count=total_borrows_count,
                           total_returns_count=total_returns_count,
                           active_borrowers_count=active_borrowers_count)

@app.route('/logout')
def logout():
    is_timeout = request.args.get('timeout') == '1'
    session.clear()
    if is_timeout:
        return redirect(url_for('auth_page', timeout='1'))
    return redirect(url_for('auth_page'))

def extract_first_rfid_scan(raw: str) -> str:
    """Extracts only the first RFID scan from any concatenated, repeated, or rapid multi-tap input."""
    if not raw:
        return ""
    s = str(raw).strip()
    # If separated by newlines, carriage returns, commas or spaces, take the first token
    lines = [p.strip() for p in s.replace('\r', '\n').replace(',', ' ').split('\n') if p.strip()]
    if lines:
        s = lines[0].split()[0]
    
    n = len(s)
    # Check if the string consists of repeated identical sub-patterns (e.g. 10 digits repeated 2x, 3x)
    for k in range(4, (n // 2) + 1):
        if n % k == 0:
            chunk = s[:k]
            if chunk * (n // k) == s:
                return chunk
    
    # If standard 10-digit EM4100 RFID scan was repeated or had trailing keystrokes
    if n > 10 and s[:10].isdigit():
        return s[:10]
        
    return s


# ----------------- REST API ENDPOINTS ----------------- #

@app.route('/api/auth/rfid', methods=['POST'])
def api_auth_rfid():
    """Authenticates a user via RFID card UID, accepting only the first scan."""
    data = request.get_json() or {}
    raw_identifier = data.get('rfid_uid', '').strip()

    if not raw_identifier:
        return jsonify({"success": False, "message": "RFID Card UID is required."}), 400

    clean_id = extract_first_rfid_scan(raw_identifier)

    conn = get_db()
    cursor = conn.cursor()

    # 1. Flexible exact matching on clean_id and raw_identifier
    cursor.execute("""
        SELECT * FROM members 
        WHERE LOWER(TRIM(rfid_uid)) = LOWER(?) 
           OR LOWER(TRIM(reg_no)) = LOWER(?)
           OR REPLACE(REPLACE(LOWER(rfid_uid), ':', ''), '-', '') = REPLACE(REPLACE(LOWER(?), ':', ''), '-', '')
           OR LOWER(TRIM(rfid_uid)) = LOWER(?) 
           OR LOWER(TRIM(reg_no)) = LOWER(?)
           OR REPLACE(REPLACE(LOWER(rfid_uid), ':', ''), '-', '') = REPLACE(REPLACE(LOWER(?), ':', ''), '-', '')
    """, (clean_id, clean_id, clean_id, raw_identifier, raw_identifier, raw_identifier))
    member = cursor.fetchone()

    # 2. Resilient fallback: Match prefix against active registered members
    if not member:
        cursor.execute("SELECT * FROM members WHERE status = 'active' OR status IS NULL")
        all_members = cursor.fetchall()
        for m in sorted(all_members, key=lambda x: len(x['rfid_uid'] or ''), reverse=True):
            m_uid = (m['rfid_uid'] or '').strip()
            m_reg = (m['reg_no'] or '').strip()
            if m_uid and len(m_uid) >= 4:
                norm_uid = m_uid.replace(':', '').replace('-', '').lower()
                norm_clean = clean_id.replace(':', '').replace('-', '').lower()
                norm_raw = raw_identifier.replace(':', '').replace('-', '').lower()
                if clean_id.startswith(m_uid) or raw_identifier.startswith(m_uid) or norm_clean.startswith(norm_uid) or norm_raw.startswith(norm_uid):
                    member = m
                    break
            if m_reg and len(m_reg) >= 4:
                if clean_id.startswith(m_reg) or raw_identifier.startswith(m_reg):
                    member = m
                    break

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not member:
        cursor.execute('''
        INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
        VALUES (NULL, NULL, 'auth', 'rejected', ?, ?)
        ''', (now_str, f"Unregistered credential: {clean_id or raw_identifier}"))
        conn.commit()
        conn.close()
        hardware.set_led('RED')
        return jsonify({"success": False, "message": f"Unrecognized RFID credential [{clean_id or raw_identifier}]. Please contact facility administrator."}), 401

    member = dict(member)
    if member['status'] != 'active':
        conn.close()
        return jsonify({"success": False, "message": "Membership account is inactive."}), 403

    session['member_id'] = member['member_id']
    session['name'] = member['name']
    session['role'] = member['role']
    session['rfid_uid'] = member['rfid_uid']
    session['last_active'] = datetime.now().timestamp()

    cursor.execute('''
    INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
    VALUES (?, NULL, 'auth', 'success', ?, ?)
    ''', (member['member_id'], now_str, f"Member {member['name']} logged in via {member['rfid_uid']}"))
    conn.commit()
    conn.close()

    hardware.set_led('GREEN')
    return jsonify({
        "success": True,
        "message": f"Welcome, {member['name']}",
        "member": member,
        "redirect_url": url_for('dashboard_page')
    })

@app.route('/api/heartbeat', methods=['POST'])
def api_heartbeat():
    """Refreshes the session activity timestamp when user requests to stay logged in."""
    if 'member_id' in session:
        session['last_active'] = datetime.now().timestamp()
        return jsonify({"success": True, "last_active": session['last_active']})
    return jsonify({"success": False, "message": "No active session"}), 401

@app.route('/api/status', methods=['GET'])
@app.route('/api/locker/status', methods=['GET'])
def api_locker_status():
    """Returns real-time sensor and controller telemetry."""
    status = hardware.read_sensors()
    return jsonify({"success": True, "status": status})

@app.route('/api/locker/unlock', methods=['POST'])
def api_locker_unlock():
    """Direct hardware unlock endpoint triggering ESP8266 relay and solenoid."""
    data = request.get_json() or {}
    duration = int(data.get('duration', 4))
    hardware.unlock_solenoid(duration_sec=duration, card_uid=session.get('rfid_uid'))
    return jsonify({
        "success": True,
        "message": f"Unlock signal sent to ESP8266 relay for {duration} seconds.",
        "status": hardware.read_sensors()
    })

@app.route('/api/locker/borrow', methods=['POST'])
def api_locker_borrow():
    """Executes verified multi-book or single-book borrow sequence."""
    if 'member_id' not in session:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json() or {}
    locker_ids = data.get('locker_ids')
    if locker_ids is None:
        single_id = data.get('locker_id')
        if single_id is not None:
            locker_ids = [single_id]
        else:
            locker_ids = []

    if not locker_ids:
        return jsonify({"success": False, "message": "Please select at least one book to borrow."}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Re-verify and self-heal session member_id if needed
    cursor.execute("SELECT * FROM members WHERE member_id = ?", (session['member_id'],))
    member = cursor.fetchone()
    if not member and 'rfid_uid' in session:
        cursor.execute("SELECT * FROM members WHERE rfid_uid = ?", (session['rfid_uid'],))
        member = cursor.fetchone()
        if member:
            session['member_id'] = member['member_id']
            session['name'] = member['name']
            session['role'] = member['role']

    if not member:
        conn.close()
        session.clear()
        return jsonify({"success": False, "message": "Session expired or user deleted. Please log in again."}), 401

    # Verify each requested locker
    borrow_items = []
    for lid in locker_ids:
        try:
            lid_int = int(lid)
        except (ValueError, TypeError):
            continue
        cursor.execute("SELECT * FROM lockers WHERE locker_id = ?", (lid_int,))
        locker = cursor.fetchone()
        if not locker:
            conn.close()
            return jsonify({"success": False, "message": f"Locker compartment #{lid} was not found."}), 404
        if locker['occupancy_status'] != 'present':
            conn.close()
            return jsonify({"success": False, "message": f"'{locker['book_label']}' ({locker['locker_code']}) is currently already borrowed."}), 400
        borrow_items.append(locker)

    if not borrow_items:
        conn.close()
        return jsonify({"success": False, "message": "No valid lockers were selected for checkout."}), 400

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    due_str = 'No Due Date'
    dispensed_codes = []
    dispensed_titles = []

    try:
        # Trigger physical lock release & green LED on ESP8266 controller
        unlock_duration = max(4, 2 + len(borrow_items) * 2)
        hardware.unlock_solenoid(duration_sec=unlock_duration, card_uid=session.get('rfid_uid'))

        for locker in borrow_items:
            lid = locker['locker_id']
            dispensed_codes.append(locker['locker_code'])
            dispensed_titles.append(locker['book_label'])

            cursor.execute('''
            UPDATE lockers SET occupancy_status = 'absent', lock_status = 'unlocked', last_updated = ?
            WHERE locker_id = ?
            ''', (now_str, lid))

            cursor.execute('''
            INSERT INTO loans (member_id, locker_id, borrowed_at, due_date, status)
            VALUES (?, ?, ?, ?, 'active')
            ''', (session['member_id'], lid, now_str, due_str))

            cursor.execute('''
            INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
            VALUES (?, ?, 'borrow', 'success', ?, ?)
            ''', (session['member_id'], lid, now_str, f"Dispensed {locker['book_label']} ({locker['locker_code']}) to {session.get('name')}"))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": f"Borrow transaction error: {str(e)}"}), 500

    conn.close()

    codes_str = ", ".join(dispensed_codes)
    return jsonify({
        "success": True,
        "message": f"{codes_str} unlocked! Please collect your {len(dispensed_titles)} book(s) and close the doors.",
        "count": len(dispensed_titles),
        "locker_codes": dispensed_codes,
        "book_labels": dispensed_titles,
        "due_date": "No Due Date"
    })

@app.route('/api/locker/return', methods=['POST'])
def api_locker_return():
    """Executes verified multi-book or single-book return sequence."""
    if 'member_id' not in session:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json() or {}
    loan_ids = data.get('loan_ids')
    if loan_ids is None:
        single_id = data.get('loan_id')
        if single_id is not None:
            loan_ids = [single_id]
        else:
            loan_ids = []

    if not loan_ids:
        return jsonify({"success": False, "message": "Please select at least one borrowed book to return."}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Re-verify and self-heal session member_id if needed
    cursor.execute("SELECT * FROM members WHERE member_id = ?", (session['member_id'],))
    member = cursor.fetchone()
    if not member and 'rfid_uid' in session:
        cursor.execute("SELECT * FROM members WHERE rfid_uid = ?", (session['rfid_uid'],))
        member = cursor.fetchone()
        if member:
            session['member_id'] = member['member_id']
            session['name'] = member['name']
            session['role'] = member['role']

    if not member:
        conn.close()
        session.clear()
        return jsonify({"success": False, "message": "Session expired or user deleted. Please log in again."}), 401

    return_records = []
    for lid in loan_ids:
        try:
            lid_int = int(lid)
        except (ValueError, TypeError):
            continue
        cursor.execute('''
        SELECT l.*, b.book_label, b.locker_id, b.locker_code 
        FROM loans l
        JOIN lockers b ON l.locker_id = b.locker_id
        WHERE l.loan_id = ? AND l.member_id = ? AND l.status = 'active'
        ''', (lid_int, session['member_id']))
        loan = cursor.fetchone()
        if not loan:
            conn.close()
            return jsonify({"success": False, "message": f"Active loan record #{lid} not found."}), 404
        return_records.append(loan)

    if not return_records:
        conn.close()
        return jsonify({"success": False, "message": "No valid active loans were selected for return."}), 400

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    returned_codes = []
    returned_titles = []

    try:
        # Trigger lock release (ESP8266 + Solenoid)
        unlock_duration = max(4, 2 + len(return_records) * 2)
        hardware.unlock_solenoid(duration_sec=unlock_duration, card_uid=session.get('rfid_uid'))

        for loan in return_records:
            returned_codes.append(loan['locker_code'])
            returned_titles.append(loan['book_label'])

            cursor.execute('''
            UPDATE loans SET returned_at = ?, status = 'returned'
            WHERE loan_id = ?
            ''', (now_str, loan['loan_id']))

            cursor.execute('''
            UPDATE lockers SET occupancy_status = 'present', lock_status = 'locked', last_updated = ?
            WHERE locker_id = ?
            ''', (now_str, loan['locker_id']))

            cursor.execute('''
            INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
            VALUES (?, ?, 'return', 'success', ?, ?)
            ''', (session['member_id'], loan['locker_id'], now_str, f"Returned {loan['book_label']} ({loan['locker_code']}) verified."))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": f"Return transaction error: {str(e)}"}), 500

    conn.close()

    codes_str = ", ".join(returned_codes)
    return jsonify({
        "success": True,
        "message": f"{codes_str} unlocked! Please return your {len(returned_titles)} book(s) and close the doors.",
        "count": len(returned_titles),
        "locker_codes": returned_codes,
        "book_labels": returned_titles
    })

@app.route('/api/lockers/<int:locker_id>/book', methods=['POST', 'PUT'])
def api_edit_locker_book(locker_id):
    """Updates the book name and author in a locker compartment (Host Only)."""
    if 'member_id' not in session or session.get('role') not in ('staff', 'admin', 'host'):
        return jsonify({"success": False, "message": "Host authorization required."}), 403

    data = request.get_json() or {}
    book_label = data.get('book_label', '').strip()
    book_author = data.get('book_author', '').strip()

    if not book_label:
        return jsonify({"success": False, "message": "Book name is required."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lockers WHERE locker_id = ?", (locker_id,))
    locker = cursor.fetchone()
    if not locker:
        conn.close()
        return jsonify({"success": False, "message": "Locker compartment not found."}), 404

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if book_author:
        cursor.execute('''
        UPDATE lockers SET book_label = ?, book_author = ?, last_updated = ?
        WHERE locker_id = ?
        ''', (book_label, book_author, now_str, locker_id))
    else:
        cursor.execute('''
        UPDATE lockers SET book_label = ?, last_updated = ?
        WHERE locker_id = ?
        ''', (book_label, now_str, locker_id))

    cursor.execute('''
    INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
    VALUES (?, ?, 'maintenance', 'success', ?, ?)
    ''', (session.get('member_id'), locker_id, now_str, f"Host updated book title to '{book_label}'"))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Book name updated to '{book_label}' successfully.",
        "book_label": book_label,
        "book_author": book_author or locker['book_author']
    })

@app.route('/api/users', methods=['POST'])
def api_add_user():
    """Registers a new company employee or host (Host Only)."""
    if 'member_id' not in session or session.get('role') not in ('staff', 'admin', 'host'):
        return jsonify({"success": False, "message": "Host authorization required."}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    rfid_uid = data.get('rfid_uid', '').strip()
    # Default reg_no to rfid_uid to satisfy SQLite NOT NULL schema constraint
    reg_no = data.get('reg_no', '').strip() or rfid_uid
    email = data.get('email', '').strip()
    role = data.get('role', 'employee').strip().lower()
    if role not in ('host', 'employee'):
        role = 'host' if role in ('staff', 'admin') else 'employee'

    department = data.get('department', '').strip()

    if not name or not rfid_uid:
        return jsonify({"success": False, "message": "Name and RFID UID are required."}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        avatar_url = f"https://api.dicebear.com/7.x/initials/svg?seed={name}&backgroundColor=123b67"
        cursor.execute('''
        INSERT INTO members (name, rfid_uid, reg_no, department, email, role, status, avatar_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
        ''', (name, rfid_uid, reg_no, department, email, role, avatar_url, now_str))

        cursor.execute('''
        INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
        VALUES (?, NULL, 'maintenance', 'success', ?, ?)
        ''', (session.get('member_id'), now_str, f"Host registered new member {name} (Role: {role}, UID: {rfid_uid})"))

        conn.commit()
        conn.close()

        # Permanent sync to local SQLite
        sync_sqlite_member_upsert({
            'name': name,
            'rfid_uid': rfid_uid,
            'reg_no': reg_no,
            'department': department,
            'email': email,
            'role': role,
            'status': 'active',
            'avatar_url': avatar_url,
            'created_at': now_str
        })

        return jsonify({"success": True, "message": f"Member {name} registered successfully!"})
    except Exception as e:
        conn.close()
        err_msg = str(e)
        if 'unique' in err_msg.lower() or 'integrity' in err_msg.lower():
            return jsonify({"success": False, "message": "RFID UID is already enrolled."}), 409
        return jsonify({"success": False, "message": f"Could not enroll user: {err_msg}"}), 400

@app.route('/api/users/<int:member_id>', methods=['PUT'])
@app.route('/api/users/<int:member_id>/update', methods=['POST'])
def api_update_user(member_id):
    """Updates member details such as name, RFID UID, or role permanently (Host Only)."""
    if 'member_id' not in session or session.get('role') not in ('staff', 'admin', 'host'):
        return jsonify({"success": False, "message": "Host authorization required."}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    rfid_uid = data.get('rfid_uid', '').strip()
    role = data.get('role', '').strip().lower()
    if role not in ('host', 'employee'):
        role = 'host' if role in ('staff', 'admin') else 'employee'

    department = data.get('department', '').strip()

    if not name or not rfid_uid:
        return jsonify({"success": False, "message": "Name and RFID UID are required."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
    member = cursor.fetchone()
    if not member:
        conn.close()
        return jsonify({"success": False, "message": "Member not found."}), 404

    try:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        avatar_url = f"https://api.dicebear.com/7.x/initials/svg?seed={name}&backgroundColor=123b67"

        cursor.execute('''
        UPDATE members 
        SET name = ?, rfid_uid = ?, reg_no = ?, role = ?, avatar_url = ?
        WHERE member_id = ?
        ''', (name, rfid_uid, rfid_uid, role, avatar_url, member_id))

        cursor.execute('''
        INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
        VALUES (?, NULL, 'maintenance', 'success', ?, ?)
        ''', (session.get('member_id'), now_str, f"Host updated member {name} to Role: {role}, UID: {rfid_uid}"))

        conn.commit()
        conn.close()

        # Update current session if the host updated themselves
        if session.get('member_id') == member_id:
            session['name'] = name
            session['role'] = role
            session['rfid_uid'] = rfid_uid

        # Permanent sync to local SQLite
        sync_sqlite_member_upsert({
            'name': name,
            'rfid_uid': rfid_uid,
            'reg_no': rfid_uid,
            'department': department or member.get('department', ''),
            'email': member.get('email', ''),
            'role': role,
            'status': member.get('status', 'active'),
            'avatar_url': avatar_url,
            'created_at': now_str
        })

        return jsonify({"success": True, "message": f"Member '{name}' updated successfully."})
    except Exception as e:
        conn.close()
        err_msg = str(e)
        if 'unique' in err_msg.lower() or 'integrity' in err_msg.lower():
            return jsonify({"success": False, "message": "RFID UID is already enrolled by another member."}), 409
        return jsonify({"success": False, "message": f"Could not update member: {err_msg}"}), 400

@app.route('/api/users/<int:member_id>', methods=['DELETE'])
@app.route('/api/users/<int:member_id>/delete', methods=['POST'])
def api_remove_user(member_id):
    """Removes a member from the registry permanently (Host Only)."""
    if 'member_id' not in session or session.get('role') not in ('staff', 'admin', 'host'):
        return jsonify({"success": False, "message": "Host authorization required."}), 403

    if session.get('member_id') == member_id:
        return jsonify({"success": False, "message": "You cannot remove your own active host account."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
    member = cursor.fetchone()
    if not member:
        conn.close()
        return jsonify({"success": False, "message": "Member not found."}), 404

    # Check for active loans
    cursor.execute("SELECT COUNT(*) FROM loans WHERE member_id = ? AND status = 'active'", (member_id,))
    active_count = cursor.fetchone()[0]
    if active_count > 0:
        conn.close()
        return jsonify({
            "success": False,
            "message": f"Cannot remove {member['name']}. They currently have an active borrowed book that must be returned first."
        }), 400

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Safe delete of past transactions, loans, and member record
    cursor.execute("DELETE FROM loans WHERE member_id = ?", (member_id,))
    cursor.execute("DELETE FROM transactions WHERE member_id = ?", (member_id,))
    cursor.execute("DELETE FROM members WHERE member_id = ?", (member_id,))

    cursor.execute('''
    INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
    VALUES (?, NULL, 'maintenance', 'success', ?, ?)
    ''', (session.get('member_id'), now_str, f"Host removed member {member['name']} ({member['rfid_uid']})"))

    conn.commit()
    conn.close()

    # Permanent sync deletion to local SQLite
    sync_sqlite_member_delete(member['rfid_uid'])

    return jsonify({"success": True, "message": f"Member '{member['name']}' has been removed successfully."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
