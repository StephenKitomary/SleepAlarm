from machine import Pin, I2C, PWM
from ssd1306 import SSD1306_I2C
import time

# OLED setup
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# Menu setup
menu_items = ["Alarms", "Pomodoro", "Timer", "Data", "Settings"]
selected_index = 0  # Keeps track of the currently selected item

# Button setup
button_up = Pin(19, Pin.IN, Pin.PULL_UP)  # Button for moving up
button_down = Pin(20, Pin.IN, Pin.PULL_UP)  # Button for moving down

# Buzzer setup
buzzer = PWM(Pin(16))  # Buzzer connected to GPIO 16

def buzz():
    """Emit a short beep."""
    buzzer.freq(500)  # Set frequency to 1000 Hz
    buzzer.duty_u16(5000)  # Set duty cycle
    time.sleep(0.1)  # Beep duration
    buzzer.duty_u16(0)  # Turn off the buzzer

def display_menu(selected_index):
    """Displays the menu on the OLED."""
    oled.fill(0)  # Clear the screen
    oled.text("Menu", 48, 0)  # Display title centered at the top

    # Define positions for menu items
    positions = [16, 28, 40]  # Y positions for the 3 items

    # Display all menu items in their respective positions
    for i, y in enumerate(positions):
        item_index = selected_index - 1 + i  # Map positions to items
        if 0 <= item_index < len(menu_items):
            if i == 1:  # Highlight the middle item
                oled.fill_rect(0, y, 128, 12, 1)  # Draw highlight rectangle
                oled.text(menu_items[item_index], 32, y, 0)  # Inverted text color
            else:
                oled.text(menu_items[item_index], 32, y, 1)  # Normal text color

    oled.show()

def handle_buttons():
    """Handles button presses for navigation."""
    global selected_index
    
    if not button_up.value():  # Button up pressed
        selected_index = max(0, selected_index - 1)  # Prevent going out of bounds
        buzz()  # Provide haptic feedback
        display_menu(selected_index)
        time.sleep(0.2)  # Debounce delay
    
    if not button_down.value():  # Button down pressed
        selected_index = min(len(menu_items) - 1, selected_index + 1)
        buzz()  # Provide haptic feedback
        display_menu(selected_index)
        time.sleep(0.2)  # Debounce delay



