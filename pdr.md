# PROJECT DESIGN REPORT (PDR)

Project Title: SmartLocker: IoT-Based Automated Library Book Dispensing and Return System

This Project Design Report is based on your SmartLocker project using a Raspberry Pi, RFID authentication, IR sensors, a magnetic door sensor, an electronic door lock, and a web-based dashboard.

The report describes the system architecture, hardware and software design, database structure, operating logic, circuit connections, and testing approach. It is written in a format suitable for an EEE engineering project.


PROJECT DOCUMENT

# SmartLocker: IoT-Based Automated Library Book Dispensing and Return System

Submitted by

Varri Shanmukha Anand

Department

Electrical and Electronics Engineering (EEE)

Institution

Vishnu Institute of Technology

Academic Year

2026–2027

Project Guide: ____________________

Roll Number: ____________________

# 1. Introduction

SmartLocker is an IoT-based automated library book dispensing and return system designed to simplify book lending and returning. The system uses RFID-based user authentication, sensors to monitor book movement and door status, an electronic locking mechanism, and a web dashboard for transaction management.

The prototype is designed around a single compartment containing one designated book at a time. A member can authenticate using an RFID card, borrow an available book, or return a previously borrowed book. The system records transactions in a database and updates the dashboard according to the verified operation.

The primary objective is to reduce manual intervention, improve transaction traceability, and demonstrate the integration of embedded systems, sensors, database management, and web technologies.

# 2. Problem Statement

Traditional library lending and return procedures often require staff to verify the member, update records, and manage book availability manually. These activities can increase transaction time and introduce recording errors.

The proposed SmartLocker addresses these challenges through:

* RFID-based member authentication.

* Automatic control of a compartment lock.

* Sensor-based monitoring of the compartment and book movement.

* Automatic recording of borrowing and return transactions.

* A web dashboard for monitoring users, book status, and transaction history.

# 3. Objectives

1. Design an automated book dispensing and return prototype.

2. Implement RFID-based authentication for members and staff.

3. Control an electronic lock using a Raspberry Pi.

4. Detect door opening, book presence, and passage-related events using sensors.

5. Develop a web-based interface for book and transaction management.

6. Store member details, loan records, and transaction logs in a database.

7. Prevent incomplete or unauthorized operations from being recorded as successful transactions.

8. Test the prototype under normal and fault conditions.

# 4. Overall System Design

## 4.1 System architecture

RFID Reader

Member / staff authentication

Raspberry Pi 3 Model B/B+

Main controller and decision-making unit

Input sensors

IR sensors, magnetic door sensor

Output devices

Lock driver, solenoid lock, RGB LED

Flask Web Application + SQLite Database

Authentication records, book availability, loans and logs

The Raspberry Pi communicates with the sensors and lock locally. The dashboard and database provide transaction management and monitoring.

## 4.2 Functional blocks

|
Block

|

Function

|
| --- | --- |
|

RFID reader

|

Reads the RFID card presented by the user.

|
|

Raspberry Pi

|

Executes control logic and coordinates all devices.

|
|

IR sensor 1

|

Detects the presence or absence of the designated book at the shelf position.

|
|

IR sensor 2

|

Detects a passage-related event near the compartment opening.

|
|

Magnetic door sensor

|

Indicates whether the compartment door is open or closed.

|
|

Electronic lock

|

Keeps the compartment secured and releases it during an authorized operation.

|
|

RGB LED

|

Indicates standby and active operating states.

|
|

Web dashboard

|

Displays book status, member details, and transaction history.

|
|

SQLite database

|

Stores members, locker status, loans, and transaction logs.

|

# 5. Hardware Design

## 5.1 Raspberry Pi 3 Model B/B+

The Raspberry Pi acts as the main controller. It receives authentication information, reads sensor states, controls the lock driver and indicator, and communicates with the web application and database.

Responsibilities include:

* Processing RFID authentication results.

* Reading sensor inputs.

* Managing the borrowing and return state machine.

* Controlling the lock through a suitable driver circuit.

* Updating the database after successful verification.

* Providing status information to the web dashboard.

The Raspberry Pi's GPIO operates at 3.3 V logic and is not 5 V tolerant. Sensor and driver interfaces must be designed accordingly.

## 5.2 RFID reader

A USB RFID reader compatible with the Raspberry Pi is used for member authentication. Many USB readers operate as keyboard-emulation devices, while others expose a different interface. The software must match the selected reader.

Each authorized card is associated with a member record in the database. The application checks the card identifier and account status before permitting an operation.

Security note: an RFID UID alone is not strong cryptographic authentication. For a real deployment, stronger credentials and appropriate access controls should be considered.

## 5.3 IR sensors

Two FC-51 IR obstacle-detection modules are proposed for the prototype.

