# 📚 SmartLocker: IoT-Based Automated Library Book Dispensing and Return System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi%203%20B%2B-red.svg)](https://www.raspberrypi.com/)

**SmartLocker** is an intelligent, automated library locker system designed to dispense, return, and inventory books using RFID authentication, sensor verification, and automated electronic solenoid locks. It features an enterprise-grade responsive web interface tailored for both **Employees** and **Hosts (Administrators)**.

---

## 🌟 Key Features

### 👤 Role-Based Access Control (RBAC)
- **Employee Portal**:
  - Instant RFID login card tap.
  - Browse available compartment inventory.
  - Dispense/Borrow books with automatic solenoid unlock and book sensor detection.
  - Return books with optical shelf verification and automatic re-locking.
  - Personal borrowing activity and transaction history.
- **Host (Admin) Portal**:
  - Full locker compartment management.
  - **Edit Book Name & Author**: Update the stored book details directly from the dashboard or compartment matrix.
  - **Employee Directory**: Register new employees, assign RFID tags, and manage active status.
  - **System Diagnostics**: Live controller telemetry (CPU, RAM, OS, IP address, uptime) and raw hardware pin monitors.
  - **Audit Logs**: Detailed transaction history with timestamps and locker operation logs.

### ⚡ Hardware Interfacing & Safety
- **Dual-Mode Execution**:
  - **Physical Deployment**: Raspberry Pi 3 Model B/B+ using `gpiozero` to control 12V solenoid locks via relay/MOSFET drivers and read IR/optical shelf sensors + magnetic reed door switches.
  - **Development Simulation Mode**: Integrated software hardware emulator allows full testing on Windows/Linux/macOS without physical GPIO pins.
- **RFID Authentication**: USB / UART RFID reader support with automatic UID resolution.

---

## 📁 Repository Structure

```
smart_locker/
├── app.py                  # Main Flask application and REST API endpoints
├── database.py             # SQLite schema initialization and seed data
├── hardware.py             # Hardware controller (GPIO / Mock simulator)
├── requirements.txt        # Python package dependencies
├── smart_locker.db         # SQLite database file
├── templates/              # Jinja2 HTML templates
│   ├── auth.html           # RFID card tap & login screen
│   ├── dashboard.html      # Main employee & host dashboard
│   ├── borrow.html         # Book borrow & dispensing flow
│   ├── return.html         # Book return & shelf verification flow
│   ├── status.html         # Host system diagnostics & locker matrix
│   ├── users.html          # Host employee directory management
│   └── inactivity_modal.html # Session inactivity modal component
├── docs/                   # Engineering & design documentation
│   ├── pdr.md              # Preliminary Design Report
│   ├── sad.md              # System Architecture Document
│   └── srs.md              # Software Requirements Specification
└── stitch_screens/         # UI design prototypes and specifications
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8 or higher
- Git

### 2. Installation

Clone this repository:
```bash
git clone https://github.com/shanmukhaanandvarri2005-ui/smart_locker.git
cd smart_locker
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Database Configuration (Supabase or SQLite)

#### Option A: Supabase Cloud Database (PostgreSQL)
1. In your Supabase project, execute `supabase_schema.sql` in the **SQL Editor**.
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Set your Supabase connection string in `.env`:
   ```env
   DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
   ```

#### Option B: Local SQLite (Offline / Standalone)
Simply leave `DATABASE_URL` unset in `.env`. The system will automatically use the built-in `smart_locker.db`.

### 4. Initialize Database (Optional)
```bash
python database.py
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Default RFID Credentials (Demo)

| Role | Name | RFID UID | Permissions |
| :--- | :--- | :--- | :--- |
| **Host** | Manoj | `1244001510` | Full administrative control, system diagnostics, user management, edit locker books |
| **Host** | Shanmukh | `3677855325` | Full administrative control, system diagnostics, user management, edit locker books |
| **Host** | K. Ramesh | `E2:80:68:10` | Full administrative control, system diagnostics, user management, edit locker books |

*(You can simulate card taps on the login page by entering the RFID UID or ID manually.)*

---

## 🛠️ API Reference

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/rfid` | Authenticate using RFID UID | Public |
| `POST` | `/api/borrow` | Dispense book from designated locker | Authenticated |
| `POST` | `/api/return` | Verify book placement and lock door | Authenticated |
| `POST` | `/api/lockers/<id>/book` | Update book label and author | Host Only |
| `POST` | `/api/users` | Register a new employee | Host Only |
| `POST` | `/api/users/<id>/delete` | Deactivate/remove an employee | Host Only |
| `GET` | `/api/hardware/state` | Poll current locker door and book sensors | Authenticated |

---

## 📄 License
This project is developed for educational and enterprise prototype demonstration purposes.
