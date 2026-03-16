import gc, time, network, socket
from machine import Pin, PWM, time_pulse_us, SoftI2C
import dht

try:
    import urequests as requests
except:
    import requests

try:
    from machine_i2c_lcd import I2cLcd
except:
    I2cLcd = None

try:
    from tm1637 import TM1637 as TM1637_CLASS
except:
    try:
        import tm1637
        TM1637_CLASS = tm1637.TM1637
    except:
        TM1637_CLASS = None

WIFI_SSID = "Phann Home"
WIFI_PASS = "@home668"
TELEGRAM_TOKEN = "8248231488:AAFBMXPj3F_Jrb6SagTzHGv4ed_LbOoSGxk"
TELEGRAM_CHAT_ID = "-1003642624312"

BLYNK_TOKEN = "XPKCVJrEE6tbLlHTjFP2h5LXxKAm4pOv"
BLYNK_API = "http://blynk.cloud/external/api"

PIN_DHT, PIN_TRIG, PIN_ECHO, SERVO_PIN, LED_PIN = 4, 27, 26, 13, 2
IR_SLOTS = [25, 32, 33]
TM_CLK, TM_DIO = 17, 16
I2C_SDA, I2C_SCL, I2C_ADDR = 21, 22, 0x27

TOTAL_SLOTS = 3
OPEN_ANGLE, CLOSE_ANGLE = 90, 0
SENSOR_INTERVAL, TELEGRAM_INTERVAL = 2, 20
VEHICLE_TIMEOUT = 10
AUTO_OPEN_DISTANCE = 30
MANUAL_CLOSE_TIMEOUT = 30

gc.collect()
led = Pin(LED_PIN, Pin.OUT)
led.off()

dht_sensor = dht.DHT11(Pin(PIN_DHT))
TRIG, ECHO = Pin(PIN_TRIG, Pin.OUT), Pin(PIN_ECHO, Pin.IN)
servo = PWM(Pin(SERVO_PIN), freq=50)
servo_current_angle = None


def angle_to_duty(angle):
    angle = max(0, min(180, angle))
    return int(25 + (angle / 180 * 100))


def set_servo(angle):
    global servo_current_angle
    try:
        angle = max(0, min(180, int(angle)))
        if servo_current_angle is not None and angle == servo_current_angle:
            return

        start = servo_current_angle if servo_current_angle is not None else angle
        step = 2 if angle > start else -2
        for a in range(start, angle, step):
            servo.duty(angle_to_duty(a))
            time.sleep_ms(20)

        servo.duty(angle_to_duty(angle))
        time.sleep_ms(250)
        servo_current_angle = angle
    except Exception as e:
        print("Servo error:", str(e)[:30])


ir_slots = [Pin(p, Pin.IN) for p in IR_SLOTS]
tm = None
if TM1637_CLASS:
    try:
        tm = TM1637_CLASS(clk_pin=TM_CLK, dio_pin=TM_DIO, brightness=5)
    except:
        try:
            tm = TM1637_CLASS(clk=Pin(TM_CLK), dio=Pin(TM_DIO))
            try:
                tm.brightness(5)
            except:
                pass
        except:
            tm = None


def tm_show_value(value):
    if not tm:
        return
    try:
        value = int(value)
    except:
        value = 0

    try:
        tm.show_number(value)
        return
    except:
        pass

    try:
        tm.show_digit(value)
        return
    except:
        pass

    try:
        tm.number(value)
        return
    except:
        pass

    try:
        tm.showNumberDec(value, False)
        return
    except:
        pass

    try:
        tm.write([int(c) for c in str(value).zfill(4)])
    except:
        pass


lcd = None
try:
    if I2cLcd:
        i2c = SoftI2C(sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)
        lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
except:
    lcd = None


def lcd_show(l1, l2=""):
    if lcd:
        try:
            lcd.clear()
            lcd.putstr(l1[:16])
            lcd.move_to(0, 1)
            lcd.putstr(l2[:16])
        except:
            pass


def ultrasonic_dist():
    try:
        TRIG.value(0)
        time.sleep_us(2)
        TRIG.value(1)
        time.sleep_us(10)
        TRIG.value(0)
        duration = time_pulse_us(ECHO, 1, 30000)
        return (duration * 0.0343) / 2 if duration > 0 else None
    except:
        return None


