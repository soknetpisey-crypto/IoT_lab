# Lab 2 : IoT Webserver with LED, Sensors, and LCD Control
this lab focuses on developing an ESP32- based IoT system that integrates a web interface with an LCD display. Users can interact through the web server to control the LCD, monitor sensor data, and send custom messages to be displayed on the screen. 
## Equipment
<img width="960" height="1280" alt="image" src="https://github.com/user-attachments/assets/4d5c6986-be26-409d-a70d-7e0b1fc36c4a" />

- ESP32 Dev Board (Micropython firmware flashed)
- DHT22 sensor (temperature/humidity)
- HC-SR04 ultrasonic distance sensor
-	LCD 16x2 with I2C backpack
-	Breadboard, jumper wires
-	USB cable + laptop with Thonny
- Wi-fi access
## Wiring Connection
## Set up instructions
### 1. Hardware Setup
- Connect all components according to the wiring diagram
- Ensure the ESP32 is properly powered via USB
- Verify all sensor connections are secure
#### DHT22 → ESP32
| DHT22 Pin | ESP32 Pin |
|----------|-----------|
| VCC (+) | VCC/5V |
| DATA (I/O) | GPIO 4 (D4) |
| GND (-) | GND |
#### Ultrasonic Sensor → ESP32
| Ultrasonic Sensor | ESP32 Pin |
|----------|-----------|
| VCC | VCC/5V |
| Tring | GPIO 27 (D27) |
| Echo | GPIO 26 (D26) |
| GND | GND |
#### LCD 12C → ESP32
| LCD 12C | ESP32 Pin |
|----------|-----------|
| VCC | VCC/5V |
| GND | GND |
| SDA | GPIO 21 (D21) |
| SCL | GPIO 22 (D22) |
### 2. Micropython Environment
- Open **Thonny IDE** on your laptop
- Connect the ESP32 via USB
- Verify Micropython firmware is installed ( check interpreter in bottom-right corner)
- Select the correct COM port for your ESP32
### 3. Wi-fi Configuration
Edit each file with your wi-fi credentials:
### 4. Required Libraries
Upload the following libraries to your ESP32:
### 5. Upload Main Code
- The script should:
    - Connect to Wi-fi
    - Initialize sensors and LCD
    - Start the web server
### 6. Running the Server
1. Reset the ESP32
2. Wait for Wi-Fi connection
3. Note the **IP address** displayed in the serial monitor
4. Open a web browser and navigate
## Tasks and Checkpoints
### Task 1 - LED Control
Evidence: https://drive.google.com/drive/folders/13wvs1C-SneUwzVL0l1u5jbmjctAps9cX?usp=sharing
### Task 2 - Sensor Read
<img width="1280" height="626" alt="image" src="https://github.com/user-attachments/assets/46d6f38b-8bb5-46be-9662-6941ef75080b" />

### Task 3 - Sensor
### Task 4 - Textbox
### Wire Diagram
<img width="3970" height="8192" alt="ESP32 LCD HTTP Route Flow-2026-02-05-053536" src="https://github.com/user-attachments/assets/c5d4d7cc-3fd0-452a-8eeb-5a65f73bbad1" />
