import os
import re

SCREEN_DIR = os.path.join(os.path.dirname(__file__), 'stitch_screens')
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
os.makedirs(TEMPLATE_DIR, exist_ok=True)

def build_auth_template():
    src_file = os.path.join(SCREEN_DIR, '1969330b2fa04e15a90a18b385f043f0_RFID_Authentication_-_SmartLoc.html')
    with open(src_file, 'r', encoding='utf-8') as f:
        html = f.read()

    cards_html = '''<!-- Card 1: Shanmukha Anand -->
<label class="demo-card-item cursor-pointer block p-space-sm bg-surface-container-low hover:bg-surface-container rounded-lg transition-all" data-id="21BEE1001" data-name="Varri Shanmukha Anand" data-rfid="12:5E:7B:44" data-role="Student" data-status="eligible">
<div class="flex items-start justify-between">
<div class="flex items-center gap-2">
<input checked="" class="text-secondary accent-secondary" name="demo_card" type="radio" value="12:5E:7B:44"/>
<div>
<div class="font-label-lg text-label-lg text-on-surface">Varri Shanmukha Anand</div>
<div class="font-code-badge text-code-badge text-on-surface-variant">Reg: 21BEE1001 • UID: 12:5E:7B:44</div>
</div>
</div>
<span class="font-code-badge text-code-badge px-2 py-0.5 rounded-full bg-tertiary-container/20 text-on-tertiary-container shrink-0">
                    Lead Dev
                  </span>
</div>
</label>
<!-- Card 2: Ananya Sharma -->
<label class="demo-card-item cursor-pointer block p-space-sm bg-surface-container-low hover:bg-surface-container rounded-lg transition-all" data-id="21BEE1048" data-name="Ananya Sharma" data-rfid="04:A2:8F:C9" data-role="Student" data-status="borrowed">
<div class="flex items-start justify-between">
<div class="flex items-center gap-2">
<input class="text-secondary accent-secondary" name="demo_card" type="radio" value="04:A2:8F:C9"/>
<div>
<div class="font-label-lg text-label-lg text-on-surface">Ananya Sharma</div>
<div class="font-code-badge text-code-badge text-on-surface-variant">Reg: 21BEE1048 • UID: 04:A2:8F:C9</div>
</div>
</div>
<span class="font-code-badge text-code-badge px-2 py-0.5 rounded-full bg-surface-variant text-on-surface-variant shrink-0">
                    1 Borrowed
                  </span>
</div>
</label>
<!-- Card 3: Dr. K. Ramesh -->
<label class="demo-card-item cursor-pointer block p-space-sm bg-surface-container-low hover:bg-surface-container rounded-lg transition-all" data-id="VIT-FAC-019" data-name="Dr. K. Ramesh" data-rfid="E2:80:68:10" data-role="Admin / Staff" data-status="faculty">
<div class="flex items-start justify-between">
<div class="flex items-center gap-2">
<input class="text-secondary accent-secondary" name="demo_card" type="radio" value="E2:80:68:10"/>
<div>
<div class="font-label-lg text-label-lg text-on-surface">Dr. K. Ramesh</div>
<div class="font-code-badge text-code-badge text-on-surface-variant">Staff: VIT-FAC-019 • UID: E2:80:68:10</div>
</div>
</div>
<span class="font-code-badge text-code-badge px-2 py-0.5 rounded-full bg-primary-container text-on-primary-container shrink-0">
                    Staff / Guide
                  </span>
</div>
</label>
<!-- Card 4: Unregistered Card -->
<label class="demo-card-item cursor-pointer block p-space-sm bg-surface-container-low hover:bg-surface-container rounded-lg transition-all" data-id="UNKNOWN" data-name="Unregistered Tag" data-rfid="FF:EE:DD:CC" data-role="Visitor" data-status="unregistered">
<div class="flex items-start justify-between">
<div class="flex items-center gap-2">
<input class="text-secondary accent-secondary" name="demo_card" type="radio" value="FF:EE:DD:CC"/>
<div>
<div class="font-label-lg text-label-lg text-error">Unregistered Test Card</div>
<div class="font-code-badge text-code-badge text-on-surface-variant">UID: FF:EE:DD:CC (Rejection Test)</div>
</div>
</div>
<span class="font-code-badge text-code-badge px-2 py-0.5 rounded-full bg-error-container text-on-error-container shrink-0">
                    Not Registered
                  </span>
</div>
</label>'''

    html = re.sub(
        r'<div class="flex flex-col gap-space-sm mb-space-md" id="cardRadioGroup">.*?</div>\s*</div>\s*<!-- Trigger',
        r'<div class="flex flex-col gap-space-sm mb-space-md" id="cardRadioGroup">' + cards_html + r'''</div>
<div class="mt-space-sm p-space-sm bg-surface-container-low rounded-lg flex items-center gap-2">
  <span class="material-symbols-outlined text-secondary">usb</span>
  <input type="text" id="manualRfidInput" placeholder="Scan with USB Reader or type UID..." class="w-full bg-surface-container-lowest px-3 py-1.5 rounded text-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-secondary font-code-telemetry" onkeydown="if(event.key === 'Enter'){ runRfidSimulation(this.value); }" />
  <button onclick="runRfidSimulation(document.getElementById('manualRfidInput').value)" class="bg-secondary text-on-secondary px-3 py-1.5 rounded text-xs font-semibold hover:bg-primary">Scan</button>
</div>
</div>
<!-- Trigger''',
        html,
        flags=re.DOTALL
    )

    js_code = '''<script>
    async function runRfidSimulation(overrideUid) {
      let rfidUid = overrideUid;
      let name = 'Member';
      let regId = '';

      if (!rfidUid) {
        const selectedRadio = document.querySelector('input[name="demo_card"]:checked');
        if (!selectedRadio) return;
        const parentItem = selectedRadio.closest('.demo-card-item');
        rfidUid = parentItem.getAttribute('data-rfid');
        name = parentItem.getAttribute('data-name');
        regId = parentItem.getAttribute('data-id');
      }

      const simulateBtn = document.getElementById('simulateBtn');
      const btnIcon = document.getElementById('btnIcon');
      const btnLabel = document.getElementById('btnLabel');
      const toast = document.getElementById('statusToast');
      const toastContent = document.getElementById('toastContent');
      const toastIcon = document.getElementById('toastIcon');
      const toastTitle = document.getElementById('toastTitle');
      const toastSubtitle = document.getElementById('toastSubtitle');
      const scannerIconHolder = document.getElementById('scannerIconHolder');
      const scannerStatusText = document.getElementById('scannerStatusText');
      const telemetryLog = document.getElementById('telemetryLog');

      simulateBtn.disabled = true;
      simulateBtn.classList.add('opacity-75');
      btnIcon.textContent = 'hourglass_empty';
      btnLabel.textContent = 'Authenticating...';

      scannerIconHolder.className = 'relative z-10 w-20 h-20 rounded-full bg-secondary flex items-center justify-center text-on-secondary shadow-lg transition-transform duration-300 scale-110';
      scannerStatusText.textContent = 'Transmitting UID: ' + rfidUid;

      const timeStr = new Date().toLocaleTimeString('en-GB');
      telemetryLog.innerHTML += `<div class="truncate text-secondary-fixed">> [${timeStr}] INDUCTION: Tag UID ${rfidUid} captured</div>`;
      telemetryLog.scrollTop = telemetryLog.scrollHeight;

      try {
        const res = await fetch('/api/auth/rfid', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ rfid_uid: rfidUid })
        });
        const data = await res.json();

        if (data.success) {
          scannerIconHolder.className = 'relative z-10 w-20 h-20 rounded-full bg-tertiary-container flex items-center justify-center text-tertiary-fixed shadow-lg transition-transform duration-300';
          scannerStatusText.textContent = 'Welcome, ' + data.member.name;

          toastIcon.textContent = 'check_circle';
          toastIcon.className = 'material-symbols-outlined text-on-tertiary-container text-2xl';
          toastTitle.textContent = 'RFID Tag Verified!';
          toastSubtitle.textContent = 'Authenticated ' + data.member.name + '. Redirecting...';
          toastContent.className = 'flex items-center gap-space-sm px-space-md py-space-sm rounded-xl shadow-xl bg-surface-container-lowest text-on-surface border-l-4 border-on-tertiary-container';

          telemetryLog.innerHTML += `<div class="truncate text-tertiary-fixed">> [AUTH] Member ${data.member.name} verified. Session Token issued.</div>`;
          telemetryLog.scrollTop = telemetryLog.scrollHeight;

          toast.classList.remove('opacity-0', 'pointer-events-none', '-translate-y-4');
          toast.classList.add('opacity-100', 'translate-y-0');

          setTimeout(() => {
            window.location.href = data.redirect_url;
          }, 800);
        } else {
          scannerIconHolder.className = 'relative z-10 w-20 h-20 rounded-full bg-error flex items-center justify-center text-on-error shadow-lg transition-transform duration-300';
          scannerStatusText.textContent = 'Access Denied: Unregistered Tag';

          toastIcon.textContent = 'cancel';
          toastIcon.className = 'material-symbols-outlined text-error text-2xl';
          toastTitle.textContent = 'Authentication Failed';
          toastSubtitle.textContent = data.message || 'Card UID not recognized in SQLite registry.';
          toastContent.className = 'flex items-center gap-space-sm px-space-md py-space-sm rounded-xl shadow-xl bg-error-container text-on-error-container';

          telemetryLog.innerHTML += `<div class="truncate text-error">> [FAIL] Registry lookup: ${data.message}</div>`;
          telemetryLog.scrollTop = telemetryLog.scrollHeight;

          toast.classList.remove('opacity-0', 'pointer-events-none', '-translate-y-4');
          toast.classList.add('opacity-100', 'translate-y-0');

          setTimeout(() => {
            toast.classList.remove('opacity-100', 'translate-y-0');
            toast.classList.add('opacity-0', 'pointer-events-none', '-translate-y-4');
            scannerIconHolder.className = 'relative z-10 w-20 h-20 rounded-full bg-primary flex items-center justify-center text-on-primary shadow-lg transition-transform duration-300';
            scannerStatusText.textContent = 'Tap your RFID student card';
            simulateBtn.disabled = false;
            simulateBtn.classList.remove('opacity-75');
            btnIcon.textContent = 'tap_and_play';
            btnLabel.textContent = 'Simulate Tap & Login';
          }, 2500);
        }
      } catch (err) {
        console.error(err);
        simulateBtn.disabled = false;
        btnLabel.textContent = 'Retry Tap & Login';
      }
    }
  </script>'''

    html = re.sub(r'<script>\s*function runRfidSimulation.*?<\/script>', js_code, html, flags=re.DOTALL)

    target = os.path.join(TEMPLATE_DIR, 'auth.html')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Created auth.html')

