from machine import Pin, PWM
from time import sleep
import network
import urequests as requests

# ---------- CONFIG ----------
WIFI_SSID = "Robotic WIFI"
WIFI_PASS = "rbtWIFI@2025"

BLYNK_TOKEN = "mQvTmfiQvPpvOIYftI-ghXJN65vZp_jc"
BLYNK_API   = "http://blynk.cloud/external/api"

SERVO_PIN = 13
IR_PIN = 12

OPEN_ANGLE = 90
CLOSE_ANGLE = 0
DELAY_TIME = 3

# ---------- HARDWARE ----------
servo = PWM(Pin(SERVO_PIN), freq=50)
ir = Pin(IR_PIN, Pin.IN)

# ---------- WIFI ----------
def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASS)

    print("Connecting to WiFi...")
    while not wifi.isconnected():
        sleep(1)
    print("WiFi connected!")

connect_wifi()

# ---------- SERVO FUNCTION ----------
def angle_to_duty(angle):
    min_duty = 26
    max_duty = 128

    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180

    return int(min_duty + (angle / 180) * (max_duty - min_duty))

def set_servo(angle):
    duty = angle_to_duty(angle)
    servo.duty(duty)
    print("Servo angle:", angle)

# ---------- BLYNK READ FUNCTION ----------
def read_blynk_v0():
    url = f"{BLYNK_API}/get?token={BLYNK_TOKEN}&V0"
    try:
        r = requests.get(url)
        value = r.text.strip()
        r.close()

        # Clean response like ["1"]
        if value.startswith('['):
            value = value[1:-1]
        value = value.replace('"', '')

        return int(value)
    except:
        return None

# ---------- INITIAL STATE ----------
set_servo(CLOSE_ANGLE)
print("System Ready...")

# ---------- MAIN LOOP ----------
while True:
    mode = read_blynk_v0()

    if mode == 1:
        # AUTOMATIC MODE
        print("Automatic IR Mode ON")

        if ir.value() == 0:
            print("Obstacle detected!")
            set_servo(OPEN_ANGLE)
            sleep(DELAY_TIME)
            set_servo(CLOSE_ANGLE)

            # Prevent repeated trigger
            while ir.value() == 0:
                sleep(0.2)

    elif mode == 0:
        # MANUAL MODE (Override)
        print("Manual Mode Active - IR Ignored")
        set_servo(CLOSE_ANGLE)

    else:
        print("Reading V0...")

    sleep(0.5)
