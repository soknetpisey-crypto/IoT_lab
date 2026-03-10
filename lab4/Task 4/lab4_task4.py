import network, time, ujson, ubinascii, machine
from umqtt.simple import MQTTClient
from machine import Pin, ADC, I2C
import bmp280, ds3231, mlx90614

SSID, PASSWORD  = "Phann Home", "@home668"
BROKER, PORT    = "broker.hivemq.com", 1883
KEEPALIVE       = 60
CLIENT_ID       = b"aupp_" + ubinascii.hexlify(machine.unique_id())

TOPIC_MQ5       = b"/aupp/esp32/mq5"
TOPIC_MLX       = b"/aupp/esp32/mlx90614"
TOPIC_BMP       = b"/aupp/esp32/bmp280"

MQ5_PIN         = 33
WINDOW          = 5
FEVER_THRESHOLD = 32.5

readings = []

def moving_average(val):
    readings.append(val)
    if len(readings) > WINDOW: readings.pop(0)
    return sum(readings) / len(readings)

def classify(avg):
    if avg < 2100:   return "SAFE",    1
    elif avg < 2600: return "WARNING", 2
    else:            return "DANGER",  3

def fever_detect(body_temp):
    return 1 if body_temp >= FEVER_THRESHOLD else 0

def make_epoch(t):
    year, month, day, hour, minute, second = t

    # Days from 1970 to given year
    days = (year - 1970) * 365
    # Add leap years between 1970 and year
    days += (year - 1969) // 4
    # Days for each month
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if year % 4 == 0:
        month_days[1] = 29
    for m in range(month - 1):
        days += month_days[m]
    days += day - 1

    epoch = days * 86400 + hour * 3600 + minute * 60 + second

    return epoch * 1000

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(0.5)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 20000:
                raise RuntimeError("Wi-Fi timeout")
            time.sleep(0.3)
    print("WiFi OK:", wlan.ifconfig())

def main():
    wifi_connect()

    mq5 = ADC(Pin(MQ5_PIN))
    mq5.atten(ADC.ATTN_11DB)
    mq5.width(ADC.WIDTH_12BIT)

    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
    bmp = bmp280.BMP280(i2c)
    rtc = ds3231.DS3231(i2c)
    mlx = mlx90614.MLX90614(i2c)

    while True:
        try:
            client = MQTTClient(CLIENT_ID, BROKER, PORT, keepalive=KEEPALIVE)
            time.sleep(2)
            client.connect()
            print("MQTT connected →", BROKER)

            while True:

                raw                  = mq5.read()
                avg                  = moving_average(raw)
                voltage              = (avg / 4095) * 3.3
                risk_level, risk_num = classify(avg)

                print(f"[MQ5]  Raw: {raw} | Avg: {avg:.2f} | {voltage:.2f}V | {risk_level}({risk_num})")

                client.publish(TOPIC_MQ5, ujson.dumps({
                    "raw":      raw,
                    "avg":      round(avg, 2),
                    "voltage":  round(voltage, 3),
                    "risk_num": risk_num
                }))

                ambient_temp = round(mlx.read_ambient_temp(), 2)
                body_temp    = round(mlx.read_object_temp(), 2)
                fever_flag   = fever_detect(body_temp)

                print(f"[MLX]  Ambient: {ambient_temp}°C | Body: {body_temp}°C | Fever: {fever_flag}")

                client.publish(TOPIC_MLX, ujson.dumps({
                    "ambient_temp": ambient_temp,
                    "body_temp":    body_temp,
                    "fever_flag":   fever_flag
                }))

                temperature = round(bmp.temperature, 2)
                pressure    = round(bmp.pressure / 100, 2)
                altitude    = round(bmp.altitude, 2)

                now       = rtc.get_time()
                epoch     = make_epoch(now)

                print(f"[BMP]  Temp: {temperature}°C | Pressure: {pressure}hPa | Altitude: {altitude}m | Epoch: {epoch}")

                client.publish(TOPIC_BMP, ujson.dumps({
                    "temperature": temperature,
                    "pressure":    pressure,
                    "altitude":    altitude,
                    "epoch":       epoch
                }))

                print("─" * 50)
                time.sleep(2)

        except OSError as e:
            print("MQTT error:", e)
            try: client.close()
            except: pass
            print("Reconnecting in 3s...")
            time.sleep(3)

main()