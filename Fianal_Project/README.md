# Final Project
## AgriSafe Rot Spotter: A Multi-Modal Edge-AI System for Early Post-Harvest Spoilage Detection
### I.Project Overview
This project, AgriSafe Rot-Spotter: A Multi-Modal Edge-AI System for Early Post-Harvest Spoilage Detection, is an IoT-based system that helps detect spoilage early. It uses sensors and a camera to monitor things like temperature , humidity, and the condition of the food. The system uses AI on a local device (edge device) to analyze the data quickly. With this system, users can know early when food stars to spoil and take action in time. It helps reduce waste, save money, and improve food quality. 
### II. Problem
Post-harvest spoilage is a major issue in agriculture:
- Large amount of food is wasted due to late detection
- Manual inspection is slow and inaccurate
- Environmental conditions are not properly monitored.
### III. Objective
- Combine image and sensor data (multi-modal approach)
- Detect spoilage at an early stage
- Process data locally using Edge AI
- Reduce agricultural losses
### IV. System Architecture
Input -> Edge Processing -> Output -> Action
#### 1. Input
- ESP32-CAM captures images of crops
- DHT11 sensor measures temperature & humidity
- IR sensor detects object presence.
#### 2. Processing
- ESP32 processes sensor and image data
- AI analyzes color, texture, and environment
- Web Server with internet connection for remote monitoring
#### 3. Output
- LCD displays system status
- Online web dashboard shows live data
- Alerts triggered when spoilage detected.
#### 4. Action
- Servo/DC motor controls gate
- Gate closes if spoilage detected
- Gate remains open if crops are healthy.
### V. Key Features
- Multi-modal detection (image + sensors)
- Real-time monitoring
- Internet-enable web server (remote access)
- Edge computing (low latency)
- Automatic gate control
- Early warming system
- Low-cost and scalable.
### VI. Methodology 
#### 1. System Design
Design connections between ESP32, sensors, camera, actuators, and internet connectivity.
#### 2. Data Processing
Process real-time data locally using AI or rule-based logic.
#### 3. Spoilage Detection
Detect color changes, texture issues, and environmental risks.
#### 4. Automated Response
Close gate and trigger alerts is spoilage detected
#### 5. Alert System
Display warnings on LCD and online web dashboard
#### 6. Testing & Evaluation
Test under different conditions to measure accuracy and performance.
### VII. Components
- ESP32
- ESP32-CAM
- DHT11 Sensor
- 12C LCD Display
- IR Sensor
- Servo Motor
- 2 DC Motor
- Power Supply
### VIII. How it works
1. Capture image of stored fruits
2. Collect environmental data from sensors
3. Process data using AI model
4. Detect spoilage condition
5. Send alert to user.
### IX. Results
- Early detection of spoilage
- Improved accuracy using multi-modal data
- Reduced food loss in storage
