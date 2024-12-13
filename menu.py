from machine import Pin, I2C, PWM
from ssd1306 import SSD1306_I2C
import time

# Setting up the display
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# Defining the menu items and the selected index
menu_items = ["Alarms", "Pomodoro", "Timer", "Data", "Settings"]
selected_index = 0

# Configuring buttons for navigation
button_up = Pin(19, Pin.IN, Pin.PULL_UP)
button_down = Pin(20, Pin.IN, Pin.PULL_UP)

# Preparing the buzzer for feedback
buzzer = PWM(Pin(16))

def buzz():
   
    buzzer.freq(500)
    buzzer.duty_u16(5000)
    time.sleep(0.1)
    buzzer.duty_u16(0)

def display_menu(selected_index):
  
    oled.fill(0)
    oled.text("Menu", 48, 0)

    # Positions for three visible items at a time: one above, one highlighted, one below
    positions = [16, 28, 40]

    # Display each item based on the selected index
    for i, y in enumerate(positions):
        item_index = selected_index - 1 + i
        if 0 <= item_index < len(menu_items):
            if i == 1:  # The middle one is the currently selected item
                oled.fill_rect(0, y, 128, 12, 1)
                oled.text(menu_items[item_index], 32, y, 0)
            else:
                oled.text(menu_items[item_index], 32, y, 1)

    oled.show()

def handle_buttons():
    
    global selected_index
    
    if not button_up.value():
        # Moving upwards through the menu
        selected_index = max(0, selected_index - 1)
        buzz()
        display_menu(selected_index)
        time.sleep(0.2) 
    
    if not button_down.value():
        # Moving downwards through the menu
        selected_index = min(len(menu_items) - 1, selected_index + 1)
        buzz()
        display_menu(selected_index)
        time.sleep(0.2)  