def read_dht():
    try:
        dht_sensor.measure()
        return dht_sensor.temperature(), dht_sensor.humidity()
    except:
        return None, None


def count_slots():
    try:
        return sum(1 for s in ir_slots if s.value() == 1)
    except:
        return 0


wifi = network.WLAN(network.STA_IF)
wifi.active(True)


def connect_wifi():
    for attempt in range(5):
        try:
            if not wifi.isconnected():
                wifi.connect(WIFI_SSID, WIFI_PASS)
                lcd_show("Connecting {}..".format(attempt + 1))
                start = time.time()
                while not wifi.isconnected() and (time.time() - start) < 15:
                    time.sleep(1)
            if wifi.isconnected():
                ip = wifi.ifconfig()[0]
                lcd_show("WiFi OK", ip)
                print("IP:", ip)
                return ip
        except:
            wifi.active(False)
            time.sleep(1)
            wifi.active(True)
            time.sleep(1)

    try:
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid='ESP32_Device')
    except:
        pass
    return "AP Mode"


ip = connect_wifi()

gate_state = 'CLOSED'
gate_manual = False
light_manual = False  # True = user manually set light, auto logic blocked until lot empties
stats = {'entries': 0, 'exits': 0, 'gates': 0}
sensor_cache = {'temp': 'N/A', 'hum': 'N/A', 'dist': 'N/A', 'free': TOTAL_SLOTS}

TG_URL = "https://api.telegram.org/bot{}/".format(TELEGRAM_TOKEN)
tg_offset = 0


def tg_send(msg):
    try:
        url = TG_URL + "sendMessage"
        data = "chat_id={}&text={}".format(TELEGRAM_CHAT_ID, msg)
        r = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
        r.close()
        gc.collect()
    except Exception as e:
        print("TG send error:", str(e)[:40])
        gc.collect()


def tg_poll():
    global tg_offset, light_manual
    gc.collect()
    try:
        url = TG_URL + "getUpdates?offset={}".format(tg_offset + 1)
        r = requests.get(url, timeout=10)
        messages = r.json().get('result', [])
        r.close()
        gc.collect()

        for msg in messages:
            tg_offset = msg['update_id']

            if 'message' not in msg:
                continue

            text = msg['message'].get('text', '').strip().lower()
            chat_id = msg['message']['chat']['id']

            if str(chat_id) != str(TELEGRAM_CHAT_ID):
                continue

            print("TG cmd:", text)

            if '/help' in text or '/start' in text:
                tg_send("🅿️ *Smart Parking System*\n\n"
                       "Commands:\n"
                       "/status - System status\n"
                       "/slots - Available slots\n"
                       "/temp - Temperature\n"
                       "/open - Open gate\n"
                       "/close - Close gate\n"
                       "/light_on - Lights ON\n"
                       "/light_off - Lights OFF\n"
                       "/stats - Statistics")

            elif '/status' in text:
                light_status = "ON" if led.value() else "OFF"
                msg = "Status\n\nSlots: {}/{}\nTemp: {}C\nHumidity: {}%\nGate: {}\nLights: {}".format(
                    sensor_cache['free'], TOTAL_SLOTS,
                    sensor_cache['temp'],
                    sensor_cache['hum'],
                    gate_state,
                    light_status)
                tg_send(msg)

            elif '/slots' in text:
                pct = int((sensor_cache['free'] / TOTAL_SLOTS) * 100)
                msg = "Parking Status\n\n{}/{} slots free\nOccupancy: {}%".format(
                    sensor_cache['free'], TOTAL_SLOTS, 100-pct)
                tg_send(msg)

            elif '/temp' in text:
                msg = "Temperature\n\nTemp: {}C\nHumidity: {}%".format(
                    sensor_cache['temp'], sensor_cache['hum'])
                tg_send(msg)

            elif '/open' in text:
                open_gate('tg')
                stats['gates'] += 1
                tg_send("Gate opened (manual)")

            elif '/close' in text:
                close_gate('tg')
                tg_send("Gate closed (manual)")

            elif '/light_on' in text:
                led.on()
                light_manual = True
                tg_send("Lights ON")

            elif '/light_off' in text:
                led.off()
                light_manual = True
                tg_send("Lights OFF")

            elif '/stats' in text:
                msg = "Statistics\n\nEntries: {}\nExits: {}\nGate Ops: {}".format(
                    stats['entries'], stats['exits'], stats['gates'])
                tg_send(msg)

    except Exception as e:
        print("TG poll error:", str(e)[:40])
    finally:
        gc.collect()


