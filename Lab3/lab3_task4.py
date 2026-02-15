import network
import time
import urequests as requests
from machine import Pin
from tm1637 import TM1637

# ---------- CONFIG ----------
WIFI_SSID = "Robotic WIFI"
WIFI_PASS = "rbtWIFI@2025"

BLYNK_TOKEN = "mQvTmfiQvPpvOIYftI-ghXJN65vZp_jc"
BLYNK_API   = "http://blynk.cloud/external/api"

# ---------- HARDWARE ----------
ir = Pin(12, Pin.IN)   # IR sensor on GPIO12
tm = TM1637(clk_pin=17, dio_pin=16, brightness=5)  # TM1637 display

# ---------- WIFI ----------
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)
print("WiFi connected!")

# ---------- COUNTER VARIABLES ----------
detection_count = 0
previous_ir_state = 1  # Track previous state to detect transitions

# ---------- BLYNK FUNCTION ----------
def blynk_write(pin, value):
    url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&{pin}={value}"
    try:
        r = requests.get(url)
        r.close()
    except Exception as e:
        print(f"Blynk write error: {e}")

# ---------- DISPLAY FUNCTIONS ----------
def update_display(count):
    """Update TM1637 display with the count value"""
    tm.show_digit(count)
    print(f"Display updated: {count}")

def update_blynk_counter(count):
    """Update Blynk numeric display (V6) with the count"""
    blynk_write("V6", count)
    print(f"Blynk V6 updated: {count}")

# ---------- MAIN LOOP ----------
print("Running IR sensor with TM1637 Display and Blynk...")
print("Detection counter initialized to 0")
update_display(detection_count)
update_blynk_counter(detection_count)

while True:
    ir_value = ir.value()
    
    # Detect transition from 0 (obstacle detected) to 1 (no obstacle)
    # This counts each detection event once
    if ir_value == 1 and previous_ir_state == 0:
        detection_count += 1
        print(f"Obstacle detected! Total detections: {detection_count}")
        
        # Update both TM1637 display and Blynk
        update_display(detection_count)
        update_blynk_counter(detection_count)
        
        # Optional: Visual feedback on detection
        blynk_write("V3", 1)   # Detected LED ON
        blynk_write("V4", 0)   # Not detected LED OFF
        time.sleep(0.2)
        blynk_write("V3", 0)   # Detected LED OFF
        blynk_write("V4", 1)   # Not detected LED ON
    
    previous_ir_state = ir_value
    time.sleep(0.1)