* Shelf sensor: Detects whether the designated book is present in the monitored position.

* Entrance sensor: Detects an object or passage event near the compartment opening.

The sensors must be positioned and calibrated to minimize false detections caused by ambient light, object alignment, or reflections.

An IR obstacle sensor detects an object, not its identity. The entrance sensor therefore cannot independently prove that the correct book was removed or returned.

## 5.4 Magnetic door sensor

An MC-38 magnetic contact sensor is used to detect door status. One part is mounted on the compartment frame and the other on the door.

The controller uses the door state to determine whether the compartment has been opened or closed. The software must establish the sensor's actual open/closed electrical logic during installation.

## 5.5 Electronic locking mechanism

A 12 V solenoid lock is proposed for securing the compartment. Since the Raspberry Pi cannot directly power a solenoid, an appropriately rated relay module or transistor/MOSFET driver must be used.

The lock circuit should include:

* A separate power supply rated for the lock.

* A suitable driver rated for the lock's operating current.

* Flyback suppression where required for the inductive load.

* Appropriate fusing and wiring.

* A safe response to power loss and controller restart.

The lock should not be connected directly to a Raspberry Pi GPIO pin.

## 5.6 RGB LED indicator

A common-cathode RGB LED provides a simple visual indication of the system state.

|
LED colour

|

Intended indication

|
| --- | --- |
|

Blue

|

Standby or ready

|
|

Green

|

Authorized operation in progress

|
|

Red, if implemented

|

Error or rejected operation

|

Current-limiting resistors must be used for the LED channels. The selected GPIO drive arrangement should remain within Raspberry Pi electrical limits.

# 6. Software Design

## 6.1 Software platform

|
Software / technology

|

Purpose

|
| --- | --- |
|

Raspberry Pi OS

|

Operating system

|
|

Python 3

|

Main control logic

|
|

Flask

|

Web application and backend routes

|
|

HTML and CSS

|

Dashboard structure and styling

|
|

JavaScript

|

Client-side interaction and status updates

|
|

SQLite

|

Local relational database

|
|

Compatible GPIO library

|

Sensor and output control

|
|

USB RFID interface

|

Card input

|

The application can be developed and tested on a laptop before being deployed on the Raspberry Pi. Hardware-dependent functions should be separated from the web routes to simplify testing.

## 6.2 Software modules

The proposed software is divided into the following modules:

1. Authentication module: Reads the card identifier and verifies the member's status.

2. Book management module: Tracks the designated book's availability.

3. Lock control module: Commands the driver to lock or release the compartment.

4. Sensor monitoring module: Reads IR and door sensor states.

5. Transaction module: Manages borrowing, return, and cancellation.

6. Database module: Performs validated database operations.

7. Dashboard module: Displays current status, member records, and transaction history.

8. Error-handling module: Handles sensor faults, timeouts, rejected cards, and interrupted operations.

# 7. Database Design

SQLite is proposed as the local database because it is suitable for a small prototype and does not require a separate database server.

## 7.1 Members table

|
Field

|

Description

|
| --- | --- |
|

`member_id`

|

Unique member identifier

|
|

`name`

|

Member name

|
|

`rfid_uid`

|

Registered RFID card identifier

|
|

`role`

|

Member or staff

|
|

`status`

|

Active or inactive

|

## 7.2 Lockers table

|
Field

|

Description

|
| --- | --- |
|

`locker_id`

|

Unique compartment identifier

|
|

`book_label`

|

Designated book identifier or label

|
|

`occupancy_status`

|

Present, absent, or unknown

|
|

`door_status`

|

Open, closed, or unknown

|
|

`lock_status`

|

Locked, unlocked, or unknown

|

## 7.3 Loans table

|
Field

|

Description

|
| --- | --- |
|

`loan_id`

|

Unique loan identifier

|
|

`member_id`

|

Member who borrowed the book

|
|

`locker_id`

|

Compartment associated with the loan

|
|

`borrowed_at`

|

Date and time of borrowing

|
|

`returned_at`

|

Date and time of return

|
|

`status`

|

Active, returned, or requiring review

|

## 7.4 Transactions table

|
Field

|

Description

|
| --- | --- |
|

`transaction_id`

|

Unique transaction identifier

|
|

`member_id`

|

Member associated with the operation

|
|

`locker_id`

|

Compartment involved

|
|

`operation`

|

Borrow, return, or cancel

|
|

`result`

|

Success, rejected, cancelled, or error

|
|

`timestamp`

|

Date and time

|
|

`details`

|

Additional diagnostic information

|

The database should use primary keys and appropriate foreign keys. RFID identifiers should be unique, and database updates should be performed transactionally to avoid inconsistent loan records.

# 8. Detailed Operational Design

## 8.1 Borrowing process

Start: user presents RFID card

