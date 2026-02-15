import network
import time
import urequests as requests
from machine import Pin

# ---------- CONFIG ----------
WIFI_SSID = "Robotic WIFI"
WIFI_PASS = "rbtWIFI@2025"

BLYNK_TOKEN = "mQvTmfiQvPpvOIYftI-ghXJN65vZp_jc"
BLYNK_API   = "http://blynk.cloud/external/api"

# ---------- HARDWARE ----------
ir = Pin(12, Pin.IN)   # IR sensor on GPIO12

# ---------- WIFI ----------
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)
print("WiFi connected!")

# ---------- BLYNK FUNCTION ----------
def blynk_write(pin, value):
    url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&{pin}={value}"
    r = requests.get(url)
    r.close()

# ---------- MAIN LOOP ----------
print("Running IR sensor with Blynk...")

while True:
    value = ir.value()

    if value == 0:
        print("Obstacle detected")
        blynk_write("V3", 1)   # Detected LED ON
        blynk_write("V4", 0)   # Not detected LED OFF
    else:
        print("No obstacle")
        blynk_write("V3", 0)   # Detected LED OFF
        blynk_write("V4", 1)   # Not detected LED ON

    time.sleep(0.5)