def build_dashboard_template():
    src_file = os.path.join(SCREEN_DIR, '75af328a10984a7eb220e66a347ecfca_Member_Dashboard_-_SmartLocker.html')
    with open(src_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Fix navigation links in sidebar
    html = html.replace('data-path="dashboard" href="#"', 'href="/dashboard"')
    html = html.replace('data-path="borrow-a-book" href="#"', 'href="/borrow"')
    html = html.replace('data-path="return-a-book" href="#"', 'href="/return"')
    html = html.replace('data-path="account-history" href="#"', 'href="/status"')
    html = html.replace('data-path="system-status" href="#"', 'href="/status"')
    html = html.replace('data-path="user-management" href="#"', 'href="/users"')
    html = html.replace('href="#logout-dialog"', 'href="/logout"')

    # Replace fast-action buttons
    html = re.sub(
        r'<button[^>]*>\s*<span class="material-symbols-outlined text-\[20px\]">book</span>\s*<span>Borrow a Book.*?</span>\s*</button>',
        r'<a href="/borrow" class="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-secondary text-on-secondary hover:bg-secondary-container px-space-lg py-2.5 rounded shadow-sm font-label-md text-label-md transition-all active:scale-[0.98]"><span class="material-symbols-outlined text-[20px]">book</span><span>Borrow a Book</span></a>',
        html
    )
    html = re.sub(
        r'<button[^>]*>\s*<span class="material-symbols-outlined text-\[20px\] text-on-tertiary-container">assignment_return</span>\s*<span class="text-on-surface font-semibold">Return a Book</span>\s*</button>',
        r'<a href="/return" class="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-surface-container-low text-tertiary hover:bg-surface-container px-space-lg py-2.5 rounded shadow-sm font-label-md text-label-md transition-all active:scale-[0.98]"><span class="material-symbols-outlined text-[20px] text-on-tertiary-container">assignment_return</span><span class="text-on-surface font-semibold">Return a Book</span></a>',
        html
    )
    html = re.sub(
        r'<button[^>]*>\s*<span class="material-symbols-outlined text-\[18px\]">terminal</span>\s*<span>Check Sensor Telemetry</span>\s*</button>',
        r'<a href="/status" class="w-full sm:w-auto flex items-center justify-center gap-2 bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container hover:text-on-surface px-space-md py-2.5 rounded font-label-md text-label-md transition-colors"><span class="material-symbols-outlined text-[18px]">terminal</span><span>Check Sensor Telemetry</span></a>',
        html
    )

    # Replace User Identity with Jinja
    html = re.sub(
        r'Welcome back, Ananya Sharma',
        r'Welcome back, {{ current_user.name if current_user else "Library Scholar" }}',
        html
    )
    html = re.sub(
        r'Reg No: <span class="font-code-telemetry text-code-telemetry font-semibold text-on-surface">21BEE1048</span>',
        r'Reg No: <span class="font-code-telemetry text-code-telemetry font-semibold text-on-surface">{{ current_user.reg_no if current_user else "21BEE1001" }}</span>',
        html
    )
    html = re.sub(
        r'04:A2:8F:C9',
        r'{{ current_user.rfid_uid if current_user else "12:5E:7B:44" }}',
        html
    )

    # Dynamic metrics
    html = re.sub(
        r'<span class="font-headline-xl text-headline-xl text-primary font-bold mt-1">18</span>',
        r'<span class="font-headline-xl text-headline-xl text-primary font-bold mt-1">{{ available_lockers|length }}</span>',
        html
    )
    html = re.sub(
        r'<span class="font-headline-xl text-headline-xl text-primary font-bold mt-1">1</span>',
        r'<span class="font-headline-xl text-headline-xl text-primary font-bold mt-1">{{ active_loans|length }}</span>',
        html
    )
    html = re.sub(
        r'<span class="font-headline-xl text-headline-xl text-on-error-container font-bold mt-1">3 Days</span>',
        r'<span class="font-headline-xl text-headline-xl text-on-error-container font-bold mt-1">{{ due_in_days }} Days</span>',
        html
    )

    # Render dynamic Active Loans table if loans exist
    loans_tbody = '''<tbody class="divide-y-0">
    {% for loan in active_loans %}
    <tr class="hover:bg-surface-container-low transition-colors">
      <td class="py-space-md px-space-md">
        <div class="flex items-center gap-space-sm">
          <div class="w-12 h-16 rounded bg-primary-container flex items-center justify-center text-on-primary-container font-bold text-xs flex-shrink-0">
            {{ loan.locker_code }}
          </div>
          <div class="flex flex-col min-w-0">
            <span class="font-label-lg text-label-lg text-primary truncate">{{ loan.book_label }}</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant">{{ loan.book_author }}</span>
            <span class="font-code-badge text-code-badge text-outline">{{ loan.category }}</span>
          </div>
        </div>
      </td>
      <td class="py-space-md px-space-md">
        <span class="font-code-telemetry text-code-telemetry text-primary font-bold bg-surface-container px-2 py-1 rounded">{{ loan.locker_code }}</span>
      </td>
      <td class="py-space-md px-space-md">
        <div class="flex flex-col">
          <span class="font-body-sm text-body-sm text-on-surface font-medium">{{ loan.borrowed_at[:10] }}</span>
          <span class="font-code-badge text-code-badge text-outline">{{ loan.borrowed_at[11:16] }}</span>
        </div>
      </td>
      <td class="py-space-md px-space-md">
        <div class="flex flex-col">
          <span class="font-label-md text-label-md text-on-error-container font-semibold">{{ loan.due_date[:10] }}</span>
          <span class="font-code-badge text-code-badge text-error">{{ due_in_days }} days left</span>
        </div>
      </td>
      <td class="py-space-md px-space-md">
        <span class="inline-flex items-center gap-1 font-code-badge text-code-badge text-tertiary-container bg-tertiary-fixed px-2 py-0.5 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-on-tertiary-container"></span> Active Loan
        </span>
      </td>
      <td class="py-space-md px-space-md text-right">
        <a href="/return" class="bg-primary text-on-primary hover:bg-primary-container px-3 py-1.5 rounded font-label-md text-label-md shadow-sm transition-all whitespace-nowrap inline-block">
          Return to Locker
        </a>
      </td>
    </tr>
    {% else %}
    <tr>
      <td colspan="6" class="py-space-lg text-center text-on-surface-variant">
        No active book loans. You can borrow an available book below!
      </td>
    </tr>
    {% endfor %}
    </tbody>'''

    html = re.sub(r'<tbody class="divide-y-0">.*?</tbody>', loans_tbody, html, flags=re.DOTALL)

    target = os.path.join(TEMPLATE_DIR, 'dashboard.html')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Created dashboard.html')

def build_borrow_template():
    src_file = os.path.join(SCREEN_DIR, '74696f4c836e4631bf9ab1794a8d0631_Borrow_a_Book_-_SmartLocker.html')
    with open(src_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Fix navigation
    html = html.replace('href="#"', 'href="/dashboard"')
    html = html.replace('data-path="dashboard"', 'href="/dashboard"')
    html = html.replace('data-path="borrow-a-book"', 'href="/borrow"')
    html = html.replace('data-path="return-a-book"', 'href="/return"')
    html = html.replace('data-path="account-history"', 'href="/status"')
    html = html.replace('data-path="system-status"', 'href="/status"')
    html = html.replace('data-path="user-management"', 'href="/users"')
    html = html.replace('href="#logout-dialog"', 'href="/logout"')

    # Wire the real unlock and verify logic to Flask endpoints
    interactive_js = '''<script>
    let currentStep = 1;
    let selectedLockerId = 4; // BAY-04 designated

    async function handleUnlockTrigger() {
      const unlockBtn = document.getElementById('unlock-btn');
      const unlockBtnLabel = document.getElementById('unlock-btn-label');
      const unlockBtnIcon = document.getElementById('unlock-btn-icon');
      
      unlockBtn.disabled = true;
      unlockBtnLabel.textContent = 'Releasing 12V Solenoid...';
      unlockBtnIcon.textContent = 'hourglass_empty';

      try {
        const res = await fetch('/api/locker/borrow', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ locker_id: selectedLockerId, step: 'initiate' })
        });
        const data = await res.json();

        if (data.success) {
          // Update UI: Step 3 Active (Solenoid Unlocked)
          document.getElementById('sensor-solenoid-led').className = 'w-3 h-3 rounded-full bg-secondary shadow-sm flex-shrink-0 animate-pulse';
          document.getElementById('sensor-solenoid-text').textContent = 'UNLOCKED (Energized)';
          
          unlockBtnLabel.textContent = 'Locker Unlocked! Open Door & Take Book';
          unlockBtnIcon.textContent = 'lock_open';
          unlockBtn.className = 'w-full sm:flex-1 flex items-center justify-center gap-space-sm px-space-lg py-3.5 bg-tertiary text-white font-label-lg rounded-lg shadow-sm';

          // Show interactive step actions
          document.getElementById('sim-step-controls').classList.remove('hidden');
        } else {
          alert(data.message || 'Error unlocking locker');
          unlockBtn.disabled = false;
          unlockBtnLabel.textContent = 'Retry Unlock';
        }
      } catch (err) {
        console.error(err);
        alert('Server communication error');
        unlockBtn.disabled = false;
      }
    }

    async function simulateStep(action) {
      const res = await fetch('/api/locker/simulate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: action })
      });
      const data = await res.json();
      
      if (action === 'open_door') {
        document.getElementById('sensor-door-led').className = 'w-3 h-3 rounded-full bg-error animate-pulse';
        document.getElementById('sensor-door-text').textContent = 'OPEN (Reed Low)';
        document.getElementById('btn-open-door').classList.add('opacity-50');
        document.getElementById('btn-take-book').classList.remove('opacity-50');
      } else if (action === 'take_book') {
        document.getElementById('sensor-ir-led').className = 'w-3 h-3 rounded-full bg-surface-dim';
        document.getElementById('sensor-ir-text').textContent = 'ABSENT (Beam Free)';
        document.getElementById('btn-take-book').classList.add('opacity-50');
        document.getElementById('btn-close-door').classList.remove('opacity-50');
      } else if (action === 'close_door') {
        document.getElementById('sensor-door-led').className = 'w-3 h-3 rounded-full bg-secondary';
        document.getElementById('sensor-door-text').textContent = 'Securely Closed';
        document.getElementById('btn-close-door').classList.add('opacity-50');
        document.getElementById('btn-verify-borrow').classList.remove('hidden');
      }
    }

    async function verifyAndFinalizeBorrow() {
      const btn = document.getElementById('btn-verify-borrow');
      btn.textContent = 'Verifying Transaction...';
      btn.disabled = true;

      const res = await fetch('/api/locker/borrow', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ locker_id: selectedLockerId, step: 'verify' })
      });
      const data = await res.json();

      if (data.success) {
        alert('Book Dispensed Successfully! Transaction recorded in SQLite.');
        window.location.href = '/dashboard';
      } else {
        alert(data.message || 'Verification failed');
        btn.disabled = false;
      }
    }
  </script>'''

    # Add simulation control box into borrow template
    sim_box = '''<!-- Interactive Hardware Simulation Box for Dispensing Demo -->
<div id="sim-step-controls" class="hidden mt-space-md p-space-md bg-surface-container-high rounded-xl border border-secondary/20 flex flex-col gap-space-sm">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <span class="material-symbols-outlined text-secondary">precision_manufacturing</span>
      <span class="font-label-lg text-label-lg text-primary font-bold">Physical Locker Sensor Interactions</span>
    </div>
    <span class="font-code-badge text-code-badge bg-secondary text-on-secondary px-2 py-0.5 rounded">SIMULATOR ACTIVE</span>
  </div>
  <p class="font-body-sm text-body-sm text-on-surface-variant">Step through the physical actions to complete the IoT dispensing sequence:</p>
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
    <button id="btn-open-door" onclick="simulateStep('open_door')" class="bg-surface-container-lowest hover:bg-surface-container p-2.5 rounded font-label-md text-xs text-primary shadow-sm flex items-center justify-center gap-1 border">
      <span class="material-symbols-outlined text-sm">meeting_room</span> 1. Pull Door Open
    </button>
    <button id="btn-take-book" onclick="simulateStep('take_book')" class="opacity-50 bg-surface-container-lowest hover:bg-surface-container p-2.5 rounded font-label-md text-xs text-primary shadow-sm flex items-center justify-center gap-1 border">
      <span class="material-symbols-outlined text-sm">front_hand</span> 2. Take Book from Shelf
    </button>
    <button id="btn-close-door" onclick="simulateStep('close_door')" class="opacity-50 bg-surface-container-lowest hover:bg-surface-container p-2.5 rounded font-label-md text-xs text-primary shadow-sm flex items-center justify-center gap-1 border">
      <span class="material-symbols-outlined text-sm">door_sliding</span> 3. Push Door Closed
    </button>
  </div>
  <button id="btn-verify-borrow" onclick="verifyAndFinalizeBorrow()" class="hidden mt-2 bg-on-tertiary-container text-white py-3 rounded-lg font-label-lg text-sm font-bold shadow-md hover:bg-tertiary flex items-center justify-center gap-2">
    <span class="material-symbols-outlined">check_circle</span> Complete Transaction & Lock Solenoid
  </button>
</div>'''

    html = html.replace('<!-- Action Control Center -->', sim_box + '\n<!-- Action Control Center -->')
    html = re.sub(r'<script>.*?</script>', interactive_js, html, flags=re.DOTALL)

    target = os.path.join(TEMPLATE_DIR, 'borrow.html')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Created borrow.html')

def build_return_template():
    src_file = os.path.join(SCREEN_DIR, '76f8f94c2c794ef4817c9174186e4d73_Return_a_Book_-_SmartLocker.html')
    with open(src_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Fix navigation
    html = html.replace('href="#"', 'href="/dashboard"')
    html = html.replace('data-path="dashboard"', 'href="/dashboard"')
    html = html.replace('data-path="borrow-a-book"', 'href="/borrow"')
    html = html.replace('data-path="return-a-book"', 'href="/return"')
    html = html.replace('data-path="account-history"', 'href="/status"')
    html = html.replace('data-path="system-status"', 'href="/status"')
    html = html.replace('data-path="user-management"', 'href="/users"')
    html = html.replace('href="#logout-dialog"', 'href="/logout"')

    return_js = '''<script>
    let activeLoanId = {% if active_loans %}{{ active_loans[0].loan_id }}{% else %}1{% endif %};

    async function handleReturnUnlock() {
      const btn = document.getElementById('return-unlock-btn');
      btn.disabled = true;
      btn.textContent = 'Unlocking Designated Bay...';

      try {
        const res = await fetch('/api/locker/return', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ loan_id: activeLoanId, step: 'initiate' })
        });
        const data = await res.json();
        if (data.success) {
          btn.textContent = 'Bay Unlocked! Place Book & Close Door';
          document.getElementById('return-sim-controls').classList.remove('hidden');
        } else {
          alert(data.message || 'Error initiating return');
          btn.disabled = false;
        }
      } catch (err) {
        console.error(err);
        btn.disabled = false;
      }
    }

    async function simulateReturnStep(action) {
      await fetch('/api/locker/simulate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: action })
      });
      if (action === 'open_door') {
        document.getElementById('btn-r-door').classList.add('opacity-50');
        document.getElementById('btn-r-place').classList.remove('opacity-50');
      } else if (action === 'place_book') {
        document.getElementById('btn-r-place').classList.add('opacity-50');
        document.getElementById('btn-r-close').classList.remove('opacity-50');
      } else if (action === 'close_door') {
        document.getElementById('btn-r-close').classList.add('opacity-50');
        document.getElementById('btn-r-finalize').classList.remove('hidden');
      }
    }

    async function finalizeReturn() {
      const btn = document.getElementById('btn-r-finalize');
      btn.disabled = true;
      btn.textContent = 'Verifying Return Sensors...';

      const res = await fetch('/api/locker/return', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ loan_id: activeLoanId, step: 'verify' })
      });
      const data = await res.json();
      if (data.success) {
        alert('Book Return Verified! Thank you for using SmartLocker.');
        window.location.href = '/dashboard';
      } else {
        alert(data.message || 'Verification error');
        btn.disabled = false;
      }
    }
  </script>'''

    sim_box_return = '''<!-- Interactive Simulation Controls for Book Return -->
<div id="return-sim-controls" class="hidden mt-space-md p-space-md bg-surface-container-high rounded-xl border border-secondary/20 flex flex-col gap-space-sm">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <span class="material-symbols-outlined text-secondary">fact_check</span>
      <span class="font-label-lg text-label-lg text-primary font-bold">Physical Return Sensor Steps</span>
    </div>
    <span class="font-code-badge text-code-badge bg-secondary text-on-secondary px-2 py-0.5 rounded">SIMULATOR ACTIVE</span>
  </div>
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
    <button id="btn-r-door" onclick="simulateReturnStep('open_door')" class="bg-surface-container-lowest p-2.5 rounded font-label-md text-xs text-primary shadow-sm flex items-center justify-center gap-1 border">
      <span class="material-symbols-outlined text-sm">meeting_room</span> 1. Open Locker Door
    </button>
    <button id="btn-r-place" onclick="simulateReturnStep('place_book')" class="opacity-50 bg-surface-container-lowest p-2.5 rounded font-label-md text-xs text-primary shadow-sm flex items-center justify-center gap-1 border">
      <span class="material-symbols-outlined text-sm">menu_book</span> 2. Place Book on IR Shelf
    </button>
    <button id="btn-r-close" onclick="simulateReturnStep('close_door')" class="opacity-50 bg-surface-container-lowest p-2.5 rounded font-label-md text-xs text-primary shadow-sm flex items-center justify-center gap-1 border">
      <span class="material-symbols-outlined text-sm">door_sliding</span> 3. Close Door Securely
    </button>
  </div>
  <button id="btn-r-finalize" onclick="finalizeReturn()" class="hidden mt-2 bg-on-tertiary-container text-white py-3 rounded-lg font-label-lg text-sm font-bold shadow-md hover:bg-tertiary flex items-center justify-center gap-2">
    <span class="material-symbols-outlined">verified</span> Complete Return Verification & Lock
  </button>
</div>'''

    html = re.sub(r'<button class="w-full sm:flex-1.*?>.*?<span>Unlock Locker.*?</span>\s*</button>', 
                  r'<button id="return-unlock-btn" onclick="handleReturnUnlock()" class="w-full sm:flex-1 flex items-center justify-center gap-space-sm px-space-lg py-3.5 bg-secondary hover:bg-primary text-on-secondary font-label-lg text-label-lg rounded-lg shadow-sm transition-all"><span class="material-symbols-outlined text-[20px]">lock_open</span><span>Unlock Locker for Return</span></button>', html)
    html = html.replace('<!-- Action Buttons Strip -->', sim_box_return + '\n<!-- Action Buttons Strip -->')
    html = re.sub(r'<script>.*?</script>', return_js, html, flags=re.DOTALL)

    target = os.path.join(TEMPLATE_DIR, 'return.html')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Created return.html')

def build_status_template():
    src_file = os.path.join(SCREEN_DIR, 'c01cc890c8a6421e84333aa7a74d7c00_System_Status_-_SmartLocker.html')
    with open(src_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Fix navigation
    html = html.replace('data-path="dashboard" href="#"', 'href="/dashboard"')
    html = html.replace('data-path="borrow-a-book" href="#"', 'href="/borrow"')
    html = html.replace('data-path="return-a-book" href="#"', 'href="/return"')
    html = html.replace('data-path="account-history" href="#"', 'href="/status"')
    html = html.replace('data-path="system-status" href="#"', 'href="/status"')
    html = html.replace('data-path="user-management" href="#"', 'href="/users"')
    html = html.replace('href="#logout-dialog"', 'href="/logout"')

    # Inject real system stats
    html = re.sub(r'<span>44\.2°C</span>', r'<span>42.5°C</span>', html)
    html = re.sub(r'<span>14\.2%</span>', r'<span>{{ sys_info.cpu_usage }}%</span>', html)
    html = re.sub(r'<span>512 MB / 1024 MB</span>', r'<span>{{ sys_info.mem_usage }}</span>', html)

    target = os.path.join(TEMPLATE_DIR, 'status.html')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Created status.html')

def build_users_template():
    src_file = os.path.join(SCREEN_DIR, 'c74a221945b2418c874abbf3f400311b_User_Management_-_SmartLocker.html')
    with open(src_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Fix navigation
    html = html.replace('data-path="dashboard" href="#"', 'href="/dashboard"')
    html = html.replace('data-path="borrow-a-book" href="#"', 'href="/borrow"')
    html = html.replace('data-path="return-a-book" href="#"', 'href="/return"')
    html = html.replace('data-path="account-history" href="#"', 'href="/status"')
    html = html.replace('data-path="system-status" href="#"', 'href="/status"')
    html = html.replace('data-path="user-management" href="#"', 'href="/users"')
    html = html.replace('href="#logout-dialog"', 'href="/logout"')

    target = os.path.join(TEMPLATE_DIR, 'users.html')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Created users.html')

if __name__ == '__main__':
    build_auth_template()
    build_dashboard_template()
    build_borrow_template()
    build_return_template()
    build_status_template()
    build_users_template()
    print('All templates built successfully!')
