from machine import Pin, SoftI2C, PWM
import time
import tcs34725

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
sensor = tcs34725.TCS34725(i2c)

# Motor pins
in1 = Pin(26, Pin.OUT)
in2 = Pin(27, Pin.OUT)
ena = PWM(Pin(14), freq=1000)

def classify_color(r, g, b):
    if r > g and r > b:
        return "RED"
    elif g > r and g > b:
        return "GREEN"
    elif b > r and b > g:
        return "BLUE"
    else:
        return "UNKNOWN"

def motor_forward(speed):
    in1.value(1)
    in2.value(0)
    ena.duty(speed)

def motor_stop():
    in1.value(0)
    in2.value(0)
    ena.duty(0)

while True:
    r, g, b, c = sensor.read_raw()
    color = classify_color(r, g, b)

    if color == "RED":
        motor_forward(700)
    elif color == "GREEN":
        motor_forward(500)
    elif color == "BLUE":
        motor_forward(300)
    else:
        motor_stop()

    print("R:", r, "G:", g, "B:", b, "C:", c, "Detected:", color)
    time.sleep(1)