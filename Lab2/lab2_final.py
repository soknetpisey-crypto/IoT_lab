import network
import socket
from machine import Pin, time_pulse_us, SoftI2C
from machine_i2c_lcd import I2cLcd
import dht
import time
import gc  # Garbage collector for memory management

# ==============================
# LED SETUP
# ==============================
led = Pin(2, Pin.OUT)
led.off()

# ==============================
# LCD SETUP
# ==============================
I2C_ADDR = 0x27
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

def lcd_clear():
    lcd.clear()
    time.sleep_ms(50)

lcd_clear()
lcd.putstr("ESP32 Ready")
lcd.move_to(0, 1)
lcd.putstr("Initializing...")
time.sleep(2)

# ==============================
# SENSOR SETUP
# ==============================
dht_sensor = dht.DHT11(Pin(4))
TRIG = Pin(27, Pin.OUT)
ECHO = Pin(26, Pin.IN)

# ==============================
# GLOBAL VARIABLES
# ==============================
current_temperature = None
current_humidity = None
current_distance = None
led_state = "OFF"

# ==============================
# SENSOR FUNCTIONS
# ==============================
def get_distance_cm():
    try:
        TRIG.value(0)
        time.sleep_us(2)
        TRIG.value(1)
        time.sleep_us(10)
        TRIG.value(0)
        
        duration = time_pulse_us(ECHO, 1, 30000)
        if duration < 0:
            return None
        return round((duration * 0.0343) / 2, 1)
    except:
        return None

def update_sensors():
    global current_temperature, current_humidity, current_distance
    try:
        dht_sensor.measure()
        current_temperature = dht_sensor.temperature()
        current_humidity = dht_sensor.humidity()
    except:
        current_temperature = None
        current_humidity = None
    
    current_distance = get_distance_cm()

# ==============================
# LCD FUNCTIONS
# ==============================
def lcd_distance_line1():
    lcd.move_to(0, 0)
    lcd.putstr(" " * 16)
    lcd.move_to(0, 0)
    if current_distance is not None:
        lcd.putstr("Dist:{:.1f}cm".format(current_distance))
    else:
        lcd.putstr("Dist: Error")

def lcd_temp_line2():
    lcd.move_to(0, 1)
    lcd.putstr(" " * 16)
    lcd.move_to(0, 1)
    if current_temperature is not None:
        lcd.putstr("Temp:{}{}C".format(current_temperature, chr(223)))
    else:
        lcd.putstr("Temp: Error")

def lcd_scroll_once(text, row, delay):
    if len(text) <= 16:
        lcd.move_to(0, row)
        lcd.putstr(" " * 16)
        lcd.move_to(0, row)
        lcd.putstr(text[:16])
        return
    
    text = text + " " * 16
    for i in range(len(text) - 15):
        lcd.move_to(0, row)
        lcd.putstr(text[i:i+16])
        time.sleep(delay)

def safe_for_lcd(text):
    out = ""
    for ch in text:
        o = ord(ch)
        if 32 <= o <= 126:
            out += ch
        else:
            out += "?"
    return out

# ==============================
# URL DECODER
# ==============================
def url_decode(text):
    text = text.replace("+", " ")
    result = ""
    i = 0
    ln = len(text)
    while i < ln:
        if text[i] == "%" and i + 2 < ln:
            try:
                result += chr(int(text[i+1:i+3], 16))
                i += 3
            except:
                result += text[i]
                i += 1
        else:
            result += text[i]
            i += 1
    return result

# ==============================
# WIFI SETUP
# ==============================
ssid = "Robotic WIFI"
password = "rbtWIFI@2025"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)

print("Connecting to WiFi...")
lcd_clear()
lcd.putstr("Connecting WiFi")

while not wifi.isconnected():
    time.sleep(1)

ip = wifi.ifconfig()[0]
print("ESP32 connected!")
print("IP Address:", ip)

lcd_clear()
lcd.putstr("IP Address:")
lcd.move_to(0, 1)
lcd.putstr(ip[:16])
time.sleep(3)

# ==============================
# WEB SERVER SETUP
# ==============================
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
s.settimeout(1)

print("Web server running...")

