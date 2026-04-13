from machine import Pin, SPI
import os
import sdcard

def init_sd():
    try:
        spi = SPI(1, baudrate=1000000,
                  sck=Pin(14), mosi=Pin(15), miso=Pin(2))

        cs = Pin(13)

        print("Initializing SD card...")

        sd = sdcard.SDCard(spi, cs)
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")

        print("SD Card Mounted OK")
        print("Files:", os.listdir("/sd"))

    except Exception as e:
        print("SD Card Failed:", e)
