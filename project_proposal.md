# PROJECT PROPOSAL

## SmartLocker: IoT-Based Automated Library Book Dispensing and Return System

![SMART Locker](https://images.openai.com/static-rsc-4/1QhLsNDbSyDFSc0EFN6tG5U3wIYMIvwrGvy3XA7K05XQExkqCKwMH8vEJlkFGCPniAERdoKZLAXoAApIAm8g7aUWJCRkhMFO6Ls4EEFr9ngEERiQpnV6to7yDqFd6OWUOfWZF2mmdDAiRYaawtmup9fdkFNprKKIisjEO8Gc2EQ?purpose=inline)

PROJECT CATEGORY

## Internet of Things (IoT), Embedded Systems and Web Development

CONTROLLER

Raspberry Pi 3 Model B/B+

INTERFACE

Web-based dashboard

AUTHENTICATION

USB RFID reader

PROTOTYPE CAPACITY

One book per locker

## 1. Abstract

SmartLocker is an Internet of Things (IoT)-based automated library book dispensing and return system designed to simplify the process of borrowing and returning books while reducing the need for continuous library staff involvement. The proposed system integrates a Raspberry Pi 3, a USB RFID reader, an electronically controlled solenoid door lock, a magnetic door sensor, two infrared (IR) sensors, an RGB LED, a database, and a web-based dashboard.

Library members authenticate themselves using their registered RFID cards. After successful authentication, the system displays their account details and borrowing history. Members can request to borrow an available book or return a previously borrowed book through the dashboard. The Raspberry Pi coordinates the locker hardware and software, while the sensors monitor door status, book presence, and passage through the locker entrance.

A key feature of SmartLocker is its account-based book tracking approach, which aims to eliminate the need for individual barcodes or RFID tags on books within the prototype's controlled, single-book compartment. Book availability is determined using physical occupancy sensing and transaction records associated with authenticated users.

During a borrowing or return transaction, the solenoid lock is released for an authorized operation. The system checks the door and sensor states before completing the transaction, updating the database, and restoring the locker to its standby condition. A blue LED indicates standby, while a green LED indicates an active locker operation.

The proposed system aims to provide a convenient, secure, and cost-conscious solution for self-service library access, with potential applications in educational institutions, departmental libraries, reading rooms, and other controlled book-lending environments.

## 2. Introduction

Libraries are essential facilities in educational institutions, providing students and staff with access to books and learning resources. Traditional library operations often require users to interact with library personnel for borrowing and returning books. During busy periods, this can result in queues, increased administrative work, and restricted access outside regular working hours.

Automation can reduce repetitive tasks by integrating electronic identification, physical access control, sensors, databases, and web applications. IoT technology makes it possible to monitor physical devices and coordinate their operation with software systems.

SmartLocker proposes a compact, automated book locker that allows an authorized user to collect or return a designated book through a web dashboard. The system combines user authentication and account-based transaction management with physical verification of the locker.

The initial prototype will contain one compartment capable of holding one book at a time. This approach allows the core borrowing and return process to be developed and tested before expanding the design to multiple lockers.

## 3. Problem Statement

Conventional library borrowing and return processes may involve manual verification, staff-assisted transactions, barcode scanning, or RFID tagging of individual books. These processes can require additional equipment, labeling, maintenance, and human intervention.

The proposed project addresses the following problems:

* Dependence on library staff for routine borrowing and return operations.

* Limited availability of self-service facilities outside normal working hours.

* The need to associate every transaction with the correct member account.

* The possibility of incorrect transaction records when physical book movement is not verified.

* Additional cost and maintenance associated with individual book identification tags in systems that use them.

* Limited visibility of locker availability and transaction status in conventional manual arrangements.

Proposed solution: Develop an IoT-enabled locker that authenticates members, controls physical access, verifies book occupancy and door closure, and updates borrowing records through a web-based interface.

A design limitation must be recognized: because the prototype does not identify books individually, it can track a single designated book through the controlled compartment, but it cannot independently determine the identity of an arbitrary book placed inside it.


## 4. Aim and Objectives

### 4.1 Aim

To design and develop an IoT-based automated library locker that enables authorized members to borrow and return a designated book through a web dashboard, using sensor-based verification and digital transaction records.

### 4.2 Specific objectives

1. To develop a web-based dashboard for member authentication, book availability, borrowing, returning, and transaction history.

2. To integrate a USB RFID reader for identifying registered library members and staff.

3. To use a Raspberry Pi 3 as the central controller for the web application, database, sensors, and lock mechanism.

4. To implement electronic door locking using a 12 V solenoid lock controlled through a suitable relay or driver circuit.

5. To monitor door status using an MC-38 magnetic reed switch.

6. To detect book occupancy and passage through the locker entrance using two FC-51 IR sensors.

7. To update the book's availability and the member's loan record only after the configured transaction conditions are satisfied.

8. To provide visual guidance through a common-cathode RGB LED.

9. To implement safe cancellation and timeout handling so that incomplete operations do not create false borrowing or return records.

10. To evaluate the reliability, response time, and accuracy of the prototype under normal and abnormal operating conditions.

## 5. Proposed System Architecture

![electronics - RPi.GPIO + single channel relay + solenoid lock - Raspberry Pi Stack Exchange](https://images.openai.com/static-rsc-4/TxhmYQ6CCcZA_KR5p3eh8eVL9sAVAfWIBw_Zf7CVzVdblK0JG-ko5WsMzv8P7RKA2PjMyOCvHWAICUT36LNz0Sr0Ynu9rknVUIJvoxVJpSwJ1TVHf7dPm9M6uoO3Bm-5mf6brAHIycbc_i2Gt1qG9tu5tHtxTaJKYhr9SoS6Kdw?purpose=inline)

The system consists of five interconnected layers.

Layer 1 — User Interface

Laptop web dashboard · Borrow/Return · Account history

Layer 2 — Application and Database

Python Flask backend · Member authentication · Loan records · Transaction validation

Layer 3 — Central Controller

Raspberry Pi 3 · GPIO control · Hardware state monitoring

Inputs

USB RFID reader, MC-38 door sensor, IR sensors 1 and 2

Outputs

12 V solenoid lock, relay/driver, RGB LED

Conceptual architecture — hardware and software communicate through the Raspberry Pi.

### 5.1 Hardware layer

The hardware layer contains the Raspberry Pi, RFID reader, door lock, door sensor, IR sensors, LED, and required power and driver circuits. These components provide user identification, physical access control, and feedback about the locker's condition.

### 5.2 Application layer

A Python-based web application will process user requests, validate permissions, manage borrowing and return operations, and coordinate hardware actions. Flask is proposed as the web framework.

### 5.3 Database layer

A lightweight database such as SQLite will store member details, RFID identifiers, book and locker status, loan records, timestamps, and transaction outcomes.

### 5.4 Dashboard layer

The dashboard will provide a clean, responsive interface accessible through a laptop browser connected to the Raspberry Pi's network. It will display the authenticated user's details, current loans, book availability, and transaction feedback.

### 5.5 Sensor and control layer

The Raspberry Pi will read the sensor inputs and control the LED and lock mechanism. A transaction will be completed only when the configured physical conditions and database rules have been satisfied.

## 6. Hardware Requirements

|
S. No.

|

Component

|

Quantity

|

Purpose

|
| --- | --- | --- | --- |
|

1

|

Raspberry Pi 3 Model B/B+

|

1

|

Main controller and application host

|
|

2

|

USB RFID reader

|

1

|

Member and staff identification

|
|

3

|

Compatible RFID cards

|

As required

|

User authentication

|
|

4

|

12 V solenoid door lock

|

1

|

Electronic locker locking

|
|

5

|

Suitable relay/driver module

|

1

|

Lock switching and isolation

|
|

6

|

MC-38 magnetic door sensor

|

1

|

Door open/closed detection

|
|

7

|

FC-51 IR sensor

|

2

|

Book occupancy and passage sensing

|
|

8

|

Common-cathode RGB LED

|

1

|

Status indication

|
|

9

|

Current-limiting resistors

|

As required

|

LED and signal protection

|
|

10

|

Regulated 5 V power supply

|

1

|

Raspberry Pi power

|
|

11

|

Suitable 12 V power supply

|

1

|

Solenoid lock power

|
|

12

|

Locker enclosure and door

|

1

|

Physical storage compartment

|
|

13

|

Jumper wires, connectors and mounting hardware

|

As required

|

Electrical interconnections

|

The final bill of materials will depend on the exact Raspberry Pi revision, lock current rating, relay module, enclosure, and power supply selected.

### Important electrical design considerations

* The Raspberry Pi GPIO operates at 3.3 V and is not 5 V tolerant. Sensor outputs must be verified as safe for the GPIO inputs.

* The solenoid lock must not be powered directly from a Raspberry Pi GPIO pin. Use a suitably rated switching circuit and a separate lock supply.

* Inductive loads require appropriate transient suppression, selected for the actual driver and lock configuration.

* The LED must have suitable current-limiting resistors. GPIO current limits must be observed.

* The sensor outputs must be tested to determine whether each module is active-high or active-low.

* The lock's default mechanical and electrical state must be considered during power failure and restart.

## 7. Software Requirements

|
Software/tool

|

Proposed purpose

|
| --- | --- |
|

Raspberry Pi OS

|

Operating system for the controller

|
|

Python 3

|

Main application programming language

|
|

Flask

|

Web server and backend routes

|
|

HTML5

|

Dashboard structure

|
|

CSS3

|

Layout, styling, and responsive design

|
|

JavaScript

|

Dynamic dashboard updates and interactions

|
|

SQLite

|

Local database for members and loans

|
|

GPIO library compatible with Raspberry Pi OS

|

Sensor inputs, LED, and lock control

|
|

USB HID or compatible reader interface

|

Reading RFID card identifiers

|
|

Web browser

|

Accessing the dashboard from the laptop

|
|

Git (optional)

|

Version control and backup of source code

|

The exact GPIO library and RFID integration method will be selected after verifying the operating system and the reader's communication interface.

## 8. Working Methodology

The project will be implemented in stages, beginning with the software and then integrating the physical hardware.

1. Requirement analysis and system design

   Define the borrowing rules, return rules, user roles, sensor positions, database structure, and lock operating sequence.

2. Web application development

   Develop the Flask application, member login flow, dashboard, borrowing and return screens, and error messages.

3. Database implementation

   Create tables for members, locker inventory, active loans, and transaction history. Enforce borrowing limits and prevent duplicate transactions.

4. RFID integration

   Register test cards, associate card identifiers with user accounts, and verify authorized and unauthorized access.

5. Hardware integration

   Connect the door sensor, two IR sensors, RGB LED, and solenoid lock using appropriate interfaces and power supplies.

6. Transaction state-machine development

   Implement explicit states such as standby, authorized, unlocking, door open, verification, locking, success, and error.

7. System testing and validation

   Test normal borrowing and return cycles, cancellation, missing books, incorrect sensor readings, timeouts, and application restarts.

8. Final evaluation and documentation

   Record measured performance, document limitations, and prepare the final report and demonstration.


## 9. Detailed Working Principle

### 9.1 Standby and initialization

When the Raspberry Pi starts, the application initializes the GPIO interfaces, database connection, RFID reader, and sensor monitoring. The software checks whether the locker is in a safe state before enabling transactions.

* The door should be closed and the lock secured.

* The blue LED indicates standby.

* The dashboard displays the RFID authentication screen.

* If a sensor or hardware initialization check fails, the application should display an error and prevent unsafe transactions.

### 9.2 Member authentication

1. The member scans a registered RFID card using the USB reader.

2. The application obtains the card identifier.

3. The backend checks whether the identifier is associated with an active member account.

4. If authentication succeeds, the dashboard displays the member's name, role, and current loan details.

5. If authentication fails, the dashboard displays an error and the lock remains secured.

For additional protection, staff functions should require staff authorization rather than relying solely on the member's ability to enter an RFID UID manually.

### 9.3 Book borrowing process

Step 1: Validate the request

Verify the member's identity, borrowing eligibility, existing loans, and current book availability.

Step 2: Unlock the locker

Turn the LED green and activate the lock driver for the configured unlock period.

Step 3: Detect book removal

Monitor the entrance IR sensor, shelf occupancy sensor, and door sensor for the expected sequence of events.

Step 4: Verify closure and secure the locker

After the door closes, command the lock to secure the compartment and verify the available feedback.

Step 5: Complete the transaction

When the configured conditions are satisfied, create the loan record, mark the compartment empty, update the dashboard, and return the LED to blue.

If the expected sensor sequence is not observed, the application should not automatically assume that borrowing succeeded. It should enter a controlled error or recovery state, retain the diagnostic information, and require appropriate verification.

### 9.4 Book return process

1. The member scans their RFID card.

2. The dashboard retrieves the active loan associated with that account.

3. The member selects Return to Locker 1.

4. The backend verifies that the member has a book eligible for return and that the locker is available.

5. The lock releases, the LED changes to green, and the user places the book inside.

6. The shelf IR sensor indicates occupancy; the entrance IR sensor can provide supporting evidence of an object crossing the entrance.

7. The door sensor confirms closure.

8. After the required conditions are satisfied, the lock is secured and the loan is marked returned.

9. The dashboard updates the member's account and makes the borrowing option available again, provided the inventory is confirmed as available.

### 9.5 Exit and cancellation

The dashboard will provide an Exit/Cancel option during an active session. Cancelling should stop the current operation safely, secure the locker when possible, and return the interface to standby.

Database rule: Cancellation must not create a completed loan or return transaction. If a physical book movement has already occurred, the system must record or flag the unresolved state for recovery instead of simply discarding the event.

### 9.6 Sensor logic

|
Sensor

|

Expected function

|

Interpretation

|
| --- | --- | --- |
|

Shelf IR sensor

|

Detect the book resting on the shelf

|

Occupied or empty

|
|

Entrance IR sensor

|

Detect a crossing event

|

Supporting evidence of removal or placement

|
|

MC-38 sensor

|

Detect door position

|

Open or closed

|

The entrance sensor detects an interruption in its optical field, not the identity of an object. A hand, book, or another object could trigger it. Likewise, FC-51 sensors can be affected by placement, surface reflectivity, ambient light, and alignment.

For this reason, sensor readings should be interpreted as a sequence of events, with suitable debounce, timeout, and consistency checks. The three sensors improve transaction verification, but they cannot guarantee theft prevention or prove book identity.

## 10. Proposed Database Design

The application will use SQLite for the initial prototype. A relational schema is proposed below.

|
Table

|

Main fields

|

Purpose

|
| --- | --- | --- |
|

`members`

|

`member_id`, `name`, `rfid_uid`, `role`, `status`

|

Stores registered members and staff

|
|

`lockers`

|

`locker_id`, `book_label`, `occupancy_status`, `door_status`, `lock_status`

|

Stores compartment information

|
|

`loans`

|

`loan_id`, `member_id`, `locker_id`, `borrowed_at`, `returned_at`, `status`

|

Stores active and completed loans

|
|

`transactions`

|

`transaction_id`, `member_id`, `locker_id`, `operation`, `result`, `timestamp`, `details`

|

Maintains an audit trail

|

### Database rules

* An RFID identifier should be unique to one registered account.

* A member cannot borrow a book already recorded as borrowed.

* Only one active loan can exist for the single designated book.

* A return must refer to a valid active loan.

* Loan status must change only after the configured physical verification succeeds.

* Database updates related to a transaction should be atomic wherever possible.

* Incomplete operations and sensor failures should be recorded for troubleshooting.

* The application should recover safely after a restart and reconcile stored records with the physical sensor state.

The proposed database can track which member borrowed the designated book. It cannot independently determine whether the book physically present is the same book previously borrowed without some additional identification or controlled handling procedure.

## 11. Web Dashboard Design

## SmartLocker

Automated Library Kiosk

System Online

MEMBER DASHBOARD · CONCEPTUAL LAYOUT

Locker inventory

# 1 book

Single-compartment prototype

Current account

# My loans

Active and completed records

Locker 1

Designated book · Availability from sensor state

Live status

Member authentication

Scan your registered RFID card

Borrow

Return

Buttons are illustrative; actual availability and authentication will be determined by the implemented application.

### Proposed dashboard features

1. Authentication screen: RFID scan prompt and authentication feedback.

2. Member profile: Name, role, account status, and active loan details.

3. Take a Book tab: Shows the current physical availability and enables borrowing only when the operation is permitted.

4. Return a Book tab: Displays active loans and permits eligible members to initiate a return.

5. Locker status: Door, lock, and shelf occupancy indicators.

6. Transaction history: Borrowing, return, cancellation, and error records.

7. Staff administration: Member registration, RFID assignment, book configuration, and transaction review.

8. Error notifications: Displays sensor inconsistencies, timeouts, unavailable hardware, and unsuccessful transactions.

The dashboard can use periodic polling or another suitable update mechanism to refresh status. A successful HTTP request alone must not be treated as proof that the physical locker operated successfully.

## 12. Security and Reliability Considerations

Security is important because the system combines account records with a physical access mechanism.

* Protect staff administration routes with authentication and role-based access control.

* Avoid treating an easily copied RFID UID as strong proof of identity for high-security applications.

* Restrict the dashboard to the intended local network during the prototype phase.

* Validate all user inputs and prevent direct database modifications through browser requests.

* Use a transaction state machine to avoid repeated or conflicting commands.

* Apply a lock activation timeout and a maximum door-open interval.

* Ensure GPIO outputs are initialized to safe values during startup and shutdown.

* Log incomplete transactions and provide a controlled recovery procedure.

* Consider backup and database integrity checks.

* Test the behavior during power failure, application restart, network interruption, and sensor disconnection.

The system's power-failure behavior will depend on the selected solenoid lock, mechanical arrangement, and driver circuit. It should be tested rather than assumed to fail securely.


## 13. Scope of the Project

### 13.1 Scope of the initial prototype

The initial implementation will focus on one designated book and one locker compartment. It will include:

* Member authentication through a USB RFID reader.

* Borrowing and returning through the web dashboard.

* Physical book occupancy monitoring.

* Door opening and closing detection.

* Electronic locking and status indication.

* Member-specific loan records and transaction history.

* Basic administrative functions.

* Error handling and transaction recovery.

### 13.2 Future enhancements

![Smart Package Locker System Electronic Digital Parcel Delivery - Smart Lock Interlocking System and Smart Lock System Using Iot](https://images.openai.com/static-rsc-4/PXb2k9-Ncw0U3K4zdAVa9yTKQxgYAkIk7VZeFMbnxkyhkhEwmLWwUCOnJLnMKJUaUz6pv2XSVnJvNv5qF3gSwElvg3Uo-e8ELLDWTEgu55_6N9SrmK-T0N1XxsB8-KnflWx319s-WWSjo-YxbtIUyXmmmdcNZjxr_j7SxTQcznU?purpose=inline)

Multi-compartment expansion

Extend the architecture to support multiple lockers, with a separate inventory record and lock-control channel for each compartment.

![University student scanning a book in  library](https://images.openai.com/static-rsc-4/I0AFaquDybIiKnlP5B6oicyOd5Zvr_mWi4C1LvTnv1dkS06IQncGLPnFs7MaI_nrRehIkmhMGszfD3ZhWXumGB4Dm6N-Oiuyaavwhungu9qmGbGx8YpZumgthoXrvzInYkZs5DHsuL6o3nhTumjZrO4nniagtqWS_OkX_8AZhrmyIXe2d0o7dOfdXLmEawE6?purpose=inline)

Individual book identification

Add barcode scanning, book-specific RFID tags, or another identification method to verify exactly which book is borrowed or returned.

![LIBBY (ONLINE BOOKS) UPDATES — Lawrence Memorial District Library](https://images.openai.com/static-rsc-4/9v6c-0hwkrgYlV0-1pH4_iD2hbJqXfRZb7mrAievhlQP0ntEDyFG1pAsEApp-wuKEUhfkNBeTr1-IaSci4ZIRHSxaag82Uo85B7_z0GiAm58n_qJxAF3caOdwe2rPQIU8P5xyxIPplj962S56ST-0TXZBbhNQ3PqCcMsNe3bSOk?purpose=inline)

Mobile access and notifications

Add a mobile-friendly interface, borrowing confirmations, due-date reminders, and overdue notifications.

![Loans and consultation - Bibliothèque nationale (BnL) - Luxembourg](https://images.openai.com/static-rsc-4/3JuAB1V8SepvyD14U4EOeCRJfWtdQhjIiRhJekCHzEdxDLKsShg_f5Z_IO9fSIs2OtEUuqxNzYkh676wFxuUZCUIWx1ztRQZlOeGgC9g5jHu2dup3CRbzGMm7GEUETnD6do60dGGhG1prq5L0H1DowD6e55xJWLAzoWeDiMXdFE?purpose=inline)

Dedicated self-service kiosk

Replace the laptop kiosk with a touchscreen interface for public library deployment.

Other possible extensions include cloud synchronization, integration with an existing library management system, analytics, remote monitoring, and stronger member authentication.

## 14. Expected Outcomes

At the completion of the project, the expected deliverables are:

1. A functioning physical locker prototype controlled by a Raspberry Pi 3.

2. A web-based interface for authenticated borrowing and returning.

3. A working RFID-based member identification mechanism.

4. Integrated door, shelf occupancy, and entrance sensors.

5. Electronic lock control and blue/green LED indication.

6. A database containing member profiles, active loans, completed loans, and transaction logs.

7. Borrow and return operations that respond to validated sensor conditions.

8. Test results documenting system reliability, transaction accuracy, and response time.

9. Complete source code, circuit documentation, and project report.

The expected benefits include reduced staff involvement in routine transactions, improved visibility of loan records, and the ability to offer self-service access during configured operating hours. These benefits will need to be evaluated through prototype testing before making claims about actual time or cost savings.

## 15. Testing and Evaluation Plan

The prototype will be tested using normal transactions, invalid requests, and fault conditions.

|
Test ID

|

Test scenario

|

Expected result

|
| --- | --- | --- |
|

T01

|

Scan a registered RFID card

|

Correct member profile is displayed

|
|

T02

|

Scan an unregistered card

|

Access is denied; lock remains secured

|
|

T03

|

Borrow when the book is present

|

Authorized borrowing workflow begins

|
|

T04

|

Attempt borrowing when the shelf is empty

|

Borrowing is disabled

|
|

T05

|

Remove the book and close the door

|

Loan completes only if all configured conditions pass

|
|

T06

|

Return the borrowed book

|

Return completes after occupancy and closure verification

|
|

T07

|

Attempt to borrow an already borrowed book

|

Duplicate checkout is prevented

|
|

T08

|

Attempt return without an active loan

|

Return request is rejected

|
|

T09

|

Cancel an operation

|

No false completed transaction is created

|
|

T10

|

Leave the door open beyond the timeout

|

Warning and recovery procedure are triggered

|
|

T11

|

Disconnect an IR sensor

|

Fault is detected where possible; transaction is not falsely confirmed

|
|

T12

|

Restart the Raspberry Pi during an operation

|

Stored records remain consistent and recovery is handled safely

|
|

T13

|

Simulate a failed lock operation

|

System reports the failure rather than assuming success

|
|

T14

|

Perform repeated borrow/return cycles

|

Transaction records and physical states remain consistent

|

### Proposed performance metrics

* Authentication success rate: Correct authentication decisions divided by total authentication tests.

* Transaction completion rate: Successfully completed valid transactions divided by valid transaction attempts.

* False acceptance rate: Invalid or incomplete operations incorrectly recorded as successful.

* Response time: Time from a user action to the corresponding dashboard or hardware response.

* Sensor agreement rate: Percentage of test scenarios in which the observed sensor sequence matches the expected physical state.

No performance figures are assumed in advance. They will be measured during testing, and the final report will include the results.

## 16. Estimated Budget

The following is an initial planning estimate in Indian rupees. These are indicative allowances, not verified live supplier quotations.

|
Component

|

Estimated cost

|
| --- | --- |
|

Raspberry Pi 3 Model B/B+

|

₹2,500–₹4,500

|
|

USB RFID reader and test cards

|

₹300–₹900

|
|

12 V solenoid lock

|

₹300–₹800

|
|

Relay/driver module and protection components

|

₹150–₹400

|
|

MC-38 magnetic door sensor

|

₹80–₹200

|
|

Two FC-51 IR sensors

|

₹100–₹250

|
|

Common-cathode RGB LED and resistors

|

₹20–₹100

|
|

Regulated power supplies

|

₹400–₹900

|
|

Locker enclosure and mounting materials

|

₹500–₹1,500

|
|

Wires, connectors, and miscellaneous parts

|

₹200–₹500

|
|

Estimated total

|

₹4,550–₹10,050

|

The estimate assumes that a suitable laptop is already available and excludes its cost. Actual expenses may differ based on Raspberry Pi availability, existing laboratory equipment, shipping, and enclosure construction. Verify local prices before finalizing the project budget.

## 17. Proposed Project Schedule

A six-week development plan is suggested for the initial prototype.

Week 1

Requirements and design

Finalize the architecture, GPIO plan, database schema, and sensor placement.

Week 2

Backend and dashboard

Develop the Flask application, member interface, and database.

Week 3

RFID and account management

Integrate card reading, account registration, and authorization.

Week 4

Hardware integration

Connect the sensors, lock driver, and RGB LED; test each component independently.

Week 5

Transaction integration

Implement the borrow/return state machine, fault handling, and database synchronization.

Week 6

Testing and documentation

Run test cases, measure performance, fix issues, and prepare the final demonstration and report.

The schedule assumes that the hardware is available at the start and that the core application can be developed alongside component testing. Additional time may be needed for mechanical construction, sensor calibration, and fault recovery.


## 18. Feasibility Analysis

### Technical feasibility

The proposed system combines established technologies: Raspberry Pi GPIO control, USB RFID input, Python web development, relational databases, and basic electronic sensors. The individual components can be developed and tested independently before integration.

### Economic feasibility

The prototype uses a laptop as the user interface and a single locker compartment to limit initial hardware requirements. Its final cost will depend on the Raspberry Pi, locking mechanism, power supply, and enclosure.

### Operational feasibility

The web interface is intended to make borrowing and returning straightforward for students and staff. However, unattended operation requires reliable sensor validation, a safe recovery procedure, and periodic hardware inspection.

### Scalability

The software can be designed to support additional lockers, members, and books. Scaling to multiple compartments will require additional GPIO channels or suitable I/O expansion, individual lock control, inventory management, and more extensive testing.

## 19. Limitations of the Proposed System

The following limitations should be acknowledged in the project report.

1. Single-book tracking: The initial prototype tracks one designated book rather than identifying arbitrary books.

2. No independent book identity verification: Occupancy sensors indicate whether an object is present but cannot establish its title or identity.

3. IR sensor limitations: FC-51 sensors may give inconsistent readings due to alignment, reflectivity, ambient light, and object position.

4. RFID security: A basic RFID UID can potentially be copied or emulated; it should not be treated as high-assurance authentication.

5. Power dependency: The Raspberry Pi, sensors, and locking circuit require appropriate power and restart handling.

6. Physical security: A solenoid lock and three sensors alone do not guarantee resistance to forced entry, tampering, or deliberate sensor manipulation.

7. Library integration: The prototype requires additional software work to integrate with an institution's existing library database or circulation system.

These limitations define the boundaries of the first prototype and provide a basis for future development.

## 20. Conclusion

SmartLocker proposes an IoT-based approach to automating library book dispensing and return operations. By integrating a Raspberry Pi 3, RFID authentication, electronic locking, door and IR sensors, a database, and a web-based dashboard, the system aims to provide a convenient self-service experience while maintaining digital transaction records.

The primary contribution of the initial prototype is the integration of account-based borrowing and returning with physical occupancy verification, without requiring individual book tags for the single designated book. The system also incorporates transaction validation, status indication, and recovery handling to reduce incorrect database updates.

The proposed design provides a foundation for future expansion into multi-compartment lockers, book-specific identification, mobile notifications, and integration with institutional library management systems. Its effectiveness will be assessed through functional testing and measured results rather than assumed performance.

## 21. References and Technical Documentation

The following official documentation can support the implementation and final technical report.

![Raspberry Pi 3 Model B Board Only LN100059 - RASPBERRYPI3-MODB-1GB | SCAN UK](https://images.openai.com/static-rsc-4/gfwCbJKBOM5pxLhtE-NJ3fsIZ4KkltlZhhd2DidoNKwnq3LGELkrzuRLnaqH9eu7lIzDlJXUBKeVmVcOaAevwXaU7wn7G-ZL7M1ffcKETFHfB4Yjf-i2q8P0S69zhnECLKH3zvKNPt-Mbbtq9jBIzYWYWiw-yUL-bnO02RhoBjE?purpose=inline)

Raspberry Pi Documentation

Hardware setup, GPIO considerations, and operating system configuration.

Official documentation

![Top Python Frameworks for 2024 - Earthly Blog](https://images.openai.com/static-rsc-4/8iVfxwKkM7quvzO-fOWtLc2yOsfTDciAnKUzWpfIZArb6quYyU-eLPc7ygeTiBPlak0YTEjUyimLvPZJJleTFr93viBSxBccNW-hZqZrnaNQGSul9zxpacEarFP97FLW1LXURC9Tgz8wgNDI1pOmy5EHCaXfBdaOvuiRbBLzfOs?purpose=inline)

Flask Documentation

Web routes, request handling, templates, and application configuration.

Official documentation

![▷ Best SQLite Course Online](https://images.openai.com/static-rsc-4/JskisXVPtbHvr9eyITeToJGKT2k8O37y_IhEKqM8XMxlIw2iSIp8W_ZaDOsNwpabAdTQCQrsv0d-fqRBSrB4KhB_FU-4h-NuSg4ooJW4EaL4MJMgARdpIXF4XA3hoJQNUJcmbU_ZnF80mwXV7O0WbYNNnaA7tnNvtIKRzgeTEiY?purpose=inline)

SQLite Documentation

Database creation, SQL operations, constraints, and transaction handling.

Official documentation

![How to iterate through a nested JSON, search for a specific value and print the key with Python](https://images.openai.com/static-rsc-4/wX9DB08klfiHDFmiZlFvVe8hnOZkjMK-X939QJluCt1sYU3qgBGAnpoEH5G6RUkPrMA-vMHYLC59ggDCWVemPtYwgLS2NkMtkogmmeT75qK53X1skFEdHue-ICjlLHVuxQVJJsTnrPlubQ0OhXREQK_RBDMY3Mkk4s6lC9gGrJI?purpose=inline)

Python Documentation

Language reference and standard-library documentation.

Official documentation

## 22. Project Information for Submission

Use the following details on the title page of your proposal.

## SMARTLOCKER

IoT-Based Automated Library Book Dispensing and Return System

Student name

Roll number

Institution

Department

Project guide

Academic year

Copy title-page details

Recommended next step: Use this proposal as the basis for your project approval submission. Before finalizing it, confirm your guide's required format, whether a budget table is needed, and whether your institution expects a formal literature review and a Gantt chart.
