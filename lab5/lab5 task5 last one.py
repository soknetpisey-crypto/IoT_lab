import network
import socket
from machine import Pin, PWM, I2C
import neopixel
import time
import tcs34725

# ─── WiFi Setup ─────────────────────────────────────
SSID = "Nhin"
PASSWORD = "nhin1979"

# ─── Motor Setup ────────────────────────
in1 = Pin(26, Pin.OUT)
in2 = Pin(27, Pin.OUT)
ena = PWM(Pin(14), freq=1000)
ena.duty(0)

# ─── Sensor Setup ───────────────────────────────────
# FIX 1: Lowered I2C frequency to 100000 to stabilize communication over jumper wires
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
sensor = tcs34725.TCS34725(i2c)

# ─── NeoPixel Setup ─────────────────────────────────
NUM_LEDS = 24
np = neopixel.NeoPixel(Pin(23), NUM_LEDS)

# ─── Global Variables ───────────────────────────────
current_r, current_g, current_b = 0, 0, 0
last_color = "UNKNOWN"
manual_neo = False  # Tracks if the app took control of the ring!

# ─── Helper Functions ───────────────────────────────
def classify_color(r, g, b):
    if r < 800 and g < 800 and b < 800:
        return "UNKNOWN"
    if r > g and r > b:
        return "RED"
    elif g > r and g > b:
        return "GREEN"
    elif b > r and b > g:
        return "BLUE"
    else:
        return "UNKNOWN"

def motor_forward(speed=600):
    in1.value(1)
    in2.value(0)
    ena.duty(speed)

def motor_backward(speed=600):
    in1.value(0)
    in2.value(1)
    ena.duty(speed)

def motor_stop():
    in1.value(0)
    in2.value(0)
    ena.duty(0)

def set_neopixel_auto(color):
    # FIX 2: Dimmed brightness to 30 to prevent voltage drops (brownouts) that crash the sensor
    if color == "RED":
        rgb = (30, 0, 0)
    elif color == "GREEN":
        rgb = (0, 30, 0)
    elif color == "BLUE":
        rgb = (0, 0, 30)
    else:
        rgb = (0, 0, 0) # Turn off if UNKNOWN
        
    for i in range(NUM_LEDS):
        np[i] = rgb
    np.write()

def update_neopixels_manual():
    for i in range(NUM_LEDS):
        np[i] = (current_r, current_g, current_b)
    np.write()

def extract_value(request):
    try:
        val_str = request.split("value=")[1].split(" ")[0].split("&")[0]
        val = int(float(val_str))
        return max(0, min(255, val))
    except:
        return 0

# ─── Connect Wi-Fi ──────────────────────────────────
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Connecting", end="")
while not wlan.isconnected():
    print(".", end="")
    time.sleep(0.5)

print("\nConnected! Your IP is:", wlan.ifconfig()[0])

# ─── Server Setup ───────────────────────────────────
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(1)
server.setblocking(False) 
print("Server running...")

# ─── Main Loop ──────────────────────────────────────
while True:
    # 1. Constantly read the sensor
    try:
        r, g, b, c = sensor.read_raw()
        color = classify_color(r, g, b)
        if color != "UNKNOWN":
            last_color = color
            
        # If the app hasn't taken over, let the sensor drive the lights!
        if not manual_neo:
            set_neopixel_auto(color)
            
    except OSError:
        last_color = "SENSOR_ERROR"

    # 2. Check for MIT App requests
    try:
        cl, addr = server.accept()
        cl.settimeout(1.0) 
        
        try:
            request = cl.recv(1024).decode()
            response = "ESP32 OK"

            # --- Motor Controls ---
            if "GET /forward" in request:
                motor_forward()
                response = "Motor Forward"
                
            elif "GET /backward" in request:
                motor_backward()
                response = "Motor Backward"
                
            elif "GET /stop" in request:
                motor_stop()
                response = "Motor Stop"

            # --- NeoPixel Mode Controls ---
            elif "GET /auto" in request:
                manual_neo = False
                response = "Auto mode enabled"

            # --- Slider Controls ---
            elif "GET /red" in request:
                manual_neo = True
                current_r = extract_value(request)
                update_neopixels_manual()
                response = "Red: " + str(current_r)
                
            elif "GET /green" in request:
                manual_neo = True
                current_g = extract_value(request)
                update_neopixels_manual()
                response = "Green: " + str(current_g)
                
            elif "GET /blue" in request:
                manual_neo = True
                current_b = extract_value(request)
                update_neopixels_manual()
                response = "Blue: " + str(current_b)

            # --- Color Sensor Endpoint ---
            elif "GET /color" in request:
                response = "COLOR:" + last_color

            # Send HTTP response
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n")
            cl.send(response)
            
        except Exception as e:
            pass 
        finally:
            cl.close()

    except OSError:
        pass
    
    # FIX 3: Increased delay to 0.2s to give the sensor integration time and stabilize the loop
    time.sleep(0.2)