#!/usr/bin/python
import smbus2 as smbus
import time
from threading import RLock, Thread
import pdb

lock = RLock()

class LCD:
    def __init__(self):
        # Define some device parameters
        self.message = "g"
        self.line = 0
        self.line = 0
        self.I2C_ADDR = 0x27     # I2C device address, if any error, change this address to 0x3f
        self.LCD_WIDTH = 16      # Maximum characters per line
        
        # Define some device constants
        self.LCD_CHR = 1     # Mode - Sending data
        self.LCD_CMD = 0     # Mode - Sending command
        
        self.LCD_LINE_1 = 0x80   # LCD RAM address for the 1st line
        self.LCD_LINE_2 = 0xC0   # LCD RAM address for the 2nd line
        self.LCD_LINE_3 = 0x94   # LCD RAM address for the 3rd line
        self.LCD_LINE_4 = 0xD4   # LCD RAM address for the 4th line
        
        self.LCD_BACKLIGHT = 0x08  # On
        
        self.ENABLE = 0b00000100     # Enable bit
        
        # Timing constants
        self.E_PULSE = 0.0001
        self.E_DELAY = 0.0001
        
        # Open I2C interface
        # bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
        self.bus = smbus.SMBus(1)    # Rev 2 Pi uses 1
        self.lcd_init()
        self.t_running = True
        self.t = Thread(target=self.lcd_string_thread)
        self.t.start()
    
    
    def lcd_init(self):
        # Initialise display
        self.lcd_byte(0x33, self.LCD_CMD)     # 110011 Initialise
        self.lcd_byte(0x32, self.LCD_CMD)     # 110010 Initialise
        self.lcd_byte(0x06, self.LCD_CMD)     # 000110 Cursor move direction
        self.lcd_byte(0x0C, self.LCD_CMD)     # 001100 Display On,Cursor Off, Blink Off
        self.lcd_byte(0x28, self.LCD_CMD)     # 101000 Data length, number of lines, font size
        self.lcd_byte(0x01, self.LCD_CMD)     # 000001 Clear display
        time.sleep(self.E_DELAY)
    
    
    def lcd_byte(self, bits, mode):
        # Send byte to data pins
        # bits = the data
        # mode = 1 for data
        #        0 for command
    
        bits_high = mode | (bits & 0xF0) | self.LCD_BACKLIGHT
        bits_low = mode | ((bits << 4) & 0xF0) | self.LCD_BACKLIGHT
    
        # High bits
        self.bus.write_byte(self.I2C_ADDR, bits_high)
        self.lcd_toggle_enable(bits_high)
    
        # Low bits
        self.bus.write_byte(self.I2C_ADDR, bits_low)
        self.lcd_toggle_enable(bits_low)
    
    
    def lcd_toggle_enable(self, bits):
        # Toggle enable
        time.sleep(self.E_DELAY)
        self.bus.write_byte(self.I2C_ADDR, (bits | self.ENABLE))
        time.sleep(self.E_PULSE)
        self.bus.write_byte(self.I2C_ADDR, (bits & ~self.ENABLE))
        time.sleep(self.E_DELAY)
    
    
    def lcd_string(self, message, line):
        # Send string to display
        lock.acquire()
        self.message = message
        self.line = line
        lock.release()
    def lcd_string_thread(self):
        while self.t_running:
            lock.acquire()
            assert(self.message)
            self.message = self.message.ljust(self.LCD_WIDTH, " ")
        
            self.lcd_byte(self.line, self.LCD_CMD)
        
            for i in range(self.LCD_WIDTH):
                self.lcd_byte(ord(self.message[i]), self.LCD_CHR)
            # time.sleep(0.2)
            lock.release()


if __name__ == '__main__':
    lcd = LCD()

    a = 0 
    while True:
        # Send some test
        a  = a +1
        lcd.lcd_string("H" + str(a), lcd.LCD_LINE_1)
        lcd.lcd_string("d", lcd.LCD_LINE_2)
        # time.sleep(0.1)
