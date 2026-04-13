# LAB 6: Smart RFID System with Cloud & SD Logging
## Overview
This project is a Smart RFID-based Attendance System built using an ESP32 and MicroPython. It uses an RFID-RC522 module to identify users, logs attendance locally on
an SD card, and stores data remotely in Google Firestore. A buzzer provides real-time feedback for user interaction.

## Features
- RFID card detection (UID reading)
- Student identification using UID database
- Real-time date and time generation
- Local data logging (CSV file on SD card)
- Cloud logging using Firestore
- Buzzer feedback system
- Invalid card detection

## System Workflow
1. Scan RFID card
2. Read UID from card
3. Check UID in student database
4. Generate timestamp
5. Perform action:
   - Valid Card:
      - Beep (0.3 sec)
      - Save to SD card
      - Send data to Firestore
   - Invalid Card:
      - Long beep (3 sec)
      - Display "Unknown Card"
## Hardware Components
- ESP32
- RFID-RC522 Module
- SD Card Module
- Buzzer
- Jumper Wires
- RFID Cards/Tags

## Pin Configuration
