# System Architectural Design

Project Title: SmartLocker – IoT-Based Automated Library Book Dispensing and Return System

## 1. System Architecture Diagram

### User / Library Staff

RFID card • Borrow / Return request

### RFID Reader

Reads card identifier

## Raspberry Pi 3 Model B/B+

Main controller • Authentication • Decision logic

#### Input Section

IR shelf sensor

IR entrance sensor

Magnetic door sensor

#### Output Section

Lock driver and solenoid

RGB LED indicator

The controller reads sensor inputs and commands output devices.

### Software and Data Layer

Python • Flask • SQLite Database

### Web Dashboard

Book availability • User records • Loan history • System status

Figure 1. Proposed system architecture of SmartLocker.

## 2. Description of Architectural Components

### 2.1 User interface layer

Users and library staff interact with the system using RFID cards and the web dashboard. The interface provides access to borrowing, returning, book availability, and transaction information.

### 2.2 Authentication layer

The RFID reader reads the presented card identifier. The software checks the identifier against registered members in the database. Only authorized users can proceed with permitted operations.

### 2.3 Processing and control layer

The Raspberry Pi acts as the central controller. It processes authentication results, checks book availability, monitors sensor inputs, controls the locking mechanism, and coordinates database updates.

### 2.4 Sensor input layer

* IR shelf sensor: Detects the presence or absence of the designated book.

* IR entrance sensor: Detects object movement near the compartment opening.

* Magnetic door sensor: Detects whether the compartment door is open or closed.

These sensor readings are evaluated together to determine whether the expected operation has occurred. IR sensors do not identify a book by itself; the prototype is intended for a designated book in a single compartment.

### 2.5 Actuator output layer

The controller operates the solenoid lock through a suitable relay or transistor driver. An RGB LED indicates the operating state, such as standby or an active operation. The lock must use an appropriately rated power supply and must not be powered directly from a Raspberry Pi GPIO pin.

### 2.6 Database and application layer

The Flask application processes requests and communicates with the SQLite database. The database stores member information, compartment status, borrowing records, return records, and transaction logs.

### 2.7 Monitoring layer

The web dashboard displays the latest available information. It should distinguish between a lock command and a physically verified lock state when lock-position feedback is not available.

## 3. Working Sequence

1. The user presents an RFID card.

2. The Raspberry Pi verifies the user's authorization.

3. The software checks the designated book's availability or active loan.

4. The lock is released for an authorized borrowing or return operation.

5. The sensors monitor the book position, passage event, and door state.

6. The software checks the expected final sensor conditions.

7. The database and dashboard are updated only after the operation is verified.

8. If a timeout, sensor fault, or inconsistent state occurs, the operation is flagged for review rather than recorded as successful.

## 4. Architectural Design Summary

|
Layer

|

Main components

|

Responsibility

|
| --- | --- | --- |
|

User layer

|

RFID card, web browser

|

Initiates and monitors operations

|
|

Authentication layer

|

USB RFID reader

|

Reads user credentials

|
|

Control layer

|

Raspberry Pi, Python

|

Executes control logic

|
|

Input layer

|

IR sensors, magnetic sensor

|

Monitors book and door conditions

|
|

Output layer

|

Solenoid lock, driver, RGB LED

|

Controls access and indicates status

|
|

Data layer

|

Flask, SQLite

|

Processes requests and maintains records

|
|

Presentation layer

|

HTML, CSS, JavaScript

|

Displays system status and history

|

Conclusion: The proposed architecture integrates embedded control, sensor monitoring, electronic access control, database management, and a web interface into a single automated library locker system.
