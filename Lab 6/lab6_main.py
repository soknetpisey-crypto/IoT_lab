from machine import Pin, SPI
from mfrc522 import MFRC522
import network
import urequests
import time
import os
import sdcard

# =========================
# WIFI
# =========================
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

print("Connecting WiFi", end="")
while not wifi.isconnected():
    print(".", end="")
    time.sleep(0.5)

print("\nConnected:", wifi.ifconfig())

# =========================
# FIRESTORE (PROJECT ID)
# =========================
PROJECT_ID = "rfid-87d6b"

url = "https://firestore.googleapis.com/v1/projects/{}/databases/(default)/documents/rfid_logs".format(PROJECT_ID)

def send_to_firestore(student, uid, datetime):
    data = {
        "fields": {
            "uid": {"stringValue": uid},
            "name": {"stringValue": student["name"]},
            "student_id": {"stringValue": student["id"]},
            "major": {"stringValue": student["major"]},
            "datetime": {"stringValue": datetime}
        }
    }

    try:
        res = urequests.post(url, json=data)
        print("Sent to Firestore")
        res.close()
    except Exception as e:
        print("Firestore Error:", e)

# =========================
# SD CARD
# =========================
def init_sd():
    try:
        spi = SPI(1, baudrate=1000000,
                  sck=Pin(14), mosi=Pin(15), miso=Pin(2))

        cs = Pin(13)

        sd = sdcard.SDCard(spi, cs)
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")

        print("SD Mounted")
    except Exception as e:
        print("SD Error:", e)

def save_to_sd(data):
    try:
        with open("/sd/attendance.csv", "a") as f:
            f.write(data + "\n")
        print("Saved to SD")
    except Exception as e:
        print("SD Write Error:", e)

# =========================
# BUZZER
# =========================
buzzer = Pin(4, Pin.OUT)

def beep(t):
    buzzer.on()
    time.sleep(t)
    buzzer.off()

# =========================
# RFID
# =========================
# spi = SPI(2, baudrate=2500000, polarity=0, phase=0)
# rdr = MFRC522(spi=spi, sck=18, mosi=23, miso=19, rst=22, cs=21)

spi = SPI(2, baudrate=1000000,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))

rdr = MFRC522(spi=spi, gpioRst=Pin(22), gpioCs=Pin(16))
# =========================
# DATABASE
# =========================
students = {
    "126402436163": {"name": "Kim Taehyung", "id": "2023001", "major": "IT"},
    "87654321": {"name": "Mesa", "id": "2023002", "major": "Software"}
}

# =========================
# TIME
# =========================
def get_time():
    t = time.localtime()
    return "{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

# =========================
# START
# =========================
init_sd()

print("Scan RFID...")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)

    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()

        if stat == rdr.OK:
            uid_str = "".join([str(i) for i in uid])
            print("UID:", uid_str)

            if uid_str in students:
                student = students[uid_str]
                now = get_time()

                print("Welcome", student["name"])

                # Buzzer short
                beep(0.3)

                # CSV
                csv = "{},{},{},{},{}".format(
                    uid_str,
                    student["name"],
                    student["id"],
                    student["major"],
                    now
                )
                save_to_sd(csv)

                # Firestore
                send_to_firestore(student, uid_str, now)

            else:
                print("Unknown Card")

                # Buzzer long
                beep(3)

            time.sleep(2)