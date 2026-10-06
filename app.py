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

from database import get_db, init_db
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
    """Member Dashboard."""
    if 'member_id' not in session:
        return redirect(url_for('auth_page'))
    
    conn = get_db()
    cursor = conn.cursor()

    # Active loans for current member
    cursor.execute('''
    SELECT l.*, b.book_label, b.book_author, b.book_isbn, b.locker_code, b.category
    FROM loans l
    JOIN lockers b ON l.locker_id = b.locker_id
    WHERE l.member_id = ? AND l.status = 'active'
    ORDER BY l.borrowed_at DESC
    ''', (session['member_id'],))
    active_loans = [dict(row) for row in cursor.fetchall()]

    # Available books
    cursor.execute('SELECT * FROM lockers ORDER BY locker_code ASC')
    all_lockers = [dict(row) for row in cursor.fetchall()]
    available_lockers = [l for l in all_lockers if l['occupancy_status'] == 'present']

    # Recent transactions for current member
    cursor.execute('''
    SELECT t.*, b.book_label, b.locker_code
    FROM transactions t
    LEFT JOIN lockers b ON t.locker_id = b.locker_id
    WHERE t.member_id = ?
    ORDER BY t.timestamp DESC LIMIT 8
    ''', (session['member_id'],))
    recent_transactions = [dict(row) for row in cursor.fetchall()]

    conn.close()

    single_locker = all_lockers[0] if all_lockers else None

    return render_template('dashboard.html',
                           active_loans=active_loans,
                           available_lockers=available_lockers,
                           all_lockers=all_lockers,
                           single_locker=single_locker,
                           recent_transactions=recent_transactions)

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
    """System Status & Hardware Diagnostics (Host Only)."""
    if 'member_id' not in session:
        return redirect(url_for('auth_page'))
    if session.get('role') not in ('staff', 'admin', 'host'):
        return redirect(url_for('dashboard_page'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT t.*, m.name as member_name, b.book_label, b.locker_code
    FROM transactions t
    LEFT JOIN members m ON t.member_id = m.member_id
    LEFT JOIN lockers b ON t.locker_id = b.locker_id
    ORDER BY t.timestamp DESC LIMIT 15
    ''')
    recent_logs = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT * FROM lockers ORDER BY locker_code ASC')
    lockers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    cpu_percent = psutil.cpu_percent(interval=None) if psutil else 12.4
    mem = psutil.virtual_memory() if psutil else None
    mem_used = f"{mem.used / (1024**3):.1f} GB / {mem.total / (1024**3):.1f} GB" if mem else "480 MB / 1024 MB"

    sys_info = {
        "os": platform.system() + " " + platform.release(),
        "arch": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_usage": cpu_percent,
        "mem_usage": mem_used,
        "controller": "Raspberry Pi 3 Model B+ (ARMv7 1.4GHz)",
        "ip_address": "127.0.0.1:5000"
    }

    return render_template('status.html', recent_logs=recent_logs, sys_info=sys_info, lockers=lockers)

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

@app.route('/logout')
def logout():
    is_timeout = request.args.get('timeout') == '1'
    session.clear()
    if is_timeout:
        return redirect(url_for('auth_page', timeout='1'))
    return redirect(url_for('auth_page'))

# ----------------- REST API ENDPOINTS ----------------- #

@app.route('/api/auth/rfid', methods=['POST'])
def api_auth_rfid():
    """Authenticates a user via RFID card UID."""
    data = request.get_json() or {}
    identifier = data.get('rfid_uid', '').strip()

    if not identifier:
        return jsonify({"success": False, "message": "RFID Card UID is required."}), 400

    conn = get_db()
    cursor = conn.cursor()
    clean_id = identifier.strip()
    # Flexible matching: Case-insensitive and colon/hyphen-insensitive
    cursor.execute("""
        SELECT * FROM members 
        WHERE LOWER(TRIM(rfid_uid)) = LOWER(?) 
           OR LOWER(TRIM(reg_no)) = LOWER(?)
           OR REPLACE(REPLACE(LOWER(rfid_uid), ':', ''), '-', '') = REPLACE(REPLACE(LOWER(?), ':', ''), '-', '')
    """, (clean_id, clean_id, clean_id))
    member = cursor.fetchone()

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not member:
        cursor.execute('''
        INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
        VALUES (NULL, NULL, 'auth', 'rejected', ?, ?)
        ''', (now_str, f"Unregistered credential: {identifier}"))
        conn.commit()
        conn.close()
        hardware.set_led('RED')
        return jsonify({"success": False, "message": f"Unrecognized RFID credential [{identifier}]. Please contact facility administrator."}), 401

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

@app.route('/api/locker/borrow', methods=['POST'])
def api_locker_borrow():
    """Executes verified borrow sequence according to SRS and SAD."""
    if 'member_id' not in session:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json() or {}
    locker_id = data.get('locker_id')

    if not locker_id:
        return jsonify({"success": False, "message": "Locker ID is required"}), 400

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

    cursor.execute("SELECT * FROM lockers WHERE locker_id = ?", (locker_id,))
    locker = cursor.fetchone()

    if not locker:
        conn.close()
        return jsonify({"success": False, "message": "Locker not found"}), 404

    if locker['occupancy_status'] != 'present':
        conn.close()
        return jsonify({"success": False, "message": "Book is already checked out of this locker."}), 400

    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    due_str = 'No Due Date'

    try:
        # Trigger physical lock release & green indicator
        hardware.unlock_solenoid(duration_sec=20)

        # Update database
        cursor.execute('''
        UPDATE lockers SET occupancy_status = 'absent', lock_status = 'unlocked', last_updated = ?
        WHERE locker_id = ?
        ''', (now_str, locker_id))

        cursor.execute('''
        INSERT INTO loans (member_id, locker_id, borrowed_at, due_date, status)
        VALUES (?, ?, ?, ?, 'active')
        ''', (session['member_id'], locker_id, now_str, due_str))

        cursor.execute('''
        INSERT INTO transactions (member_id, locker_id, operation, result, timestamp, details)
        VALUES (?, ?, 'borrow', 'success', ?, ?)
        ''', (session['member_id'], locker_id, now_str, f"Dispensed {locker['book_label']} ({locker['locker_code']}) to {session.get('name')}"))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": f"Borrow transaction error: {str(e)}"}), 500

    conn.close()

    return jsonify({
        "success": True,
        "message": f"{locker['locker_code']} unlocked! Please collect '{locker['book_label']}' and close the compartment.",
        "locker_code": locker['locker_code'],
        "book_label": locker['book_label'],
        "due_date": "No Due Date"
    })

@app.route('/api/locker/return', methods=['POST'])
def api_locker_return():
    """Executes verified return sequence according to SRS and SAD."""
    if 'member_id' not in session:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json() or {}
    loan_id = data.get('loan_id')

    if not loan_id:
        return jsonify({"success": False, "message": "Loan ID is required"}), 400

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

    cursor.execute('''
    SELECT l.*, b.book_label, b.locker_id, b.locker_code 
    FROM loans l
    JOIN lockers b ON l.locker_id = b.locker_id
    WHERE l.loan_id = ? AND l.member_id = ? AND l.status = 'active'
    ''', (loan_id, session['member_id']))
    loan = cursor.fetchone()

    if not loan:
        conn.close()
        return jsonify({"success": False, "message": "Active loan record not found."}), 404

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Trigger lock release
        hardware.unlock_solenoid(duration_sec=20)

        # Update loan
        cursor.execute('''
        UPDATE loans SET returned_at = ?, status = 'returned'
        WHERE loan_id = ?
        ''', (now_str, loan_id))

        # Update locker status
        cursor.execute('''
        UPDATE lockers SET occupancy_status = 'present', lock_status = 'locked', last_updated = ?
        WHERE locker_id = ?
        ''', (now_str, loan['locker_id']))

        # Transaction audit log
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

    return jsonify({
        "success": True,
        "message": f"{loan['locker_code']} unlocked. '{loan['book_label']}' successfully returned.",
        "locker_code": loan['locker_code'],
        "book_label": loan['book_label']
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
    """Registers a new company employee (Host Only)."""
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
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Member {name} registered successfully!"})
    except Exception as e:
        conn.close()
        err_msg = str(e)
        if 'unique' in err_msg.lower() or 'integrity' in err_msg.lower():
            return jsonify({"success": False, "message": "RFID UID is already enrolled."}), 409
        return jsonify({"success": False, "message": f"Could not enroll user: {err_msg}"}), 400

@app.route('/api/users/<int:member_id>', methods=['DELETE'])
def api_remove_user(member_id):
    """Removes a member from the registry (Host Only)."""
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

    # Safe delete of past transactions, loans, and member record
    cursor.execute("DELETE FROM loans WHERE member_id = ?", (member_id,))
    cursor.execute("DELETE FROM transactions WHERE member_id = ?", (member_id,))
    cursor.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Member '{member['name']}' has been removed successfully."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
