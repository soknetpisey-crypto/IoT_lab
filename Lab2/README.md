# Lab 2 : IoT Webserver with LED, Sensors, and LCD Control
This lab focuses on developing an ESP32- based IoT system that integrates a web interface with an LCD display. Users can interact through the web server to control the LCD, monitor sensor data, and send custom messages to be displayed on the screen. 
## Equipment
<img width="960" height="1280" alt="image" src="https://github.com/user-attachments/assets/4d5c6986-be26-409d-a70d-7e0b1fc36c4a" />

- ESP32 Dev Board (Micropython firmware flashed)
- DHT22 sensor (temperature/humidity)
- HC-SR04 ultrasonic distance sensor
-	LCD 16x2 with I2C backpack
-	Breadboard, jumper wires
-	USB cable + laptop with Thonny
- Wi-fi access
## Wiring Connection and Set up instructions
### 1. Hardware Setup
- Connect all components according to the wiring diagram
- Ensure the ESP32 is properly powered via USB
- Verify all sensor connections are secure
#### DHT22 → ESP32
| DHT22 Pin | ESP32 Pin |
|----------|-----------|
| VCC (+) | VCC/5V |
| DATA (I/O) | GPIO 4 (D4) |
| GND (-) | GND |
#### Ultrasonic Sensor → ESP32
| Ultrasonic Sensor | ESP32 Pin |
|----------|-----------|
| VCC | VCC/5V |
| Tring | GPIO 27 (D27) |
| Echo | GPIO 26 (D26) |
| GND | GND |
#### LCD 12C → ESP32
| LCD 12C | ESP32 Pin |
|----------|-----------|
| VCC | VCC/5V |
| GND | GND |
| SDA | GPIO 21 (D21) |
| SCL | GPIO 22 (D22) |
### 2. Micropython Environment
- Open **Thonny IDE** on your laptop
- Connect the ESP32 via USB
- Verify Micropython firmware is installed ( check interpreter in bottom-right corner)
- Select the correct COM port for your ESP32
### 3. Wi-fi Configuration
Edit each file with your wi-fi credentials:
```python
ssid = ""
password = ""
```
### 4. Required Libraries
Upload the following libraries to your ESP32:
- lcd_api.py
```python
# Minimal LCD API (HD44780-compatible)
from time import sleep_ms

# Commands
LCD_CLR         = 0x01
LCD_HOME        = 0x02
LCD_ENTRY_MODE  = 0x04
LCD_ENTRY_INC   = 0x02
LCD_ENTRY_SHIFT = 0x01
LCD_ON_CTRL     = 0x08
LCD_ON_DISPLAY  = 0x04
LCD_ON_CURSOR   = 0x02
LCD_ON_BLINK    = 0x01
LCD_MOVE        = 0x10
LCD_MOVE_DISP   = 0x08
LCD_MOVE_RIGHT  = 0x04
LCD_FUNCTION    = 0x20
LCD_FUNCTION_2L = 0x08
LCD_FUNCTION_5x10_DOTS = 0x04
LCD_SET_CGRAM   = 0x40
LCD_SET_DDRAM   = 0x80

class LcdApi:
    def __init__(self, num_lines, num_columns):
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.cursor_x = 0
        self.cursor_y = 0

    def clear(self):
        self.hal_write_command(LCD_CLR)
        sleep_ms(2)
        self.move_to(0, 0)

    def home(self):
        self.hal_write_command(LCD_HOME)
        sleep_ms(2)
        self.move_to(0, 0)

    def show_cursor(self, show):
        cmd = LCD_ON_CTRL | LCD_ON_DISPLAY | (LCD_ON_CURSOR if show else 0)
        self.hal_write_command(cmd)

    def blink_cursor(self, blink):
        cmd = LCD_ON_CTRL | LCD_ON_DISPLAY | (LCD_ON_BLINK if blink else 0)
        self.hal_write_command(cmd)

    def hide(self):
        self.hal_write_command(LCD_ON_CTRL)

    def display_on(self, on=True):
        cmd = LCD_ON_CTRL | (LCD_ON_DISPLAY if on else 0)
        self.hal_write_command(cmd)

    def move_to(self, col, row):
        self.cursor_x = col
        self.cursor_y = row
        addr = col & 0x3F
        if row == 1:
            addr |= 0x40
        elif row == 2:
            addr |= 0x14
        elif row == 3:
            addr |= 0x54
        self.hal_write_command(LCD_SET_DDRAM | addr)

    def putchar(self, char):
        if char == '\n':
            self.cursor_y = (self.cursor_y + 1) % self.num_lines
            self.move_to(0, self.cursor_y)
        else:
            self.hal_write_data(ord(char))
            self.cursor_x += 1
            if self.cursor_x >= self.num_columns:
                self.cursor_x = 0
                self.cursor_y = (self.cursor_y + 1) % self.num_lines
                self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        for c in string:
            self.putchar(c)

    # Must be implemented by subclass:
    def hal_write_command(self, cmd):  # pragma: no cover
        raise NotImplementedError

    def hal_write_data(self, data):    # pragma: no cover
        raise NotImplementedError
```
- machine_i2c_lcd.py
```python
from time import sleep_us
from lcd_api import LcdApi, LCD_FUNCTION, LCD_FUNCTION_2L, LCD_ON_CTRL, LCD_ON_DISPLAY, LCD_ENTRY_MODE, LCD_ENTRY_INC

# PCF8574 bit masks (most common backpack wiring)
MASK_RS = 0x01
MASK_RW = 0x02
MASK_E  = 0x04
MASK_BL = 0x08  # backlight
SHIFT_DATA = 4  # D4..D7 on P4..P7

class I2cLcd(LcdApi):
    def __init__(self, i2c, i2c_addr, num_lines, num_columns, backlight=True):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.backlight = MASK_BL if backlight else 0
        self._byte(0)  # ensure something sent
        # Init sequence for 4-bit
        self._write_init_nibble(0x30)
        self._write_init_nibble(0x30)
        self._write_init_nibble(0x30)
        self._write_init_nibble(0x20)  # 4-bit mode

        # Function set: 2-line if needed
        func = LCD_FUNCTION | (LCD_FUNCTION_2L if num_lines > 1 else 0)
        self.hal_write_command(func)
        # Display ON, cursor/ blink off
        self.hal_write_command(LCD_ON_CTRL | LCD_ON_DISPLAY)
        # Entry mode set: increment, no shift
        self.hal_write_command(LCD_ENTRY_MODE | LCD_ENTRY_INC)
        self.clear()
        super().__init__(num_lines, num_columns)

    def backlight_on(self, on=True):
        self.backlight = MASK_BL if on else 0
        self._byte(0)

    def hal_write_command(self, cmd):
        self._write4(cmd, rs=False)

    def hal_write_data(self, data):
        self._write4(data, rs=True)

    # ---- low-level helpers ----
    def _write_init_nibble(self, nibble):
        self._nibble(nibble)
        self._strobe()

    def _write4(self, value, rs):
        high = (value & 0xF0)
        low  = ((value << 4) & 0xF0)
        self._nibble(high, rs)
        self._strobe()
        self._nibble(low, rs)
        self._strobe()

    def _nibble(self, nib, rs=False):
        data = (nib & 0xF0) | (MASK_RS if rs else 0) | self.backlight
        self._byte(data)

    def _strobe(self):
        self._byte(self._last | MASK_E)
        sleep_us(1)
        self._byte(self._last & ~MASK_E)
        sleep_us(50)

    def _byte(self, b):
        self._last = b
        self.i2c.writeto(self.i2c_addr, bytes([b]))
```
### 5. Upload Main Code
- The script should:
    - Connect to Wi-fi
    - Initialize sensors and LCD
    - Start the web server
