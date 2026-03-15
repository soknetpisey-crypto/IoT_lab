# System Logic Explanation

This section explains how the Smart IoT Parking Management System makes decisions at runtime and keeps all channels (Telegram, Web, Blynk, local displays) synchronized.

---

## 1) Core Logic Model

The ESP32 is the single source of truth.  
All sensor readings, control decisions, and remote commands are processed through centralized global states:

- `sensor_cache`: latest telemetry (`temp`, `hum`, `dist`, `free`)
- `gate_state`: `'OPEN'` / `'CLOSED'`
- `gate_manual`: blocks auto-gate behavior when manual control is active
- `light_manual`: blocks auto-light behavior when manual control is active
- `stats`: counters for entries, exits, gate operations

This architecture prevents fragmented decisions and keeps behavior consistent across all interfaces.

---

## 2) Sensor-to-Decision Pipeline

### 2.1 Periodic Sensor Sampling
Every `SENSOR_INTERVAL` (2 seconds), the controller reads:
- Ultrasonic distance (`ultrasonic_dist()`)
- DHT11 temperature and humidity (`read_dht()`)
- IR slot states (`count_slots()`)

### 2.2 State Update
After reading sensors:
- `sensor_cache` values are refreshed
- TM1637 is updated with free slot count
- LCD is updated with compact runtime information
- Entry/exit stats are updated when free slots change

### 2.3 Decision Triggers
Sensor values drive:
- gate auto-open/auto-close logic
- light auto on/off logic
- cloud telemetry refresh values for Blynk, Telegram status, and web API

---

## 3) Gate Logic (Auto + Manual)

## 3.1 Automatic Gate Open
Gate opens only if all conditions are true:
1. `gate_manual == False`
2. `gate_state == 'CLOSED'`
3. ultrasonic distance is valid and `< AUTO_OPEN_DISTANCE`
4. `sensor_cache['free'] > 0`

This ensures entry is allowed only when a vehicle is detected and parking space exists.

## 3.2 Automatic Gate Close
If gate is open, the system tracks vehicle visibility timer:
- if vehicle is not detected near entry for `VEHICLE_TIMEOUT`, gate closes automatically
- if vehicle is still near, open state is maintained

## 3.3 Manual Gate Control
Manual commands may come from:
- Telegram (`/open`, `/close`)
- Web API (`/api/gate/open`, `/api/gate/close`)
- Blynk (`V3 = 1/0`)

Manual action updates gate behavior flags to avoid conflict with automatic actions.  
This gives users predictable override control.

---

## 4) Lighting Logic (Auto + Manual)

## 4.1 Automatic Lighting
When `light_manual == False`:
- if any slot is occupied → lights ON
- if lot remains empty for timeout window → lights OFF

This saves power while maintaining usability.

## 4.2 Manual Light Override
Manual commands:
- Telegram: `/light_on`, `/light_off`
- Web API: `/api/lights/on`, `/api/lights/off`

Manual action sets `light_manual = True`, which temporarily blocks automatic lighting logic.

## 4.3 Manual Lock Release
When all slots become free (`free == TOTAL_SLOTS`), manual light lock is released (`light_manual = False`), allowing auto mode to resume.

---

## 5) Multi-Platform Synchronization Logic

The system supports three parallel control planes:
1. Telegram bot
2. Web dashboard
3. Blynk app

To keep them synchronized:
- all commands route through shared actuator functions (`open_gate()`, `close_gate()`)
- status fields are centralized (`sensor_cache`, `gate_state`, `stats`)
- Blynk command transition check (`blynk_gate_cmd_prev`) ignores repeated identical values
- web `/api/data` always reports latest unified state

Result: no platform becomes “out of sync” for long during normal operation.

---

## 6) Statistics Logic

The system tracks:
- `entries`: increment when free slots decrease
- `exits`: increment when free slots increase
- `gates`: increment when a real gate-open action occurs

These stats are displayed on web dashboard and available in Telegram `/stats`.

---

## 7) Network and Fault-Tolerance Logic

## 7.1 WiFi Reliability
- up to 5 connection attempts in STA mode
- if failed, automatic AP fallback (`ESP32_Device`)

## 7.2 Runtime Stability
- short socket timeout prevents web server blocking
- HTTP cloud calls use timeout
- `try/except` around network/hardware calls prevents full crash
- frequent `gc.collect()` reduces heap pressure risk on ESP32

The system prioritizes “keep running” behavior even under partial failures.

---

## 8) Real-Time Scheduling Strategy

Instead of fully blocking calls, the main loop uses time-based checks:
- sensors every 2s
- Telegram every 20s
- Blynk every 5s
- web requests continuously (timeout-driven)

This cooperative scheduling keeps control responsive without requiring full async framework.

---

# List of Smart Features

Below are the implemented smart capabilities of the system.

---

## A. Smart Access and Parking Intelligence

1. **Automatic Vehicle Detection at Entry**  
   Ultrasonic sensing detects arriving vehicles before gate operation.

2. **Availability-Aware Gate Opening**  
   Gate auto-opens only when free slots exist, preventing invalid entry.

3. **Automatic Gate Closing by Timeout**  
   Gate closes when vehicle is no longer detected near entrance.

4. **Real-Time Multi-Slot Occupancy Monitoring**  
   Three IR sensors track slot states continuously.

5. **Live Free-Slot Computation**  
   Dynamic available-slot count is updated in runtime state.

---

## B. Smart Multi-Platform Control

6. **Telegram Remote Command Control**  
   Users can query status and trigger gate/light commands via bot.

7. **Web Dashboard Manual Control**  
   On-device dashboard provides local browser control and monitoring.

8. **Blynk Mobile App Integration**  
   Remote V-pin controls and status indicators enable app-based operation.

9. **Cross-Channel State Synchronization**  
   Shared internal state ensures consistent values across Telegram/Web/Blynk.

10. **Duplicate Command Suppression (Blynk)**  
    Edge-trigger command handling prevents repeated actions from unchanged values.

---

## C. Smart Display and User Feedback

11. **TM1637 Free-Slot Visual Indicator**  
    Instantly shows current parking availability locally.

12. **LCD Status Console**  
    Displays startup state, IP/AP info, slot count, and sensor summaries.

13. **Live Web Monitoring Cards**  
    Dashboard shows gate state, lights state, temp/humidity, distance, and occupancy.

14. **Operational Statistics Reporting**  
    Entries, exits, and gate operation counts available for analysis.

---

## D. Smart Energy and Environment Features

15. **Automatic Parking Light Control**  
    Lights turn on when occupancy exists, off after empty timeout.

16. **Manual Light Override with Safe Reset**  
    Manual mode supports operator control and returns to auto when lot empties.

17. **Environmental Sensing**  
    DHT11 telemetry gives temperature/humidity context for operators.

---

## E. Smart Reliability Features

18. **WiFi Retry + AP Fallback Mode**  
    If router connection fails, system still remains locally accessible.

19. **Exception-Protected Runtime**  
    Network/sensor errors are handled gracefully to avoid loop termination.

20. **Memory-Aware Design with GC**  
    Frequent garbage collection improves long-run ESP32 stability.

21. **Non-Blocking Web Service Behavior**  
    Short socket timeouts keep core logic responsive under varying request load.

---

## F. Smart Expandability Features

22. **Modular Function-Based Control Paths**  
    Gate/light/network logic is organized into reusable function blocks.

23. **Cloud Telemetry Hooks Ready for Scaling**  
    Current architecture is suitable for future MQTT/DB integration.

24. **Upgrade-Friendly Design**  
    Can be extended to `uasyncio`, OTA updates, authentication, and analytics dashboards.
