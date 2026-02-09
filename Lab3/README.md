# Lab3: Iot Smart Gate Control With Blynk, IR Sensor, Servo Motor, and TM1637
## 1. Overview
This lab aims to design and implement an ESP32-based IoT system using Micropython and the Blynk platform. The system integrates an IR sensor for object detection, a servo motor for physical actuation, and a TM1637 7-segment display for real-time local feedback. 
## 2. Equipment
- ESP32 Dev Board
- 16x2 LCD Display
- 12C LCD Backpack (PCF8574)
- Jumper Wires
- USB cable for ESP32
## 3. System Description
An IR sensor is used to sense when an object approaches the system. Once detection occurs, the ESP32 interprets the signal and drives a servo motor to mimic the opening of a gate or barrier. Every time an object is detected, a counter increases, and the updated count is a shown a TM1637 display while also being transmitted to the Blynk application for remote tracking. 
## 4. Tasks and Checkpoints
### Task 1: IR Sensor Reading
- Read IR sensor digital output using ESP32
- Display IR status (Detected / Not Detected) on Blynk
<img width="1603" height="804" alt="Screenshot 2026-02-09 130323" src="https://github.com/user-attachments/assets/68147d2a-2967-4055-9a20-edd63030996e" />

<img width="1603" height="788" alt="image_2026-02-09_13-04-15" src="https://github.com/user-attachments/assets/36cdf195-dec0-43a1-b440-286cfcde0257" />

### Task 2: Servo Motor Control via Blynk
### Task 3: Automatic IR- Servo Action
### Task 4: TM1637 Display Integration
### Task 5: Manual Override Mode

