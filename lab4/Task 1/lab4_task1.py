import network, time, ujson
from umqtt.simple import MQTTClient
from machine import Pin, ADC

SSID, PASSWORD = "Robotic WIFI", "rbtWIFI@2025"
BROKER, PORT   = "test.mosquitto.org", 1883
TOPIC          = b"/aupp/esp32/mq5"
WINDOW         = 5
readings       = []

def moving_average(val):
    readings.append(val)
    if len(readings) > WINDOW: readings.pop(0)
    return sum(readings) / len(readings)

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

def main():
    wifi_connect()
    mq5 = ADC(Pin(33))
    mq5.atten(ADC.ATTN_11DB)
    mq5.width(ADC.WIDTH_12BIT)
    client = MQTTClient(b"esp32_mq5_1", BROKER, PORT, keepalive=30)

    while True:
        try:
            client.connect()
            while True:
                raw = mq5.read()
                avg = moving_average(raw)
                voltage = (avg / 4095) * 3.3
                print(f"Raw: {raw} | Avg: {avg:.2f} | Voltage: {voltage:.2f}V")
                client.publish(TOPIC, ujson.dumps({
                    "raw": raw, "avg": round(avg, 2), "voltage": round(voltage, 3)
                }))
                time.sleep(1)
        except OSError:
            try: client.close()
            except: pass
            time.sleep(3)

main()