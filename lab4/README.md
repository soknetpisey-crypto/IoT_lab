# 🌡️ Lab 4: Multi-Sensor IoT Monitoring with Grafana Dashboard

> **Platform:** ESP32 + MicroPython  
> **Tools:** Thonny · Node-RED · InfluxDB · Grafana

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Learning Outcomes](#-learning-outcomes)
- [Equipment](#-equipment)
- [System Architecture](#️-system-architecture)
- [Task 1 — Gas Filtering (Moving Average)](#-task-1--gas-filtering-moving-average)
- [Task 2 — Gas Risk Classification](#️-task-2--gas-risk-classification)
- [Task 3 — Fever Detection Logic](#️-task-3--fever-detection-logic)
- [Task 4 — Pressure & Altitude Monitoring (Grafana)](#-task-4--pressure--altitude-monitoring-grafana)
- [Wiring](#-wiring)
- [MQTT Topics](#-mqtt-topics)
- [Node-RED Flow](#-node-red-flow)
- [InfluxDB Queries](#️-influxdb-queries)
- [Setup Guide](#️-setup-guide)
- [Project Structure](#-project-structure)

---

## 🔍 Overview

This lab guides you through building a **multi-sensor IoT monitoring system** using an **ESP32** running **MicroPython**. Edge-side data processing is performed directly on the ESP32 before publishing sensor readings via MQTT to Node-RED, which stores them in InfluxDB and visualizes them in a Grafana dashboard.

### Sensors Used

| Sensor | Interface | Data Collected |
|---|---|---|
| **MLX90614** | I2C (IR Thermometer) | Ambient temp, body temp, fever flag |
| **MQ-5** | Analog (ADC) | Raw ADC, moving average, voltage, risk level |
| **BMP280** | I2C (Barometric) | Room temp, pressure, altitude |
| **DS3231** | I2C (RTC) | Unix epoch timestamp |

---

## 🎯 Learning Outcomes

By completing this lab, you will be able to:

1. Integrate multiple I2C and analog sensors with an ESP32
2. Implement a moving average filter to smooth noisy sensor signals
3. Build rule-based classification logic at the edge
4. Structure JSON payloads for IoT data transmission
5. Store time-series data in InfluxDB via Node-RED
6. Design and configure multi-panel dashboards in Grafana

---

## 🔧 Equipment

| Component | Description | Interface |
|---|---|---|
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
┌─────────────────────────────────────────────────────────────┐
│                            ESP32                            │
│                                                             │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  │
│  │  MQ-5    │  │ MLX90614  │  │  BMP280  │  │  DS3231  │  │
│  │ (GPIO33) │  │  (I2C)    │  │  (I2C)   │  │  (I2C)   │  │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │             │              │        │
│       ▼              ▼             ▼              ▼        │
│  ┌────────────────────────────────────────────────────┐    │
│  │               Edge Processing Logic                │    │
│  │  • Moving Average (Window = 5)                     │    │
│  │  • Risk Classification (SAFE / WARNING / DANGER)   │    │
│  │  • Fever Detection (threshold ≥ 32.5 °C)           │    │
│  │  • Unix Epoch Conversion                           │    │
│  └──────────────────────┬─────────────────────────────┘    │
└─────────────────────────┼───────────────────────────────────┘
                          │ MQTT → broker.hivemq.com:1883
                          ▼
             ┌────────────────────────┐
             │        Node-RED        │
             │  • Parse JSON payload  │
             │  • Format for InfluxDB │
             └────────────┬───────────┘
                          │ HTTP Write API
                          ▼
             ┌────────────────────────┐
             │        InfluxDB        │
             │  Database: aupp_lab    │
             │  Measurements:         │
             │    • mq5               │
             │    • mlx90614          │
             │    • bmp280            │
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

### Objective
Read the MQ-5 sensor using the ESP32's 12-bit ADC (range: 0–4095), smooth the signal using a **sliding window moving average** (window size = 5), and publish the averaged value to Node-RED via MQTT.

### Implementation

```python
WINDOW = 5
readings = []

def moving_average(val):
    readings.append(val)
    if len(readings) > WINDOW:
        readings.pop(0)
    return sum(readings) / len(readings)
```

### Expected Serial Output

```
[MQ5]  Raw: 2657 | Avg: 2678.80 | 2.16V | DANGER(3)
[MQ5]  Raw: 2601 | Avg: 2645.20 | 2.13V | DANGER(3)
[MQ5]  Raw: 2544 | Avg: 2607.40 | 2.10V | DANGER(3)
```

---

## ⚠️ Task 2 — Gas Risk Classification

### Classification Rules

| ADC Average | Risk Level | `risk_num` |
|---|---|---|
| `< 2100` | ✅ SAFE | `1` |
| `2100 – 2599` | ⚠️ WARNING | `2` |
| `≥ 2600` | 🚨 DANGER | `3` |

### Implementation

```python
def classify(avg):
    if avg < 2100:
        return "SAFE", 1
    elif avg < 2600:
        return "WARNING", 2
    else:
        return "DANGER", 3
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

> **Why `risk_num`?**  
> Sending an integer (`1`, `2`, or `3`) instead of a string allows InfluxDB to store it as a numeric field, enabling Grafana to apply colour-coded value mappings.

---

## 🌡️ Task 3 — Fever Detection Logic

### Detection Rule

| Condition | `fever_flag` | Meaning |
|---|---|---|
| `body_temp >= 32.5 °C` | `1` | 🔴 Fever Detected |
| `body_temp < 32.5 °C` | `0` | 🟢 Normal |

### Implementation

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

### Dashboard Panels

| # | Panel Title | Measurement | Field | Visualization |
|---|---|---|---|---|
| 1 | Gas Average | `mq5` | `avg` | Time Series |
| 2 | Risk Level | `mq5` | `risk_num` | Stat |
| 3 | Body Temperature Gauge | `mlx90614` | `body_temp` | Gauge |
| 4 | Pressure Graph | `bmp280` | `pressure` | Time Series |
| 5 | Altitude Graph | `bmp280` | `altitude` | Time Series |
| 6 | Pressure (hPa) | `bmp280` | `pressure` | Stat |
| 7 | Altitude (m) | `bmp280` | `altitude` | Stat |
| 8 | DS3231 Timestamp | `bmp280` | `epoch` | Stat |

### InfluxQL Queries

```sql
-- Panel 1: Gas Average (time series)
SELECT mean("avg") FROM "mq5"
WHERE $timeFilter GROUP BY time($__interval) fill(null)

-- Panel 2: Risk Level (latest value)
SELECT last("risk_num") FROM "mq5" WHERE $timeFilter

-- Panel 3: Body Temperature (latest value)
SELECT last("body_temp") FROM "mlx90614" WHERE $timeFilter

-- Panel 4: Pressure Graph (time series)
SELECT mean("pressure") FROM "bmp280"
WHERE $timeFilter GROUP BY time($__interval) fill(null)

-- Panel 5: Altitude Graph (time series)
SELECT mean("altitude") FROM "bmp280"
WHERE $timeFilter GROUP BY time($__interval) fill(null)

-- Panel 6: Pressure hPa (latest value)
SELECT last("pressure") FROM "bmp280" WHERE $timeFilter

-- Panel 7: Altitude Meters (latest value)
SELECT last("altitude") FROM "bmp280" WHERE $timeFilter

-- Panel 8: DS3231 Timestamp (latest value)
SELECT last("epoch") FROM "bmp280" WHERE $timeFilter
```

### Risk Level Value Mappings (Panel 2)

| Value | Display | Colour |
|---|---|---|
| `1` | ✅ SAFE | 🟢 Green |
| `2` | ⚠️ WARNING | 🟡 Yellow |
| `3` | 🚨 DANGER | 🔴 Red |

---

## 🔌 Wiring

### I2C Bus — BMP280, DS3231, MLX90614

| ESP32 Pin | Sensor Pin | Wire Colour |
|---|---|---|
| GPIO 21 | SDA | Blue |
| GPIO 22 | SCL | Yellow |
| 3.3 V | VCC | Red |
| GND | GND | Black |
|
### MQ-5 Gas Sensor

| ESP32 Pin | Sensor Pin | Wire Colour |
|---|---|---|
| GPIO 33 | AO (Analog Out) | Green |
| 5 V | VCC | Red |
| GND | GND | Black |

> ⚠️ The MQ-5 requires **5 V** for the heater element; the analogue output signal is safe to read directly on GPIO 33.

---

## 📡 MQTT Topics

| Topic | Sensor | Published Fields |
|---|---|---|
| `/aupp/esp32/mq5` | MQ-5 | `raw`, `avg`, `voltage`, `risk_num` |
| `/aupp/esp32/mlx90614` | MLX90614 | `ambient_temp`, `body_temp`, `fever_flag` |
| `/aupp/esp32/bmp280` | BMP280 + DS3231 | `temperature`, `pressure`, `altitude`, `epoch` |

| Setting | Value |
|---|---|
| Broker | `broker.hivemq.com` |
| Port | `1883` |
| Publish interval | Every `2 seconds` |

---

## 🔄 Node-RED Flow

Three independent pipelines: **MQTT In → Function → InfluxDB Out**

### Function Node — MQ-5

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

### Function Node — MLX90614

```javascript
msg.measurement = "mlx90614";
msg.payload = {
    ambient_temp: Number(msg.payload.ambient_temp),
    body_temp:    Number(msg.payload.body_temp),
    fever_flag:   Number(msg.payload.fever_flag)
};
return msg;
```

### Function Node — BMP280

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
# Open the InfluxDB CLI
influx

# Select the database
USE aupp_lab

# List all measurements
SHOW MEASUREMENTS

# View the 5 most recent records per sensor
SELECT * FROM mq5      ORDER BY time DESC LIMIT 5
SELECT * FROM mlx90614 ORDER BY time DESC LIMIT 5
SELECT * FROM bmp280   ORDER BY time DESC LIMIT 5

# Count total stored records per sensor
SELECT count(avg)       FROM mq5
SELECT count(body_temp) FROM mlx90614
SELECT count(pressure)  FROM bmp280
```

---

## ⚙️ Setup Guide

### Step 1 — Flash MicroPython to the ESP32

```bash
esptool.py --port COM3 erase_flash
esptool.py --port COM3 write_flash -z 0x1000 micropython.bin
```

### Step 2 — Upload Libraries via Thonny

Upload the following files to the ESP32 filesystem:

```
bmp280.py
d3231.py
mlx90614.py
umqtt/simple.py
```

### Step 3 — Configure Wi-Fi Credentials

Edit `main.py`:

```python
SSID     = "YourWiFiName"
PASSWORD = "YourWiFiPassword"
```

### Step 4 — Set DS3231 Time (First Run Only)

```python
rtc.set_time(2026, 3, 9, 23, 0, 0)
# ⚠️ Comment out this line after the first successful run.
```

### Step 5 — Run `main.py` in Thonny

Click ▶️ **Run** and verify the serial output:

```
WiFi OK: ('192.168.x.x', ...)
MQTT connected → broker.hivemq.com
[MQ5]  Raw: 2657 | Avg: 2678.80 | 2.16V | DANGER(3)
[MLX]  Ambient: 32.37°C | Body: 32.27°C | Fever: 0
[BMP]  Temp: 32.27°C | Pressure: 1012.32hPa | Altitude: -4.5m | Epoch: 1741561839000
```

### Step 6 — Deploy the Node-RED Flow

1. Import `flows.json` into Node-RED.
2. Set the MQTT broker to `broker.hivemq.com:1883`.
3. Connect each pipeline: **MQTT In → Function → InfluxDB Out**.
4. Click **Deploy**.

### Step 7 — Configure Grafana

1. Add a data source: **InfluxDB** → `http://localhost:8086`
2. Set database to `aupp_lab` and query language to `InfluxQL`.
3. Create a new dashboard and add **8 panels** using the queries listed in [Task 4](#-task-4--pressure--altitude-monitoring-grafana).

---

## 📁 Project Structure

```
lab4/
├── main.py          # ESP32 firmware (MicroPython)
├── bmp280.py        # BMP280 pressure sensor driver
├── ds3231.py        # DS3231 RTC driver
├── mlx90614.py      # MLX90614 IR temperature driver
├── umqtt/
│   └── simple.py    # Lightweight MQTT client
├── flows.json       # Node-RED flow export
└── README.md        # This file
```