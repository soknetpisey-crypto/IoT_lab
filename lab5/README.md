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

#### Driver Motor → ESP32
| Driver Motor | ESP32 Pin |
|----------|-----------|
| GND | GND |

#### Driver Motor → Power Supply
| Driver Motor | Power Supply |
|----------|-----------|
| VCC | VCC/5V |
| OUT | GPIO 12 (D12) |
| GND | GND |

#### IR Sensor → ESP32
| IR Sensor | ESP32 Pin |
|----------|-----------|
| VCC | VCC/5V |
| OUT | GPIO 12 (D12) |
| GND | GND |
