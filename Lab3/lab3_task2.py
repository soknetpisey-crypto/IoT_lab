from machine import Pin, PWM
from time import sleep
import network
import urequests as requests

# ---------- CONFIG ----------
WIFI_SSID = "Robotic WIFI"
WIFI_PASS = "rbtWIFI@2025"

BLYNK_TOKEN = "mQvTmfiQvPpvOIYftI-ghXJN65vZp_jc"
BLYNK_API   = "http://blynk.cloud/external/api"

SERVO_PIN = 13   # the pin your servo signal line is connected to
POLL_INTERVAL = 0.2   

# ---------- Setup ----------
servo = PWM(Pin(SERVO_PIN), freq=50)   # 50 Hz for hobby servo

def connect_wifi(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        t = 0
        while not wlan.isconnected() and t < timeout:
            sleep(1)
            t += 1
    return wlan.isconnected()

def angle_to_duty(angle):
    # Map 0..180 degrees to duty values appropriate for MicroPython on ESP8266 (0-1023)
    # These endpoints (26..128) work for many servos — adjust if your servo needs different range.
    min_duty = 26
    max_duty = 128
    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180
    return int(min_duty + (angle / 180.0) * (max_duty - min_duty))

def parse_blynk_response_text(text):
    # Blynk often returns ["123"] or [123] or plain 123. This tries to extract a numeric value robustly.
    t = text.strip()
    # remove surrounding brackets if present
    if t.startswith('[') and t.endswith(']'):
        t = t[1:-1].strip()
    # remove surrounding quotes
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
        t = t[1:-1]
    # try numeric conversion
    try:
        if '.' in t:
            return float(t)
        return int(t)
    except:
        # fallback: remove non-numeric chars except dot and minus
        s = ''.join(ch for ch in t if ch.isdigit() or ch in '.-')
        try:
            if '.' in s:
                return float(s)
            return int(s)
        except:
            return None

def read_blynk_v5():
    # Try common GET formats used by different Blynk setups
    urls = [
        "{}/get?token={}&pin=V5".format(BLYNK_API, BLYNK_TOKEN),
        "{}/get?token={}&V5".format(BLYNK_API, BLYNK_TOKEN),
        "{}/get?token={}&vPin=V5".format(BLYNK_API, BLYNK_TOKEN),
        "{}/get?token={}&v5".format(BLYNK_API, BLYNK_TOKEN),
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            text = r.text
            r.close()
            val = parse_blynk_response_text(text)
            if val is not None:
                return val
        except Exception:
            # Try next URL option
            pass
    return None

# ---------- Main ----------
print("Connecting to Wi-Fi...")
if not connect_wifi(WIFI_SSID, WIFI_PASS):
    print("Wi-Fi connection failed. Check credentials and network.")
else:
    print("Wi-Fi connected.")

last_angle = None

while True:
    val = read_blynk_v5()
    if val is None:
        # Could not read value; you can log or wait and retry
        # Keep previous position (or optionally center)
        # print("No value from Blynk (try check V5 slider and internet).")
        pass
    else:
        # val might be in 0..180, or 0..1023 (typical slider ranges).
        angle = int(val)
        if angle > 180:
            # assume 0-1023 slider, map to 0-180
            angle = int((angle / 1023.0) * 180.0)
        # only update if changed significantly
        if last_angle is None or abs(angle - last_angle) >= 1:
            duty = angle_to_duty(angle)
            servo.duty(duty)
            last_angle = angle
            # print feedback for debugging
            print("angle:", angle, "duty:", duty)
    sleep(POLL_INTERVAL)