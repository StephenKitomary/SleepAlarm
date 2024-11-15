import time
from machine import Pin
from clock import display_clock
from menu import display_menu, handle_buttons

# Buttons
button_select = Pin(18, Pin.IN, Pin.PULL_UP)  # Select/OK button
button_back = Pin(21, Pin.IN, Pin.PULL_UP)  # Back button

# State tracking
is_menu_active = False
selected_index = 0

def main_loop():
    """Main loop to manage transitions between clock and menu."""
    global is_menu_active, selected_index

    while True:
        if is_menu_active:
            # Handle menu logic
            handle_buttons()
            if not button_back.value():  # Back button pressed
                print("Returning to clock...")
                is_menu_active = False
        else:
            # Display the clock and wait for the menu button
            display_clock(button_select)  # Pass button_select to display_clock
            print("Switching to menu...")
            is_menu_active = True
            display_menu(selected_index)

# Run the main loop
if __name__ == "__main__":
    main_loop()

