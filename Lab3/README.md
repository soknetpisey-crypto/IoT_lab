# Lab3: Iot Smart Gate Control With Blynk, IR Sensor, Servo Motor, and TM1637
## 1. Overview
This lab aims to design and implement an ESP32-based IoT system using Micropython and the Blynk platform. The system integrates an IR sensor for object detection, a servo motor for physical actuation, and a TM1637 7-segment display for real-time local feedback. 
## 2. Equipment
- ESP32 Dev Board
- 16x2 LCD Display
- 12C LCD Backpack (PCF8574)
- Jumper Wires
- USB cable for ESP32
## 3. Wiring Connection
  <img width="1073" height="613" alt="image" src="https://github.com/user-attachments/assets/ed7edab2-e898-4ef5-935a-cefc7140ee3a" />
  
#### IR Sensor → ESP32
| IR Sensor | ESP32 Pin |
|----------|-----------|
| VCC | VCC/5V |
| OUT | GPIO 12 (D12) |
| GND | GND |

#### Sevor Sensor → ESP32
| Servo Sensor | ESP32 Pin |
|----------|-----------|
| Yellow Wire | GPIO 13 (D13) |
| Red Wire | VCC/5V |
| Brown Wire | GND |

#### TM1637 → ESP32
| TM1637| ESP32 Pin |
|----------|-----------|
| GND | GND |
| VCC | VCC/5V |
| DIO | GPIO 16 (D16) |
| CLK | GPIO 17 (D17) |

## 4. System Description
An IR sensor is used to sense when an object approaches the system. Once detection occurs, the ESP32 interprets the signal and drives a servo motor to mimic the opening of a gate or barrier. Every time an object is detected, a counter increases, and the updated count is a shown a TM1637 display while also being transmitted to the Blynk application for remote tracking. 
## 5. Tasks and Checkpoints
### Task 1: IR Sensor Reading
- Read IR sensor digital output using ESP32
- Display IR status (Detected / Not Detected) on Blynk
<img width="1603" height="804" alt="Screenshot 2026-02-09 130323" src="https://github.com/user-attachments/assets/68147d2a-2967-4055-9a20-edd63030996e" />

<img width="1603" height="788" alt="image_2026-02-09_13-04-15" src="https://github.com/user-attachments/assets/36cdf195-dec0-43a1-b440-286cfcde0257" />

### Task 2: Servo Motor Control via Blynk
- Add a Blynk Slider widget to control servor position.
- Slider position from 0 to 180 degree and the servo is moving following the slider. <br>
Video Evidence: https://youtu.be/4t-Uhp8_JVw?feature=shared
### Task 3: Automatic IR- Servo Action
- When IR sensor detects an object, servo opens automatically.
- After a short delay, servo returns to closed position. <br>
Video Evidence: https://youtu.be/sCNMGhiOjLc?feature=shared
### Task 4: TM1637 Display Integration
- Count the number of IR detection events.
- Display the counter value on the TM1637 display.
- Send the same value to Blynk numeric display widget. <br>
Video Evidence: https://youtu.be/w7w-R8_-Dso?feature=shared
### Task 5: Manual Override Mode
- Add a Blynk switch to enable/disable automic IR mode.
- When manual mode is active, IR sensor is ignored. <br>
Video Evidence: https://youtu.be/g4tDh4JYB_U?feature=shared