### 6. Running the Server
1. Reset the ESP32
2. Wait for Wi-Fi connection
3. Note the **IP address** displayed in the serial monitor
4. Open a web browser and navigate
## Tasks and Checkpoints
### Task 1 - LED Control
Create a web page with two buttons: ON and OFF. <br>
When the ON button is clicked, the LED connected to GPIO2 turns ON. <br>
When the OFF button is clicked, the LED turns OFF. <br>
Evidence: https://drive.google.com/drive/folders/13wvs1C-SneUwzVL0l1u5jbmjctAps9cX?usp=sharing

### Task 2 - Sensor Read
Read data from the DHT11 temperature sensor and the ultrasonic distance sensor. <br>
Display the temperature and distance values on the web page. <br>
The values should automatically refresh every 1–2 seconds. <br>
<img width="1280" height="626" alt="image" src="https://github.com/user-attachments/assets/46d6f38b-8bb5-46be-9662-6941ef75080b" />

### Task 3 - Sensor
Add two buttons on the web page:
- Show Distance → Displays the measured distance on LCD line 1.
- Show Temp → Displays the temperature on LCD line 2. <br>
When each button is clicked, the corresponding sensor value should appear on the LCD.
<img width="1274" height="712" alt="Screenshot 2026-02-07 213746" src="https://github.com/user-attachments/assets/ec18c94a-f02a-45ee-ba7c-2984617fdac2" />

### Task 4 - Textbox
Add a textbox and a “Send” button on the web page. <br>
User types any custom text into the textbox. <br>
When Send is clicked, the text is displayed on the LCD. <br>
If the text is longer than 16 characters, it should scroll on the LCD. <br>
Evidence: https://drive.google.com/drive/folders/13wvs1C-SneUwzVL0l1u5jbmjctAps9cX?usp=sharing

### Wire Diagram
<img width="3970" height="8192" alt="ESP32 LCD HTTP Route Flow-2026-02-05-053536" src="https://github.com/user-attachments/assets/c5d4d7cc-3fd0-452a-8eeb-5a65f73bbad1" />
