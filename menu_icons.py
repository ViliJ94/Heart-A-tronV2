#Import stuff
from machine import UART, Pin, I2C, Timer, ADC
import time
from ssd1306 import SSD1306_I2C
import framebuf


#Oled stuff
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

#Heart meant for HR, analysis for analysis, wifi for kubios, clock for history
heart = bytearray([0x66, 0x99, 0x81, 0x81, 0x81, 0x42, 0x24, 0x18])
wifi = bytearray([0x00, 0x00, 0x7C, 0x82, 0x00, 0x38, 0x00, 0x10])
analysis = bytearray([0x04, 0x0C, 0x0A, 0xD3, 0x30, 0x20, 0x00, 0x00])
clock = bytearray([0x3C, 0x42, 0x91, 0x91, 0x9D, 0x81, 0x42, 0x3C])


oled.fill(0)
fb_heart = framebuf.FrameBuffer(heart, 8, 8, framebuf.MONO_HLSB)
fb_wifi = framebuf.FrameBuffer(wifi, 8, 8, framebuf.MONO_HLSB)
fb_analysis = framebuf.FrameBuffer(analysis, 8, 8, framebuf.MONO_HLSB)
fb_clock = framebuf.FrameBuffer(clock,8,8,framebuf.MONO_HLSB)
oled.blit(fb_heart,10,10)
oled.blit(fb_wifi,10,20)
oled.blit(fb_analysis,20,10)
oled.blit(fb_clock,20,20)

oled.show()