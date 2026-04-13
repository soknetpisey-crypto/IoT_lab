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
#### RC522 → ESP32
| RC522 Pin | ESP32 Pin |
|----------|-----------|
| SDA (SS) | GPIO 16 (D16) |
| SCK | GPIO 18 (D18) |
| MOSI | GPIO 23 (D23) |
| MISO | GPIO 19 (D19) |
| RST | GPIO 22 (D22) |
| GND | GND |
| 3.3V | 3.3V |

#### SD Card → ESP32
| SD Pin | ESP32 Pin |
|----------|-----------|
| CS | GPIO 13 (D13) |
| SCK | GPIO 14 (D14) |
| MOSI | GPIO 15 (D15) |
| MISO | GPIO 2 (D2) |

#### Buzzer → ESP32
| Buzzer Pin | ESP32 Pin |
|----------|-----------|
| + | 5V) |
| - | GND |
| S | GPIO 4 (D4) |

## Firestore Setup
1. Create a project in Firebase
2. Enable Firebase Database
3. Copy the project ID
4. Update in the code

## CSV Format 
Data stored in SD card: <br>
UID, Name, StudentID, Major, DateTime <br>
Example: <br>
12345678,Kim Taehyung,2023001,IT,2025-03-10 10:15:30 <br>

## Task 
1. Read UID from RFID card
- Detect card and retrieve its unique ID (UID)
2. Match UID with student database
- Compare UID with predefined data
- If found ->valid student
- If not -> unknown card
3. Generate current datetime
- Format: <br>
YYYY-MM-DD HH:MM:SS
4. If UID is valid:
- Activate buzzer for 0.3 seconds
- Save data to SD card (CSV format):
UID, Name, StudentID, Major, DateTime
- Send data to Firestore
5. If UID is invalid:
- Activate buzzer for 3 seconds
- Display: "Unknown Card"
- Do not save or send data 
<br>Video Evidence: https://youtu.be/RvyzR_OVraE
<img width="1906" height="963" alt="image" src="https://github.com/user-attachments/assets/4f04b100-489b-41e4-b4da-d6e6ee999db7" />

## Flowchart
<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/8cddb88e-3adf-4569-b238-a9c6f3da6398" />
