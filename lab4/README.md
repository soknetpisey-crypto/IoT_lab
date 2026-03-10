# 🌡️ LAB 4: Multi-Sensor IoT Monitoring with Grafana Dashboard

> **Platform:** ESP32 + MicroPython
> **Tools:** Thonny | Node-RED | InfluxDB | Grafana

---

## 📋 Table of Contents
- [Overview](#overview)
- [Learning Outcomes](#learning-outcomes)
- [Equipment](#equipment)
- [System Architecture](#system-architecture)
- [Task 1 — Gas Filtering (Moving Average)](#task-1--gas-filtering-moving-average)
- [Task 2 — Gas Risk Classification](#task-2--gas-risk-classification)
- [Task 3 — Fever Detection Logic](#task-3--fever-detection-logic)
- [Task 4 — Pressure & Altitude Monitoring (Grafana)](#task-4--pressure--altitude-monitoring-grafana)
- [Wiring](#wiring)
- [MQTT Topics](#mqtt-topics)
- [Node-RED Flow](#node-red-flow)
- [InfluxDB Queries](#influxdb-queries)
- [Grafana Dashboard](#grafana-dashboard)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)

---

## 🔍 Overview

In this lab, a multi-sensor IoT monitoring system is designed and implemented using
**ESP32** and **MicroPython**. The system integrates:

| Sensor | Type | Data |
|--------|------|------|
| **MLX90614** | I2C IR Thermometer | Ambient & Body Temperature, Fever Flag |
| **MQ-5** | Analog Gas Sensor | Raw ADC, Moving Average, Voltage, Risk Level |
| **BMP280** | I2C Barometric Sensor | Room Temperature, Pressure, Altitude |
| **DS3231** | I2C Real-Time Clock | Timestamp (epoch) |

Edge logic processing is implemented **on the ESP32 before sending** to Node-RED,
where data is stored in **InfluxDB** and visualized in **Grafana**.

---

## 🎯 Learning Outcomes

| # | Outcome |
|---|---------|
| 1 | Integrate multiple I2C and analog sensors with ESP32 |
| 2 | Implement moving average filtering for noisy sensor signals |
| 3 | Create rule-based classification logic at the edge |
| 4 | Structure JSON packets for IoT transmission |
| 5 | Store time-series data in InfluxDB |
| 6 | Design dashboards using Grafana |

---

## 🔧 Equipment

| Component | Description | Interface |
|-----------|-------------|-----------|
| ESP32 DevKit | Main microcontroller | — |
| MQ-5 | Gas sensor (LPG, Methane, Propane) | Analog (ADC) |
| MLX90614 | Contactless IR temperature sensor | I2C |
| BMP280 | Barometric pressure & altitude sensor | I2C |
| DS3231 | Real-time clock (RTC) module | I2C |
| Jumper Wires | Connections | — |
| Breadboard | Prototyping | — |

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         ESP32                                │
│                                                              │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐   │
│  │  MQ-5    │  │ MLX90614  │  │  BMP280  │  │  DS3231  │   │
│  │ (GPIO33) │  │  (I2C)    │  │  (I2C)   │  │  (I2C)   │   │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │             │              │         │
│       ▼              ▼             ▼              ▼         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Edge Processing Logic                  │    │
│  │  • Moving Average (Window=5)                        │    │
│  │  • Risk Classification (SAFE/WARNING/DANGER)        │    │
│  │  • Fever Detection (threshold 32.5°C)               │    │
│  │  • Unix Epoch Conversion                            │    │
│  └───────────────────────┬─────────────────────────────┘    │
└──────────────────────────┼─────────────────────────────────-┘
                           │ MQTT (HiveMQ)
                           ▼
              ┌────────────────────────┐
              │        Node-RED        │
              │  • Parse JSON payload  │
              │  • Format for InfluxDB │
              └────────────┬───────────┘
                           │ HTTP Write
                           ▼
              ┌────────────────────────┐
              │        InfluxDB        │
              │   Database: aupp_lab   │
              │  • mq5                 │
              │  • mlx90614            │
              │  • bmp280              │
              └────────────┬───────────┘
                           │ InfluxQL
                           ▼
              ┌────────────────────────┐
              │        Grafana         │
              │   8-Panel Dashboard    │
              └────────────────────────┘
```

---

## 📊 Task 1 — Gas Filtering (Moving Average)

### Description
- Read MQ-5 using ESP32 ADC (12-bit resolution, 0–4095)
- Store the **last 5 readings** in a sliding window
- Compute **moving average** from stored readings
- Print both raw and averaged values to Serial Monitor
- Send averaged value to Node-RED via MQTT

### Logic
```python
WINDOW = 5
readings = []

def moving_average(val):
    readings.append(val)
    if len(readings) > WINDOW:
        readings.pop(0)
    return sum(readings) / len(readings)
```

### Serial Output Evidence
```
[MQ5]  Raw: 2657 | Avg: 2678.80 | 2.16V | DANGER(3)
[MQ5]  Raw: 2601 | Avg: 2645.20 | 2.13V | DANGER(3)
[MQ5]  Raw: 2544 | Avg: 2607.40 | 2.10V | DANGER(3)
```

---

## ⚠️ Task 2 — Gas Risk Classification

### Classification Rules

| ADC Average Value | Risk Level | risk_num |
| ----------------- | ---------- | -------- |
| < 2100            | ✅ SAFE     | 1        |
| 2100 – 2599       | ⚠️ WARNING | 2        |
| ≥ 2600            | 🚨 DANGER  | 3        |

### Logic
```python
def classify(avg):
    if avg < 2100:   return "SAFE",    1
    elif avg < 2600: return "WARNING", 2
    else:            return "DANGER",  3
```

### MQTT Payload
```json
{
  "raw": 2657,
  "avg": 2678.80,
  "voltage": 2.157,
  "risk_num": 3
}
```

> **Note:** `risk_num` is sent as an integer (1/2/3) instead of a string
> so InfluxDB can store it and Grafana can display it with color mappings.

---

## 🌡️ Task 3 — Fever Detection Logic

### Detection Rule

| Condition | fever_flag | Meaning |
|-----------|------------|---------|
| `body_temp >= 32.5°C` | `1` | 🔴 Fever Detected |
| `body_temp < 32.5°C` | `0` | 🟢 Normal |

### Logic
```python
FEVER_THRESHOLD = 32.5

def fever_detect(body_temp):
    return 1 if body_temp >= FEVER_THRESHOLD else 0
```

### MQTT Payload
```json
{
  "ambient_temp": 32.37,
  "body_temp": 32.27,
  "fever_flag": 0
}
```

---

## 📈 Task 4 — Pressure & Altitude Monitoring (Grafana)

### Grafana Dashboard Panels

| #   | Panel Title            | Measurement | Field       | Type        |
| --- | ---------------------- | ----------- | ----------- | ----------- |
| 1   | Gas Average            | `mq5`       | `avg`       | Time Series |
| 2   | Risk Level             | `mq5`       | `risk_num`  | Stat        |
| 3   | Body Temperature Gauge | `mlx90614`  | `body_temp` | Gauge       |
| 4   | Pressure Graph         | `bmp280`    | `pressure`  | Time Series |
| 5   | Altitude Graph         | `bmp280`    | `altitude`  | Time Series |
| 6   | Pressure hPa           | `bmp280`    | `pressure`  | Stat        |
| 7   | Altitude Meters        | `bmp280`    | `altitude`  | Stat        |
| 8   | DS3231 Timestamp       | `bmp280`    | `epoch`     | Stat        |

### InfluxQL Queries
```sql
-- Panel 1: Gas Average
SELECT mean("avg") FROM "mq5" WHERE $timeFilter GROUP BY time($__interval) fill(null)

-- Panel 2: Risk Level
SELECT last("risk_num") FROM "mq5" WHERE $timeFilter

-- Panel 3: Body Temperature
SELECT last("body_temp") FROM "mlx90614" WHERE $timeFilter

-- Panel 4: Pressure Graph
SELECT mean("pressure") FROM "bmp280" WHERE $timeFilter GROUP BY time($__interval) fill(null)

-- Panel 5: Altitude Graph
SELECT mean("altitude") FROM "bmp280" WHERE $timeFilter GROUP BY time($__interval) fill(null)

-- Panel 6: Pressure hPa
SELECT last("pressure") FROM "bmp280" WHERE $timeFilter

-- Panel 7: Altitude Meters
SELECT last("altitude") FROM "bmp280" WHERE $timeFilter

-- Panel 8: DS3231 Timestamp
SELECT last("epoch") FROM "bmp280" WHERE $timeFilter
```

### Risk Level Value Mappings
| Value | Display Text | Color |
|-------|-------------|-------|
| `1` | ✅ SAFE | 🟢 Green |
| `2` | ⚠️ WARNING | 🟡 Yellow |
| `3` | 🚨 DANGER | 🔴 Red |

---

## 🔌 Wiring

### I2C Bus (BMP280 + DS3231 + MLX90614)
| ESP32 Pin | Sensor Pin | Color |
|-----------|------------|-------|
| GPIO 21 | SDA | Blue |
| GPIO 22 | SCL | Yellow |
| 3.3V | VCC | Red |
| GND | GND | Black |

### MQ-5 Gas Sensor
| ESP32 Pin | Sensor Pin | Color |
|-----------|------------|-------|
| GPIO 33 | AO (Analog Out) | Green |
| 5V | VCC | Red |
| GND | GND | Black |

---

## 📡 MQTT Topics

| Topic                  | Sensor          | Published Fields                               |
| ---------------------- | --------------- | ---------------------------------------------- |
| `/aupp/esp32/mq5`      | MQ-5            | `raw`, `avg`, `voltage`, `risk_num`            |
| `/aupp/esp32/mlx90614` | MLX90614        | `ambient_temp`, `body_temp`, `fever_flag`      |
| `/aupp/esp32/bmp280`   | BMP280 + DS3231 | `temperature`, `pressure`, `altitude`, `epoch` |

- **Broker:** `broker.hivemq.com`
- **Port:** `1883`
- **Interval:** Every `2 seconds`

---

## 🔄 Node-RED Flow

Three MQTT-in flows, each connected to a Function node then InfluxDB out:

### Function — MQ-5
```javascript
msg.measurement = "mq5";
msg.payload = {
    raw:      Number(msg.payload.raw),
    avg:      Number(msg.payload.avg),
    voltage:  Number(msg.payload.voltage),
    risk_num: Number(msg.payload.risk_num)
};
return msg;
```

### Function — MLX90614
```javascript
msg.measurement = "mlx90614";
msg.payload = {
    ambient_temp: Number(msg.payload.ambient_temp),
    body_temp:    Number(msg.payload.body_temp),
    fever_flag:   Number(msg.payload.fever_flag)
};
return msg;
```

### Function — BMP280
```javascript
msg.measurement = "bmp280";
msg.payload = {
    temperature: Number(msg.payload.temperature),
    pressure:    Number(msg.payload.pressure),
    altitude:    Number(msg.payload.altitude),
    epoch:       Number(msg.payload.epoch)
};
return msg;
```

---

## 🗄️ InfluxDB Queries

```bash
# Open InfluxDB shell
influx

# Select database
USE aupp_lab

# Show all measurements
SHOW MEASUREMENTS

# View latest 5 records from each sensor
SELECT * FROM mq5      ORDER BY time DESC LIMIT 5
SELECT * FROM mlx90614 ORDER BY time DESC LIMIT 5
SELECT * FROM bmp280   ORDER BY time DESC LIMIT 5

# Count total records
SELECT count(avg)       FROM mq5
SELECT count(body_temp) FROM mlx90614
SELECT count(pressure)  FROM bmp280
```

---

## ⚙️ Setup Guide

### Step 1 — Flash MicroPython to ESP32
```bash
esptool.py --port COM3 erase_flash
esptool.py --port COM3 write_flash -z 0x1000 micropython.bin
```

### Step 2 — Upload Libraries via Thonny
```
bmp280.py
ds3231.py
mlx90614.py
umqtt/simple.py
```

### Step 3 — Configure WiFi in main.py
```python
SSID, PASSWORD = "YourWiFi", "YourPassword"
```

### Step 4 — Set DS3231 Time (first run only)
```python
rtc.set_time(2026, 3, 9, 23, 0, 0)
# ⚠️ Comment out after first successful run
```

### Step 5 — Run main.py in Thonny
Click ▶️ Run and verify serial output:
```
WiFi OK: ('192.168.x.x', ...)
MQTT connected → broker.hivemq.com
[MQ5]  Raw: 2657 | Avg: 2678.80 | 2.16V | DANGER(3)
[MLX]  Ambient: 32.37°C | Body: 32.27°C | Fever: 0
[BMP]  Temp: 32.27°C | Pressure: 1012.32hPa | Altitude: -4.5m | Epoch: 1741561839000
```

### Step 6 — Deploy Node-RED Flow
- Import 3 MQTT-in flows
- Set server: `broker.hivemq.com:1883`
- Connect each to Function → InfluxDB out
- Click Deploy

### Step 7 — Configure Grafana
- Data source: InfluxDB → `http://localhost:8086`
- Database: `aupp_lab`
- Query language: `InfluxQL`
- Add 8 panels using queries from Task 4

---

## 📁 Project Structure

```
lab4/
├── main.py              # Main ESP32 firmware (MicroPython)
├── ds3231.py            # DS3231 RTC driver
├── bmp280.py            # BMP280 pressure sensor driver
├── mlx90614.py          # MLX90614 IR temperature driver
├── umqtt/
│   └── simple.py        # Lightweight MQTT client
├── flows.json           # Node-RED flow export
└── README.md            # This file
```



