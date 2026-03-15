# Mini Project: Smart IoT Parking Management System

---
**Course:** Introduction to Internet of Things <br>
**Department:**  School of Digital Technologies <br>
**University:** American University of Phnom Penh (AUPP)

**Prepared by:**  
- SUN, Kimsroul
- KEATHA, Mesa
- NHEN, Sophamony
- SOK, Netpiseay

**Instructor:** Theara SENG <br>
**Class/Section:** 002 Introduction to Internet of Things <br>
**Academic Year:** Spring 2026  <br>
**Submission Date:** March 14, 2026

**Project Platform:** ESP32 + MicroPython  
**Main Implementation File:** `MiniProjectFinal.py`

---
## EXECUTIVE SUMMARY
This report presents the design and implementation of a Smart IoT Parking Management System using ESP32 and MicroPython. The system integrates physical sensors and actuators with cloud and local interfaces to provide real-time parking monitoring, automated gate operations, and remote manual control.

The implementation includes:
- Ultrasonic sensor for incoming vehicle detection,
- Three IR sensors for slot occupancy,
- Servo motor for gate control,
- Relay for parking lights,
- DHT11 for temperature/humidity,
- TM1637 for slot count display,
- I2C LCD for local system status.

The project also integrates three mandatory IoT platforms:
- Telegram Bot (commands + notifications),
- Web dashboard hosted on ESP32 (monitoring + manual controls),
- Blynk cloud app (remote control + telemetry).

Core engineering contributions include robust decision logic, multi-channel synchronization, memory-aware programming on ESP32, and fault-tolerant network behavior with timeout protection and AP fallback mode.

