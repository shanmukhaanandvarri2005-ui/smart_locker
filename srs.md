# System Requirements – Software Requirements

Project Title: SmartLocker: IoT-Based Automated Library Book Dispensing and Return System

## 1. Software Requirements

The following software is required to develop and operate the SmartLocker system.

|
S. No.

|

Software

|

Purpose

|
| --- | --- | --- |
|

1

|

Raspberry Pi OS

|

Operating system for the Raspberry Pi 3 Model B/B+

|
|

2

|

Python 3

|

Programming the system logic, sensor monitoring, and lock control

|
|

3

|

Flask

|

Developing the web application and backend

|
|

4

|

HTML5

|

Designing the dashboard structure

|
|

5

|

CSS3

|

Styling the dashboard

|
|

6

|

JavaScript

|

Handling dashboard interactions and status updates

|
|

7

|

SQLite

|

Storing member details, book availability, loan records, and transaction history

|
|

8

|

GPIO control library

|

Interfacing the Raspberry Pi with sensors, LED, and lock driver

|
|

9

|

USB RFID reader interface

|

Reading RFID card data for authentication

|
|

10

|

Web browser

|

Accessing the SmartLocker dashboard

|
|

11

|

Visual Studio Code or Thonny

|

Writing, editing, and debugging Python code

|
|

12

|

Git (optional)

|

Version control and source-code management

|

## 2. Minimum Development Environment

* Programming language: Python 3

* Web framework: Flask

* Database: SQLite

* Frontend: HTML, CSS, JavaScript

* Controller platform: Raspberry Pi 3 Model B/B+

* Development computer: Laptop or desktop computer

* Browser: Chrome, Firefox, or another modern browser

* Network: Local Wi-Fi or Ethernet if the dashboard is accessed from another device

## 3. Required Python Packages

Depending on the selected hardware and software implementation, the following packages may be required:

|
Package

|

Purpose

|
| --- | --- |
|

`Flask`

|

Web application

|
|

`gpiozero` or a compatible GPIO library

|

Sensor and output control

|
|

`sqlite3`

|

Database operations; included with standard Python installations

|
|

`pytest` (optional)

|

Software testing

|

The exact GPIO library depends on the Raspberry Pi OS version and the selected GPIO interface. USB RFID readers that emulate a keyboard may not require an additional Python RFID library.

## 4. Functional Software Requirements

1. The software shall authenticate users using registered RFID card identifiers.

2. It shall check book availability before permitting borrowing.

3. It shall monitor the compartment door and book-related sensor states.

4. It shall control the electronic lock through a suitable driver interface.

5. It shall record verified borrowing and return transactions in SQLite.

6. It shall display book availability and transaction history on the web dashboard.

7. It shall handle invalid cards, timeouts, sensor faults, and cancelled operations.

8. It shall prevent incomplete operations from being recorded as successful transactions.

## 5. Non-Functional Software Requirements

* Reliability: Maintain consistent database records during normal operation and recovery.

* Security: Restrict unauthorized access to member and administrative functions.

* Usability: Provide a simple dashboard with clear status indicators.

* Maintainability: Separate authentication, sensor control, database, and web-interface code into modules.

* Performance: Respond to user actions within a practical time for a local prototype.

* Recoverability: Detect interrupted operations and flag uncertain physical states for review.

Note: Raspberry Pi OS, Python 3, Flask, and SQLite are the core software components. The remaining tools and packages depend on the exact implementation and development workflow.