# ==============================
# JSON API FOR SENSOR DATA (NEW)
# ==============================
def get_sensor_json():
    """Return sensor data as JSON string"""
    update_sensors()
    temp = str(current_temperature) if current_temperature is not None else "N/A"
    humid = str(current_humidity) if current_humidity is not None else "N/A"
    dist = str(current_distance) if current_distance is not None else "N/A"
    
    json_data = '{"temperature":"' + temp + '","humidity":"' + humid + '","distance":"' + dist + '","led":"' + led_state + '"}'
    return json_data

# ==============================
# OPTIMIZED WEB INTERFACE (NO AUTO-RELOAD)
# ==============================
def web_page():
    # Don't update sensors here - only on API call
    temp_display = str(current_temperature) if current_temperature is not None else "N/A"
    humid_display = str(current_humidity) if current_humidity is not None else "N/A"
    dist_display = str(current_distance) if current_distance is not None else "N/A"
    
    # Simplified HTML - removed redundant spaces and comments
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ESP32 Control</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0a0a;--surface:#141414;--border:#282828;--text:#e8e8e8;--text-dim:#787878;--accent:#00d9ff;--green:#00ff88;--red:#ff3366;--orange:#ff9500}
[data-theme="light"]{--bg:#fafafa;--surface:#fff;--border:#e0e0e0;--text:#1a1a1a;--text-dim:#666}
body{font-family:-apple-system,system-ui,sans-serif;background:var(--bg);color:var(--text);transition:all .3s}
.topbar{background:var(--surface);border-bottom:1px solid var(--border);padding:0 24px;height:64px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.logo{font-size:15px;font-weight:600;display:flex;align-items:center;gap:10px}
.logo-dot{width:8px;height:8px;background:var(--accent);border-radius:50%;animation:pulse-dot 2s ease-in-out infinite}
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.6}}
.theme-switch{width:52px;height:28px;background:var(--border);border-radius:14px;position:relative;cursor:pointer}
.theme-switch::after{content:'';position:absolute;width:22px;height:22px;background:var(--text);border-radius:50%;top:3px;left:3px;transition:transform .3s}
[data-theme="dark"] .theme-switch::after{transform:translateX(24px)}
.main{max-width:1400px;margin:0 auto;padding:32px 24px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:16px}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;transition:border-color .2s}
.panel:hover{border-color:var(--text-dim)}
.panel-header{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--text-dim);margin-bottom:16px;font-weight:500}
.metric{font-size:42px;font-weight:300;letter-spacing:-1.5px;line-height:1;margin-bottom:8px;color:var(--text)}
.metric-unit{font-size:16px;color:var(--text-dim);font-weight:400;margin-left:4px}
.led-control{grid-column:span 2}
.switch-container{display:flex;gap:12px;margin-top:20px}
.switch-btn{flex:1;height:44px;border:1px solid var(--border);background:transparent;color:var(--text);border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:all .2s;text-decoration:none;display:flex;align-items:center;justify-content:center}
.switch-btn:hover{background:var(--border)}
.switch-btn.active-on{background:var(--green);border-color:var(--green);color:#000}
.switch-btn.active-off{background:var(--red);border-color:var(--red);color:#fff}
.led-status{margin-top:16px;font-size:13px;color:var(--text-dim)}
.status-indicator{display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:6px;background:var(--text-dim)}
.status-indicator.on{background:var(--green);box-shadow:0 0 8px var(--green)}
.lcd-section{grid-column:span 4;margin-top:16px}
.lcd-controls{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.ctrl-btn{height:48px;background:var(--surface);border:1px solid var(--border);color:var(--text);border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:all .2s;text-decoration:none;display:flex;align-items:center;justify-content:center}
.ctrl-btn:hover{border-color:var(--accent);background:rgba(0,217,255,.05)}
.input-wrapper{display:flex;gap:12px}
.text-field{flex:1;height:48px;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:0 16px;border-radius:8px;font-size:14px;outline:none}
.text-field:focus{border-color:var(--accent)}
.send-btn{height:48px;padding:0 28px;background:var(--accent);border:none;color:#000;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s}
.send-btn:hover{background:#00b8d4;transform:translateY(-1px)}
.clear-btn{background:transparent;border:1px solid var(--orange);color:var(--orange);margin-top:12px;width:100%}
.clear-btn:hover{background:rgba(255,149,0,.1)}
.refresh-tag{display:inline-block;font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-dim);background:var(--border);padding:4px 8px;border-radius:4px;margin-top:12px}
@media(max-width:1024px){.grid{grid-template-columns:repeat(2,1fr)}.lcd-section,.led-control{grid-column:span 2}}
@media(max-width:640px){.grid{grid-template-columns:1fr}.lcd-section,.led-control{grid-column:span 1}.metric{font-size:36px}.topbar{padding:0 16px}.main{padding:20px 16px}}
</style>
</head>
<body data-theme="dark">
<div class="topbar">
<div class="logo"><div class="logo-dot"></div>ESP32 CONTROL SYSTEM</div>
<div class="theme-switch" onclick="toggleTheme()"></div>
</div>
<div class="main">
<div class="grid">
<div class="panel">
<div class="panel-header">Temperature</div>
<div class="metric"><span id="temp">""" + temp_display + """</span><span class="metric-unit">°C</span></div>
<div class="refresh-tag">Live Data</div>
</div>
<div class="panel">
<div class="panel-header">Humidity</div>
<div class="metric"><span id="humid">""" + humid_display + """</span><span class="metric-unit">%</span></div>
<div class="refresh-tag">Live Data</div>
</div>
<div class="panel">
<div class="panel-header">Distance</div>
<div class="metric"><span id="dist">""" + dist_display + """</span><span class="metric-unit">cm</span></div>
<div class="refresh-tag">Live Data</div>
</div>
<div class="panel led-control">
<div class="panel-header">GPIO Control</div>
<div class="switch-container">
<a href="/led_on" class="switch-btn """ + ("active-on" if led_state == "ON" else "") + """" onclick="return ctrlLED('on')">ENABLE</a>
<a href="/led_off" class="switch-btn """ + ("active-off" if led_state == "OFF" else "") + """" onclick="return ctrlLED('off')">DISABLE</a>
</div>
<div class="led-status">
<span class="status-indicator """ + ("on" if led_state == "ON" else "") + """" id="ledIndicator"></span>
STATUS: <span id="ledStatus">""" + led_state + """</span>
</div>
</div>
</div>
<div class="grid">
<div class="panel lcd-section">
<div class="panel-header">LCD Display Control</div>
<div class="lcd-controls">
<a href="/show_distance" class="ctrl-btn" onclick="return sendCmd('show_distance')">DISPLAY DISTANCE</a>
<a href="/show_temp" class="ctrl-btn" onclick="return sendCmd('show_temp')">DISPLAY TEMPERATURE</a>
</div>
<form onsubmit="return sendText(event)">
<div class="input-wrapper">
<input type="text" id="msgInput" class="text-field" placeholder="Enter custom message" maxlength="100" required>
<button type="submit" class="send-btn">SEND</button>
</div>
</form>
<a href="/clear_lcd" class="ctrl-btn clear-btn" onclick="return sendCmd('clear_lcd')">CLEAR DISPLAY</a>
</div>
</div>
</div>
<script>
function toggleTheme(){const b=document.body,c=b.getAttribute('data-theme'),n=c==='dark'?'light':'dark';b.setAttribute('data-theme',n);localStorage.setItem('theme',n)}
const saved=localStorage.getItem('theme')||'dark';document.body.setAttribute('data-theme',saved);
function updateSensors(){fetch('/api/sensors').then(r=>r.json()).then(d=>{document.getElementById('temp').textContent=d.temperature;document.getElementById('humid').textContent=d.humidity;document.getElementById('dist').textContent=d.distance;document.getElementById('ledStatus').textContent=d.led;const ind=document.getElementById('ledIndicator');ind.className=d.led==='ON'?'status-indicator on':'status-indicator'}).catch(e=>console.error('Error:',e))}
setInterval(updateSensors,2000);
function ctrlLED(s){fetch('/led_'+s).then(()=>updateSensors());return false}
function sendCmd(c){fetch('/'+c).then(()=>updateSensors());return false}
function sendText(e){e.preventDefault();const m=document.getElementById('msgInput').value;fetch('/send_text?msg='+encodeURIComponent(m)).then(()=>{document.getElementById('msgInput').value='';updateSensors()});return false}
</script>
</body>
</html>
"""
    return html

# ==============================
# MAIN LOOP (OPTIMIZED)
# ==============================
print("Server ready! Access at: http://{}".format(ip))
lcd_clear()
lcd.putstr("Server Ready!")

# Request counter for garbage collection
request_count = 0

while True:
    try:
        conn = None
        try:
            conn, addr = s.accept()
        except OSError:
            continue
        
        if conn:
            raw = conn.recv(1024)
            try:
                request = raw.decode()
            except:
                request = str(raw)
            
            # Parse request path
            lines = request.split("\r\n")
            if len(lines) > 0:
                first_line = lines[0]
                parts = first_line.split(" ")
                if len(parts) >= 2:
                    path = parts[1]
                else:
                    path = "/"
            else:
                path = "/"
            
            print("Request:", path)
            
            # Handle API endpoint for sensor data (NEW - lightweight JSON response)
            if path.startswith("/api/sensors"):
                json_response = get_sensor_json()
                try:
                    conn.send(b"HTTP/1.1 200 OK\r\n")
                    conn.send(b"Content-Type: application/json\r\n")
                    conn.send(b"Connection: close\r\n\r\n")
                    conn.send(json_response.encode())
                except Exception as e:
                    print("Error sending JSON:", e)
                finally:
                    conn.close()
                    conn = None
                continue
            
            # TASK 1: LED CONTROL
            if path.startswith("/led_on"):
                led.on()
                led_state = "ON"
                print("LED ON")
            
            elif path.startswith("/led_off"):
                led.off()
                led_state = "OFF"
                print("LED OFF")
            
            # TASK 3: SENSOR TO LCD
            elif path.startswith("/show_distance"):
                update_sensors()
                lcd_distance_line1()
                print("Distance on LCD")
            
            elif path.startswith("/show_temp"):
                update_sensors()
                lcd_temp_line2()
                print("Temp on LCD")
            
            # TASK 4: TEXT TO LCD
            elif path.startswith("/send_text?"):
                try:
                    q_split = path.split("?", 1)
                    if len(q_split) > 1:
                        query = q_split[1]
                        params = query.split("&")
                        raw_msg = ""
                        for p in params:
                            if p.startswith("msg="):
                                raw_msg = p[4:]
                                break
                        
                        decoded = url_decode(raw_msg)
                        decoded = safe_for_lcd(decoded)
                        
                        if decoded:
                            lcd_clear()
                            lcd_scroll_once(decoded, 0, 0.3)
                            print("Text to LCD:", decoded[:20])
                except Exception as e:
                    print("Error:", e)
            
            elif path.startswith("/clear_lcd"):
                lcd_clear()
                print("LCD cleared")
            
            # Send minimal response for control commands
            if not path.startswith("/api/"):
                try:
                    if path == "/":
                        # Full page only for initial load
                        response = web_page()
                        conn.send(b"HTTP/1.1 200 OK\r\n")
                        conn.send(b"Content-Type: text/html; charset=UTF-8\r\n")
                        conn.send(b"Connection: close\r\n\r\n")
                        conn.sendall(response.encode())
                    else:
                        # Minimal response for actions
                        conn.send(b"HTTP/1.1 200 OK\r\n")
                        conn.send(b"Content-Type: text/plain\r\n")
                        conn.send(b"Connection: close\r\n\r\n")
                        conn.send(b"OK")
                except Exception as e:
                    print("Error sending response:", e)
                finally:
                    if conn:
                        conn.close()
                        conn = None
            
            # Garbage collection every 10 requests
            request_count += 1
            if request_count >= 10:
                gc.collect()
                print("Free memory:", gc.mem_free())
                request_count = 0
        
        time.sleep_ms(10)  # Reduced from 50ms
    
    except KeyboardInterrupt:
        print("Server stopped")
        lcd_clear()
        lcd.putstr("Stopped")
        break
    except Exception as e:
        print("Error:", e)
        if conn:
            try:
                conn.close()
            except:
                pass
        gc.collect()
        time.sleep_ms(100)

# Cleanup
try:
    s.close()
    wifi.active(False)
except:
    pass
print("Goodbye!")
