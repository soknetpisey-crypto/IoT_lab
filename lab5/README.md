# LAB5: Smart Color Detection & Control with MIT App
In this lab, student will design and implement a color-based IoT control system using ESP32 and Micropython (Thonny). The system integrates TCS34725 (color sensor), NeoPixel (RGB LED), and a DC motor. Students must implement edge logic processing to clasify colors and control accordingly. The system will also communicate with MIT App Inventor for real-time monitoring and manual control. 
## CLO Alignment
- Integrate 12C sensor (TCS34725) with ESP32.
- Implement rule-based color classification logic.
- Control NeoPixel LED using RGB values. 
- Control DC motor speed using PWM.
- Design a mobile app using MIT App Inventor.
- Implement combined automatic and manual control systems.
## Connection
<img width="960" height="1280" alt="image" src="https://github.com/nsmony/IoT_lab/blob/main/lab5/Screenshot%202026-04-02%20125528.png" />

#### WS2812 → ESP32
| WS2812 | ESP32 Pin |
|----------|-----------|
| DI | GPIO 23 (D23) |
| 5V | 5V |
| GND | GND |

#### TCS34725 → ESP32
| TCS34725 | ESP32 Pin |
|----------|-----------|
| SLC | GPIO 22 (D22) |
| SDA | GPIO 21 (D21) |
| GND | GND |
| 3V3 | VCC/3.3V |

#### L298N → ESP32
| L298N | ESP32 Pin |
|----------|-----------|
| ENA | GPIO 14 (D14) |
| IN1 | GPIO 26 (D26) |
| IN2 | GPIO 27 (D27) |
| GND | GND |

#### L298N → Power Supply
| L298N | Power Supply |
|----------|-----------|
| +12V | +6V |
| GND | -6V |

#### DC Motor → L298N
| DC Motor |L298N |
|----------|-----------|
| IN1 | OUT1 |
| IN2 | OUT2 |

## System Working Principle
The ESP32 continuously reads RGB values from the TCS34725 sensor. Based on the highest RGB value, the system classifies the detected color and performs control
actions.

### Automatic Control Logic
| Detect Color | NeoPixel Color | Motor PWM |
|----------|-----------|-----------|
| RED | Red | 700 |
| GREEN | Green| 500 |
| BLUE | Blue | 300 |

## MIT App Inventor Interface
The mobile application includes:
### Display Components
- Label showing detected color
### Control Components
- Forward button
- Stop button
- Backward button
- RGB input text boxes
- Set Color button
### The app communicates with ESP32 to:
- Display detected color
- Send manual motor commands
- Send manual RGB values

## Tasks & Checkpoints
### Task 1 - RGB Reading
- Read RGB values from TCS34725.
- Print values to Serial Monitor.

<img width="1180" height="1001" alt="image" src="https://github.com/user-attachments/assets/f58cde49-15c8-48c5-b07e-a539cb6d9a3e" />

### Task 2 - Color Classification
Classification Rules:
- R > G and R > B → RED
- G > R and G > B → GREEN
- B > R and B > G → BLUE

### Task 3 - NeoPixel Control
- RED → NeoPixel shows Red
- GREEN → NeoPixel shows Green
- BLUE → NeoPixel shows Blue

### Task 4 - Motor Control (PWM)
- RED → PWM = 700
- GREEN → PWM = 500
- BLUE → PWM = 300

### Task 5 - MIT App Integration
App Requirements:
- Display detected color (Label).
- Buttons: Forward, Stop, Backward.
- RGB input boxes (R, G, B).
- Button to set NeoPixel color manually.