def web_page():
    gc.collect()
    free = sensor_cache['free']

    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" name="viewport" content="width=device-width,initial-scale=1">
<title>Smart Parking</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: Arial, sans-serif; background:#f0f2f5; color:#1c1e21; padding:10px; }
.header { background:#2563eb; color:#fff; padding:15px; border-radius:5px; margin-bottom:15px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-bottom:15px; }
.card { background:#fff; padding:15px; border-radius:5px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
.card-val { font-size:28px; font-weight:bold; color:#2563eb; }
.card-label { font-size:11px; color:#666; text-transform:uppercase; margin-top:5px; }
.status { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:15px; }
.slot { padding:12px; text-align:center; border:2px solid #ddd; border-radius:5px; font-weight:bold; }
.slot.free { color:#10b981; border-color:#10b981; background:#ecfdf5; }
.slot.occ { color:#ef4444; border-color:#ef4444; background:#fee2e2; }
.controls { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:15px; }
.btn { padding:10px; border:none; border-radius:5px; color:#fff; font-weight:bold; cursor:pointer; }
.btn-green { background:#10b981; }
.btn-red { background:#ef4444; }
.btn-blue { background:#3b82f6; }
.btn:hover { opacity:0.9; }
.panel { background:#fff; padding:15px; border-radius:5px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-top:10px; }
.stat { background:#f0f2f5; padding:8px; text-align:center; border-radius:5px; }
.stat-val { font-size:18px; font-weight:bold; color:#2563eb; }
.stat-lbl { font-size:10px; color:#666; }
</style>
</head>
<body>
<div class="header">
<h2>🅿️ Smart Parking System</h2>
<p style="font-size:12px; opacity:0.9; margin-top:5px;">Live monitoring dashboard</p>
</div>

<div class="grid">
<div class="card"><div class="card-val">""" + str(free) + """</div><div class="card-label">Available Slots</div></div>
<div class="card"><div class="card-val">""" + str(sensor_cache['temp']) + """°</div><div class="card-label">Temperature</div></div>
<div class="card"><div class="card-val">""" + str(sensor_cache['hum']) + """%</div><div class="card-label">Humidity</div></div>
<div class="card"><div class="card-val">""" + str(sensor_cache['dist']) + """cm</div><div class="card-label">Entry Dist</div></div>
<div class="card"><div class="card-val">""" + gate_state + """</div><div class="card-label">Gate Status</div></div>
<div class="card"><div class="card-val">""" + ("ON" if led.value() else "OFF") + """</div><div class="card-label">Lights</div></div>
</div>

<div class="panel">
<b>Parking Slots</b>
<div class="status">
<div class="slot """ + ("free" if ir_slots[0].value() == 1 else "occ") + """">Slot 1</div>
<div class="slot """ + ("free" if ir_slots[1].value() == 1 else "occ") + """">Slot 2</div>
<div class="slot """ + ("free" if ir_slots[2].value() == 1 else "occ") + """">Slot 3</div>
</div>
</div>

<div class="controls">
<button class="btn btn-green" onclick="fetch('/api/gate/open').catch(e=>alert('Error'))">OPEN GATE</button>
<button class="btn btn-red" onclick="fetch('/api/gate/close').catch(e=>alert('Error'))">CLOSE GATE</button>
<button class="btn btn-blue" onclick="fetch('/api/lights/on').catch(e=>alert('Error'))">LIGHTS ON</button>
<button class="btn btn-red" onclick="fetch('/api/lights/off').catch(e=>alert('Error'))">LIGHTS OFF</button>
</div>

<div class="panel">
<b>Statistics</b>
<div class="stats">
<div class="stat"><div class="stat-val">""" + str(stats['entries']) + """</div><div class="stat-lbl">Entries</div></div>
<div class="stat"><div class="stat-val">""" + str(stats['exits']) + """</div><div class="stat-lbl">Exits</div></div>
<div class="stat"><div class="stat-val">""" + str(stats['gates']) + """</div><div class="stat-lbl">Gates</div></div>
<div class="stat"><div class="stat-val">""" + str(TOTAL_SLOTS - free) + """</div><div class="stat-lbl">Occupied</div></div>
</div>
</div>

<script>
function updateDash(){fetch('/api/data').then(r=>r.text()).then(d=>{let parts=d.split('|');let free=parts[0],temp=parts[1],hum=parts[2],dist=parts[3],gate=parts[4],light=parts[5],entries=parts[6],exits=parts[7],gates=parts[8],s0=parts[9],s1=parts[10],s2=parts[11];document.querySelectorAll('.card-val')[0].textContent=free;document.querySelectorAll('.card-val')[1].textContent=temp+'°';document.querySelectorAll('.card-val')[2].textContent=hum+'%';document.querySelectorAll('.card-val')[3].textContent=dist+'cm';document.querySelectorAll('.card-val')[4].textContent=gate;document.querySelectorAll('.card-val')[5].textContent=light;document.querySelectorAll('.stat-val')[0].textContent=entries;document.querySelectorAll('.stat-val')[1].textContent=exits;document.querySelectorAll('.stat-val')[2].textContent=gates;let occ=3-parseInt(free);document.querySelectorAll('.stat-val')[3].textContent=occ;let slots=document.querySelectorAll('.slot');if(slots.length>=3){slots[0].className='slot '+(s0=='1'?'free':'occ');slots[1].className='slot '+(s1=='1'?'free':'occ');slots[2].className='slot '+(s2=='1'?'free':'occ');}}).catch(e=>console.log('Update failed'))}
setInterval(updateDash,2000);
</script>
</body>
</html>"""
    gc.collect()
    return html


s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 80))
s.listen(1)
s.settimeout(0.5)


def send_http(conn, data, ctype='text/html'):
    try:
        header = "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nConnection: close\r\n\r\n".format(ctype)
        conn.send(header)
        if isinstance(data, str):
            data = data.encode()
        conn.send(data)
    except:
        pass


def blynk_get(pin):
    try:
        url = "{}/get?token={}&{}".format(BLYNK_API, BLYNK_TOKEN, pin)
        r = requests.get(url, timeout=5)
        val = r.text
        r.close()
        return val
    except:
        return None


def blynk_write(pin, value):
    try:
        url = "{}/update?token={}&{}={}".format(BLYNK_API, BLYNK_TOKEN, pin, value)
        r = requests.get(url, timeout=5)
        r.close()
    except Exception as e:
        print("Blynk write error:", str(e)[:30])


def blynk_write_slots_now():
    try:
        free = int(sensor_cache['free'])
    except:
        free = 0
    if free < 0:
        free = 0
    if free > TOTAL_SLOTS:
        free = TOTAL_SLOTS
    blynk_write('V0', free)


def blynk_update():
    try:
        blynk_write_slots_now()
        temp_val = sensor_cache['temp']
        if temp_val == 'N/A':
            temp_val = 0
        blynk_write('V2', temp_val)
        blynk_write('V5', 1 if gate_state == 'OPEN' else 0)
        blynk_write('V6', 1 if led.value() else 0)
    except Exception as e:
        print("Blynk update error:", str(e)[:30])


def blynk_poll():
    global blynk_gate_cmd_prev
    try:
        gate_cmd = blynk_get('V3')
        cmd = None
        if gate_cmd is not None:
            txt = str(gate_cmd).strip().strip('[]').strip('"').strip("'")
            if txt in ('1', '1.0'):
                cmd = 1
            elif txt in ('0', '0.0'):
                cmd = 0

        if cmd is None:
            return

        if blynk_gate_cmd_prev is None:
            blynk_gate_cmd_prev = cmd
            return

        if blynk_gate_cmd_prev == cmd:
            return

        blynk_gate_cmd_prev = cmd

        if cmd == 1 and gate_state == 'CLOSED':
            open_gate('blynk')
            stats['gates'] += 1
        elif cmd == 0 and gate_state == 'OPEN':
            close_gate('blynk')
    except Exception as e:
        print("Blynk poll error:", str(e)[:30])


def open_gate(by='auto'):
    global gate_state, gate_manual
    if gate_state == 'OPEN':
        return
    try:
        set_servo(OPEN_ANGLE)
        gate_state = 'OPEN'
        if by in ['tg', 'web', 'blynk']:
            gate_manual = True
    except:
        pass


def close_gate(by='auto'):
    global gate_state, gate_manual
    if gate_state == 'CLOSED':
        return
    try:
        set_servo(CLOSE_ANGLE)
        gate_state = 'CLOSED'
        if by in ['tg', 'web', 'blynk']:
            gate_manual = False
    except:
        pass


set_servo(CLOSE_ANGLE)
print('Server: http://{}'.format(ip))
lcd_show('Ready', ip)

tg_t = time.time()
sen_t = time.time()
slot_prev = count_slots()
light_t = time.time()
vseen_t = time.time()
blynk_t = time.time()
blynk_gate_cmd_prev = None

sensor_cache['free'] = slot_prev
blynk_write_slots_now()

try:
    while True:
        if time.time() - sen_t > SENSOR_INTERVAL:
            sen_t = time.time()
            dist = ultrasonic_dist()
            temp, hum = read_dht()
            free = count_slots()

            sensor_cache['temp'] = temp if temp is not None else 'N/A'
            sensor_cache['hum'] = hum if hum is not None else 'N/A'
            sensor_cache['dist'] = round(dist, 1) if dist is not None else 'N/A'
            sensor_cache['free'] = free

            if free != slot_prev:
                stats['entries' if free < slot_prev else 'exits'] += 1
                slot_prev = free
                blynk_write_slots_now()

            if tm:
                tm_show_value(free)

            lcd_show('Slots:{} G:{}'.format(free, gate_state),
                     'T:{} H:{}'.format(temp if temp is not None else 'N/A',
                                        hum if hum is not None else 'N/A'))

            if free == TOTAL_SLOTS:
                light_manual = False  # lot fully empty: release manual lock, auto resumes

            if not light_manual:
                if free < TOTAL_SLOTS:
                    if not led.value():
                        led.on()
                    light_t = time.time()
                elif time.time() - light_t > 60 and led.value():
                    led.off()

            if not gate_manual:
                if dist is not None and dist < AUTO_OPEN_DISTANCE and free > 0 and gate_state == 'CLOSED':
                    open_gate('sensor')
                    stats['gates'] += 1
                    vseen_t = time.time()

                if gate_state == 'OPEN' and (dist is None or dist >= AUTO_OPEN_DISTANCE):
                    if time.time() - vseen_t > VEHICLE_TIMEOUT:
                        close_gate('sensor')
                else:
                    vseen_t = time.time()
            # gate_manual=True: do nothing — gate stays as-is until a manual close command

        if time.time() - tg_t > TELEGRAM_INTERVAL:
            tg_t = time.time()
            tg_poll()

        if time.time() - blynk_t > 5:
            blynk_t = time.time()
            blynk_update()
            blynk_poll()

        try:
            conn, _ = s.accept()
            try:
                req = conn.recv(512).decode()
                path = req.split(' ')[1]

                if '/api/gate/open' in path:
                    open_gate('web')
                    stats['gates'] += 1
                    send_http(conn, '{"ok":true}', 'application/json')
                elif '/api/gate/close' in path:
                    close_gate('web')
                    send_http(conn, '{"ok":true}', 'application/json')
                elif '/api/lights/on' in path:
                    led.on()
                    light_manual = True
                    light_t = time.time()
                    send_http(conn, '{"ok":true}', 'application/json')
                elif '/api/lights/off' in path:
                    led.off()
                    light_manual = True
                    send_http(conn, '{"ok":true}', 'application/json')
                elif '/api/data' in path:
                    s0 = '1' if ir_slots[0].value() == 1 else '0'
                    s1 = '1' if ir_slots[1].value() == 1 else '0'
                    s2 = '1' if ir_slots[2].value() == 1 else '0'
                    data = '{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}'.format(
                        sensor_cache['free'], sensor_cache['temp'], sensor_cache['hum'],
                        sensor_cache['dist'], gate_state, 'ON' if led.value() else 'OFF',
                        stats['entries'], stats['exits'], stats['gates'], s0, s1, s2)
                    send_http(conn, data, 'text/plain')
                else:
                    gc.collect()
                    send_http(conn, web_page(), 'text/html')
            except:
                pass
            finally:
                conn.close()
                gc.collect()
        except OSError:
            pass
        except:
            pass

        gc.collect()
        time.sleep_ms(50)

except KeyboardInterrupt:
    print('Stopped')
    lcd_show('Stopped')
    s.close()