Verify card and member status

Check book availability and active loans

Authorize operation and release lock

Monitor door, shelf and entrance sensors

Wait for door closure and verify expected final state

Record verified result and update dashboard

The borrowing procedure is as follows:

1. The user presents a registered RFID card.

2. The application verifies that the member is active and eligible to borrow.

3. The application checks that the book is available and that no conflicting active loan exists.

4. The lock is released for the authorized operation.

5. The controller monitors door status and sensor events.

6. Once the door is closed, the controller evaluates the observed sensor states.

7. If the required conditions are satisfied, the loan record is created and the book status is updated.

8. If the operation is incomplete or the sensors disagree, the system records an unresolved or failed transaction instead of falsely marking the book as borrowed.

Design limitation: the prototype's IR sensors cannot prove the identity of a removed book. The system can track the designated book's presence within its controlled compartment, but reliable book identification would require an additional identification mechanism if multiple books were introduced.

## 8.2 Return process

1. The user presents a registered RFID card.

2. The application checks for an active loan associated with the user and book.

3. If the return is valid, the compartment lock is released.

4. The user places the designated book in the compartment.

5. The shelf sensor checks the book's presence, while the entrance and door sensors provide supporting event information.

6. After the door closes, the application verifies the expected final state.

7. If the return is verified, the active loan is marked as returned and the book becomes available.

8. If the expected sensor conditions are not met, the transaction is flagged for review.

## 8.3 Cancellation and timeout handling

If the user cancels or the operation times out:

* Stop accepting further actions for the current transaction.

* Do not create a successful borrowing or return record.

* If the door can safely be closed and the sensor states are consistent, secure the lock.

* If the book's physical state is uncertain, record the issue for staff review.

* Reset the system to standby only when the compartment is in a known, safe state.

# 9. Sensor Logic and State Management

The system should use a state machine rather than responding independently to every sensor change.

|
State

|

Description

|
| --- | --- |
|

`IDLE`

|

System is ready for a new user

|
|

`AUTHENTICATING`

|

RFID credentials are being checked

|
|

`VALIDATING`

|

Book availability and loan conditions are checked

|
|

`UNLOCKED`

|

An authorized access operation is in progress

|
|

`VERIFYING`

|

Sensor readings and door closure are checked

|
|

`COMPLETED`

|

The verified transaction has been recorded

|
|

`CANCELLED`

|

Operation ended without a completed transaction

|
|

`ERROR_REVIEW`

|

The observed physical state is uncertain or inconsistent

|

Sensor values should be debounced or filtered as necessary. The application should also use operation timeouts and reject conflicting transactions while another operation is active.

For example, a borrowing operation should not be marked successful solely because the entrance sensor detects an object. The application must check the expected final shelf state and door state as well.

# 10. Electrical and Interface Design

The following table describes the proposed interfaces. Exact GPIO assignments should be finalized after checking the installed Raspberry Pi software, available pins, and the specific hardware modules.

|
Device

|

Interface

|

Design requirement

|
| --- | --- | --- |
|

USB RFID reader

|

USB

|

Verify that the reader is recognized by the operating system

|
|

Shelf IR sensor

|

GPIO input

|

Confirm output voltage compatibility

|
|

Entrance IR sensor

|

GPIO input

|

Confirm output voltage compatibility

|
|

MC-38 door sensor

|

GPIO input

|

Use suitable pull-up/pull-down configuration

|
|

Lock driver

|

GPIO output to driver input

|

Never drive the lock directly from GPIO

|
|

RGB LED

|

GPIO outputs through resistors

|

Limit current in each channel

|
|

Lock power supply

|

Separate supply

|

Match lock voltage and current requirements

|

### Electrical precautions

* Raspberry Pi GPIO inputs must not receive 5 V signals.

* Check the actual sensor output voltage before connecting it to the Raspberry Pi.

* If an IR sensor is powered at 5 V, use a suitable level-shifting interface unless its output is confirmed to be 3.3 V compatible.

* Use a separate, appropriately rated supply for the solenoid lock.

* Keep power and signal wiring secure and provide a common reference where required by the chosen driver design.

* Test the lock and driver independently before integrating them with the software.

* Determine whether the chosen lock is fail-safe or fail-secure and plan for power loss accordingly.

# 11. Web Dashboard Design

The web dashboard provides the user interface for monitoring and managing the system.

## 11.1 Main dashboard features

* Member authentication status.

* Current book availability.

* Compartment door status.

* Lock status.

* Active loan details.

* Borrow and return controls.

* Transaction history.

* Error and maintenance notifications.

* Staff access for member and book management.

## 11.2 Dashboard behaviour

The dashboard should display the latest confirmed system state. A command to unlock the compartment should not immediately be displayed as proof that the physical lock has successfully changed state.