The final system satisfies all mandatory project requirements and demonstrates a complete embedded IoT solution suitable for practical deployment and future scaling.

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [Project Overview](#2-project-overview)
3. [Project Learning Goals](#3-project-learning-goals)
4. [Hardware Description](#4-hardware-description)
5. [System Architecture](#5-system-architecture)
6. [Software Architecture](#6-software-architecture)
7. [IoT Integration](#7-iot-integration)
8. [Working Process Explanation](#8-working-process-explanation)
9. [Functional Requirements Mapping](#9-functional-requirements-mapping)
10. [Challenges Faced](#10-challenges-faced)
11. [Testing and Validation](#11-testing-and-validation)
12. [Future Improvements](#12-future-improvements)
13. [Conclusion](#13-conclusion)
14. [References](#14-references)
15. [Appendices](#15-appendices)

## LIST OF ABBREVIATIONS
- **ESP32**: Embedded System Platform 32-bit MCU  
- **IoT**: Internet of Things  
- **GPIO**: General Purpose Input/Output  
- **PWM**: Pulse Width Modulation  
- **DHT11**: Digital Humidity and Temperature Sensor  
- **I2C**: Inter-Integrated Circuit  
- **API**: Application Programming Interface  
- **STA Mode**: Station mode (connect to WiFi router)  
- **AP Mode**: Access Point mode  
- **GC**: Garbage Collection  
- **UI**: User Interface  
- **OTA**: Over-the-Air update  
- **MQTT**: Message Queuing Telemetry Transport  
- **TLS**: Transport Layer Security

## 1) INTRODUCTION
Modern parking management requires automation and live visibility to reduce manual effort, traffic delays, and uncertainty about slot availability. This project addresses these needs by implementing a complete Smart IoT Parking Management System on ESP32 with MicroPython.

The system detects vehicles at the entrance, checks available slots, controls gate access, monitors environmental data, manages parking lights, and synchronizes data across Telegram, Web, and Blynk interfaces. It combines autonomous local control and remote manual intervention while maintaining consistent state behavior.

This report documents architecture, implementation details, workflow, challenges, and future upgrade opportunities.

---

## 2) PROJECT OVERVIEW
Each team is required to design and implement a complete embedded IoT parking solution integrating mandatory hardware and three IoT platforms into one unified operational system.

### Delivered capabilities:
- Vehicle detection and smart entry management
- Parking slot occupancy tracking (3 slots minimum)
- Automatic + manual gate operation
- Automatic + manual lighting control
- Real-time dashboard and cloud updates
- Multi-interface remote control (Telegram, Web, Blynk)

---

## 3) PROJECT LEARNING GOALS
This project achieved the following goals:

1. **Design a complete embedded IoT system**  
   Integrated sensing, actuation, networking, and user interfaces.

2. **Integrate hardware with cloud platforms**  
   Implemented Telegram Bot API and Blynk cloud telemetry/control.

3. **Develop real-time monitoring and decision logic**  
   Built threshold and timeout based automation for gate and lights.

4. **Apply system-level engineering thinking**  
   Added network fallback, exception handling, and memory management.

5. **Document architecture professionally**  
   Structured report with hardware/software architecture and flow explanations.

6. **Present technical workflow clearly**  
   Explained lifecycle from system boot to runtime operation and error recovery.

---

## 4) HARDWARE DESCRIPTION

## 4.1 Main Controller
- **ESP32** running **MicroPython**

## 4.2 Mandatory Components
- Ultrasonic sensor (entry detection)
- 3 IR sensors (slot occupancy)
- Servo motor (gate barrier)
- DHT11 (temperature/humidity)
- Relay module (lighting)
- TM1637 display (slot counter)
- LCD I2C 16x2 (status display)

## 4.3 Implemented Pin Mapping
- DHT11 (`PIN_DHT`) → GPIO 4  
- Ultrasonic TRIG (`PIN_TRIG`) → GPIO 27  
- Ultrasonic ECHO (`PIN_ECHO`) → GPIO 26  
- Servo (`SERVO_PIN`) → GPIO 13  
- Relay (`LED_PIN`) → GPIO 2  
- IR slots (`IR_SLOTS`) → GPIO 25, 32, 33  
- TM1637 CLK → GPIO 17  
- TM1637 DIO → GPIO 16  
- I2C SDA → GPIO 21  
- I2C SCL → GPIO 22  
- LCD address → 0x27

## 4.4 Installation Notes
- Ultrasonic mounted facing driveway at stable angle.
- IR sensors aligned at slot positions and calibrated for reliable detection.
- Servo arm mechanically fixed to gate barrier with stable torque.
- Proper power and grounding used for ESP32 + relay + servo reliability.

---

## 5) SYSTEM ARCHITECTURE

## 5.1 High-Level Components
1. **ESP32 Core Controller**
2. **Local Web Server Dashboard**
3. **Telegram Bot Client**
4. **Blynk Cloud Client**
5. **Local Display Layer (TM1637 + LCD)**

## 5.2 Logical Data Flow
Sensors → ESP32 processing loop → state cache update → actuator commands + status publishing  
Remote commands (Telegram/Web/Blynk) → unified control handlers → synchronized state update

## 5.3 Architectural Characteristics
- Centralized runtime state (`sensor_cache`, `stats`, manual flags)
- Cooperative periodic scheduling
- Multi-channel command handling
- Fault-tolerant behavior using try/except and timeouts

---

## 6) SOFTWARE ARCHITECTURE

## 6.1 Program Organization (`MiniProjectFinal.py`)
The software is implemented in one script with clear functional sections:
- constants and device setup
- utility functions
- network initialization
- cloud integrations
- web server
- main runtime loop

## 6.2 Core Global Variables
- `gate_state`, `gate_manual`, `light_manual`
- `stats = {'entries', 'exits', 'gates'}`
- `sensor_cache = {'temp','hum','dist','free'}`

## 6.3 Utility Layer
- `angle_to_duty()`, `set_servo()`
- `ultrasonic_dist()`
- `read_dht()`
- `count_slots()`
- `tm_show_value()`, `lcd_show()`

## 6.4 Networking and Cloud Layer
- `connect_wifi()` with retry + AP fallback
- Telegram: `tg_send()`, `tg_poll()`
- Blynk: `blynk_get()`, `blynk_write()`, `blynk_update()`, `blynk_poll()`

## 6.5 Web Layer
HTTP endpoints:
- `/api/data`
- `/api/gate/open`
- `/api/gate/close`
- `/api/lights/on`
- `/api/lights/off`

## 6.6 Scheduler Model
- Sensor read every 2s
- Telegram polling every 20s
- Blynk update/poll every 5s
- Web accepts requests in short timeout loop

---

## 7) IoT INTEGRATION

## 7.1 Telegram Bot (Commands + Notifications)
Implemented commands:
- `/help`, `/start`
- `/status`
- `/slots`
- `/temp`
- `/open`, `/close`
- `/light_on`, `/light_off`
- `/stats`

Behavior:
- Poll updates from Bot API
- Validate `TELEGRAM_CHAT_ID`
- Execute control + send response messages

## 7.2 Web Dashboard (Monitoring + Manual Control)
Features:
- Live values for slots, temperature, humidity, distance, gate, lights
- Slot occupancy cards (3 slots)
- Statistics panel (entries/exits/gates)
- Buttons for gate and light control
- Polls `/api/data` every 2 seconds

## 7.3 Blynk App (Remote Control + Data Display)
Virtual pins:
- V0: free slots
- V2: temperature
- V3: gate command
- V5: gate state
- V6: light state

Special logic:
- Detect command transitions to avoid repeated actions

---

## 8) WORKING PROCESS EXPLANATION

## 8.1 Boot Stage
1. Initialize sensors, actuator outputs, display interfaces.
2. Connect to WiFi (retry up to 5 attempts).
3. If fail, activate AP mode (`ESP32_Device`).
4. Set gate to closed for safe startup.
5. Display system readiness and IP on LCD.

## 8.2 Periodic Sensor Cycle
- Read ultrasonic, DHT11, IR slots.
- Update `sensor_cache`.
- Update TM1637 and LCD.
- Track entry/exit stats if slot count changes.

## 8.3 Automatic Logic
### Gate:
- Open if vehicle is near + free slot available + no manual lock.
- Close after no-vehicle timeout.

### Lights:
- Auto ON when occupied.
- Auto OFF after delay when lot empty.
- Respect manual override lock.

## 8.4 Remote Command Cycle
- Telegram polled periodically.
- Blynk values synced and command pin polled.
- Web requests processed continuously.

## 8.5 Maintenance Cycle
- Frequent `gc.collect()` calls.
- Short non-blocking waits.
- Exception handling keeps loop alive.

---

## 9) FUNCTIONAL REQUIREMENTS MAPPING

| Functional Requirement                         | Implemented Method                      |
| ---------------------------------------------- | --------------------------------------- |
| Detect incoming vehicle using Ultrasonic       | `ultrasonic_dist()` with threshold      |
| Check slot availability before gate opens      | `count_slots()` and `free > 0`          |
| Control gate via Auto + Telegram + Web + Blynk | `open_gate()` / `close_gate()`          |
| Detect slot occupancy using IR sensors         | 3 digital IR inputs                     |
| Real-time available slot updates               | periodic polling + dashboard/Blynk sync |
| Display slot count on TM1637                   | `tm_show_value()`                       |
| Display status on LCD I2C                      | `lcd_show()`                            |
| Monitor temperature/humidity                   | `read_dht()` + UI updates               |
| Control lights manually + automatically        | relay + logic + manual flag             |

---

## 10) CHALLENGES FACED

## 10.1 Memory Outage with ESP32
**Cause:** Limited heap with multiple libraries and dynamic strings.  
**Mitigation:**
- aggressive `gc.collect()`,
- defensive try/except blocks,
- reduced memory pressure in loop operations.

## 10.2 Network Connection Error and Packet Loss
**Cause:** intermittent WiFi/cloud instability.  
**Mitigation:**
- retry-based connect logic,
- AP fallback mode,
- request timeout and exception handling,
- non-blocking web socket accept.

## 10.3 Synchronizing All Feed Channels
**Cause:** Telegram, Web, and Blynk can issue overlapping commands.  
**Mitigation:**
- manual override flags for gate/light,
- shared state cache,
- Blynk previous-command check to prevent duplicate triggers.

---

## 11) TESTING AND VALIDATION

## 11.1 Functional Tests
- Auto open when object enters threshold
- Auto close after vehicle leaves for timeout
- Slot count changes reflected in all interfaces
- Temperature/humidity visible on cloud/local UI
- Relay manual on/off and auto behavior verified

## 11.2 Interface Tests
- Telegram command responses successful
- Web controls execute and update state
- Blynk command transitions trigger correct gate action
- Cross-platform state remains consistent

## 11.3 Resilience Tests
- WiFi interruption → system keeps local core logic running
- Cloud/API timeout → loop continues without crash
- Memory pressure → periodic GC prevents long-run freeze

---

## 12) FUTURE IMPROVEMENTS

1. Move credentials to `secrets.py` and secure storage  
2. Replace HTTP polling with MQTT + TLS  
3. Refactor to `uasyncio` for better non-blocking concurrency  
4. Add secure OTA update support  
5. Add persistent event logging and analytics  
6. Add authentication to web dashboard  
7. Upgrade sensors and add redundancy  
8. Add calibration/diagnostic mode endpoints  

---

## 13) CONCLUSION
The Smart IoT Parking Management System successfully demonstrates a complete embedded IoT solution with real-time sensing, autonomous control, and multi-platform remote integration. The final implementation satisfies all required hardware, software, and functional criteria while addressing practical reliability issues in memory and networking.  
This project provides a strong foundation for advanced smart parking deployments with future enhancements in security, scalability, and asynchronous architecture.

---

## 14) REFERENCES
1. ESP32 MicroPython documentation  
2. MicroPython `machine`, `network`, `socket`, and `dht` modules  
3. Telegram Bot API documentation  
4. Blynk External HTTP API documentation  
5. TM1637 and I2C LCD MicroPython library documentation

---

## 15) APPENDICES

## Appendix A: Pin Mapping
- GPIO4: DHT11  
- GPIO27: Ultrasonic TRIG  
- GPIO26: Ultrasonic ECHO  
- GPIO13: Servo  
- GPIO2: Relay  
- GPIO25/32/33: IR slot sensors  
- GPIO17/16: TM1637  
- GPIO21/22: I2C LCD  

## Appendix B: API and Command Reference
### Web
- `/api/gate/open`
- `/api/gate/close`
- `/api/lights/on`
- `/api/lights/off`
- `/api/data`

### Telegram
- `/help`, `/start`, `/status`, `/slots`, `/temp`, `/open`, `/close`, `/light_on`, `/light_off`, `/stats`

### Blynk
- V0, V2, V3, V5, V6

## Appendix C: Figure Placeholders and Diagrams Section

### Figure 1 — Overall System Architecture  
<img alt="image" src="assets/System Architecture Block Diagram.png">  

### Figure 2 — Process Flow Diagram
<img alt="image" src="assets/Process Flow Diagram.png">

### Figure 4 — Main Loop Flowchart  
`[Insert Figure 4: Runtime control loop flowchart]`

### Figure 5 — Gate Decision Logic  
`[Insert Figure 5: Auto/manual gate logic flowchart]`

### Figure 6 — Light Decision Logic  
`[Insert Figure 6: Manual/auto light control flowchart]`

### Figure 7 — Telegram Screenshots  
`[Insert Figure 7A/7B/7C: Telegram command responses]`

### Figure 8 — Web Dashboard Screenshots  
`[Insert Figure 8A/8B/8C: Dashboard + controls]`

### Figure 9 — Blynk Screenshots  
`[Insert Figure 9A/9B/9C: Blynk widgets and control]`

### Figure 10 — Physical Prototype Photo  
`[Insert Figure 10: Real hardware setup]`

### Figure 11 — Functional Test Matrix  
`[Insert Figure 11: Pass/fail result table]`

### Figure 12 — Network Recovery Sequence  
`[Insert Figure 12: Timeout/reconnect/AP fallback sequence]`
