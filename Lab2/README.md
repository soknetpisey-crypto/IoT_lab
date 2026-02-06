# Lab 2 : IoT Webserver with LED, Sensors, and LCD Control
this lab focuses on developing an ESP32- based IoT system that integrates a web interface with an LCD display. Users can interact through the web server to control the LCD, monitor sensor data, and send custom messages to be displayed on the screen. 
## Equipment
- ESP32 Dev Board (Micropython firmware flashed)
- DHT11 sensor (temperature/humidity)
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