Where no physical lock feedback is available, the dashboard should distinguish between a command being issued and the actual lock position being verified. Similarly, sensor faults should result in an “Unknown” or “Needs review” status rather than an assumed normal condition.

# 12. Security and Reliability Design

The system should implement the following safeguards:

1. Only registered, active RFID cards may initiate authorized operations.

2. Staff-only functions should require role-based authorization.

3. Borrow and return operations should be protected against duplicate submissions.

4. Database changes should occur only after transaction verification.

5. All completed, rejected, and interrupted operations should be logged.

6. Sensor faults and door timeouts should trigger a safe handling procedure.

7. The application should validate all web requests and restrict unauthorized administrative access.

8. The lock should not remain unlocked indefinitely following a software error.

9. Sensitive configuration information should not be stored in publicly accessible code.

10. The system should be tested for interrupted power, application restart, and database recovery.

# 13. Testing and Validation Plan

|
Test case

|

Procedure

|

Expected result

|
| --- | --- | --- |
|

Valid RFID card

|

Present a registered active card

|

Authentication succeeds

|
|

Invalid RFID card

|

Present an unregistered card

|

Access is denied and logged

|
|

Borrow available book

|

Start a valid borrowing operation

|

Compartment unlocks and the verified loan is recorded

|
|

Borrow unavailable book

|

Attempt to borrow an already-borrowed book

|

Operation is rejected

|
|

Valid return

|

Return a book with an active loan

|

Return is verified and loan is closed

|
|

Invalid return

|

Attempt a return with no matching active loan

|

Operation is rejected or flagged

|
|

Door remains open

|

Leave the door open beyond the timeout

|

Warning is generated and the system follows its safe-state procedure

|
|

Sensor disconnected

|

Disconnect a sensor during testing

|

Fault is detected where possible; transaction is not falsely completed

|
|

Cancellation

|

Cancel an operation before completion

|

No successful loan or return is recorded

|
|

Application restart

|

Restart the software during an operation

|

Previous records remain consistent and the interrupted operation is reviewed

|
|

Lock-driver failure

|

Simulate a failed lock command where safely possible

|

Dashboard does not falsely claim a verified lock state

|
|

Repeated operation

|

Perform multiple borrowing and return cycles

|

Records and availability remain consistent

|

## 13.1 Performance metrics

The following measurements can be used to evaluate the prototype:

* RFID authentication success rate.

* Average time from card presentation to access authorization.

* Successful transaction completion rate.

* Number of false sensor detections.

* Number of incomplete transactions requiring staff review.

* Consistency between physical book presence and database availability.

* Reliability over repeated operating cycles.

The results should be measured during testing rather than assumed in advance.

# 14. Design Limitations

The initial prototype has several limitations:

* It is designed around a single designated book and compartment.

* IR sensors cannot independently identify a book.

* A magnetic door sensor confirms door position but not whether the compartment is physically secure.

* A commanded lock state does not necessarily prove that the lock moved successfully.

* RFID UID authentication alone offers limited protection against card cloning.

* Internet connectivity is not required for the core local prototype, but remote monitoring would need additional networking and security design.

These limitations can be addressed in later versions through book-specific identification, lock-position feedback, stronger authentication, multiple compartments, and improved monitoring.

# 15. Future Enhancements

Potential future improvements include:

* Integration of multiple book compartments.

* Book-level RFID tags or another unique identification method.

* Email or mobile notifications.

* Remote dashboard access with secure authentication.

* Automatic overdue-loan alerts.

* Integration with an existing library management system.

* Battery backup and power-failure recovery.

* Audit reports and usage analytics.

* Additional lock-position or tamper sensors.

* Improved access control for staff and administrators.

# 16. Conclusion

The SmartLocker project proposes an automated approach to library book dispensing and return using a Raspberry Pi, RFID authentication, sensor-based monitoring, electronic locking, a web dashboard, and a local database.

The design combines electrical and electronic hardware with embedded programming and web application development. Its transaction state machine and sensor verification process are intended to reduce inconsistent records and prevent incomplete operations from being marked as successful.

The initial single-compartment prototype provides a foundation for future expansion into a multi-compartment automated library system.

# 17. References

1. Raspberry Pi Documentation — [https://www.raspberrypi.com/documentation/](https://www.raspberrypi.com/documentation/) 

2. Flask Documentation — [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/) 

3. SQLite Documentation — [https://www.sqlite.org/docs.html](https://www.sqlite.org/docs.html) 

4. Python Documentation — [https://docs.python.org/3/](https://docs.python.org/3/) 

Before submission: Add your actual circuit diagram, GPIO pin assignments, photographs of the assembled prototype, software flowchart, and test results. These should reflect the hardware and code you have implemented rather than only the proposed design.
