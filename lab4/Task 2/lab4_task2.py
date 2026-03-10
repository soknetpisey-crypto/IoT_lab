import network, time, ujson
from umqtt.simple import MQTTClient
from machine import Pin, ADC

# ─── Configuration ────────────────────────────────────────────────────────────
SSID, PASSWORD = "Phann Hhome", "@home668"
BROKER, PORT   = "broker.hivemq.com", 1883
CLIENT_ID      = b"esp32_mq5_aupp_01"
TOPIC          = b"/aupp/esp32/mq5"
MQ5_PIN        = 33
WINDOW         = 5

# ─── State ────────────────────────────────────────────────────────────────────
readings = []

# ─── Helpers ──────────────────────────────────────────────────────────────────
def moving_average(val):
    readings.append(val)
    if len(readings) > WINDOW: readings.pop(0)
    return sum(readings) / len(readings)

def classify(avg):
    if avg < 2100:   return "SAFE"
    elif avg < 2600: return "WARNING"
    else:            return "DANGER"

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 20000:
                raise RuntimeError("Wi-Fi timeout")
            time.sleep(0.3)
    print("WiFi OK:", wlan.ifconfig())

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    wifi_connect()

    mq5 = ADC(Pin(MQ5_PIN))
    mq5.atten(ADC.ATTN_11DB)
    mq5.width(ADC.WIDTH_12BIT)

    client = MQTTClient(CLIENT_ID, BROKER, PORT, keepalive=30)

    while True:
        try:
            time.sleep(1)
            client.connect()
            print("MQTT connected")

            while True:
                raw        = mq5.read()
                avg        = moving_average(raw)
                voltage    = (avg / 4095) * 3.3
                risk_level = classify(avg)

                print(f"Raw: {raw} | Avg: {avg:.2f} | {voltage:.2f}V | {risk_level}")

                client.publish(TOPIC, ujson.dumps({
                    "raw":        raw,
                    "avg":        round(avg, 2),
                    "voltage":    round(voltage, 3),
                    "risk_level": risk_level
                }))

                time.sleep(1)

        except OSError as e:
            print("MQTT error:", e)
            try: client.close()
            except: pass
            time.sleep(3)

main()