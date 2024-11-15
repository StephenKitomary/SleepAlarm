from machine import Pin, I2C, RTC
from ssd1306 import SSD1306_I2C
import network
import urequests
import time

# WiFi Details
SSID = "Bennington Public"
PASSWORD = ""

# Constants
I2C_SDA = 0
I2C_SCL = 1
API_KEY = "dc32fe9d532562bf4c62e91f37cce2d3"
CITY_ID = "5233742"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Initialize I2C and OLED
i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
rtc = RTC()  # Initialize RTC

def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    print("Connecting to Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(1)
        print("Trying to connect...")
    
    print("Connected to Wi-Fi")
    print("IP Address:", wlan.ifconfig()[0])

def get_weather():
    try:
        url = f"{BASE_URL}?id={CITY_ID}&appid={API_KEY}&units=metric"
        response = urequests.get(url)
        weather_data = response.json()
        temp = float(weather_data['main']['temp'])  # Convert to float
        response.close()
        return temp
    except Exception as e:
        print("Error fetching weather data:", e)
        return None

def fetch_time_from_api():
    try:
        url = "http://worldtimeapi.org/api/timezone/America/New_York"
        response = urequests.get(url)
        time_data = response.json()
        response.close()
        
        # Parse the datetime string
        datetime_str = time_data['datetime']  # Example: "2024-11-14T08:45:30.123456+00:00"
        date_part, time_part = datetime_str.split("T")  # Split into date and time
        time_part = time_part.split(".")[0]  # Remove fractional seconds (e.g., "08:45:30")
        hour, minute, second = map(int, time_part.split(":"))  # Extract hours, minutes, seconds
        year, month, day = map(int, date_part.split("-"))  # Extract year, month, day

        # Set the RTC with the parsed time
        rtc.datetime((year, month, day, 0, hour, minute, second, 0))

        # Return the date and time string for display
        time_string = f"{hour:02}:{minute:02}:{second:02}"
        return date_part, time_string
    except Exception as e:
        print("Error fetching time data:", e)
        return None, None


def get_time_from_rtc():
    datetime = rtc.datetime()
    date = f"{datetime[0]}-{datetime[1]:02}-{datetime[2]:02}"
    time_string = f"{datetime[4]:02}:{datetime[5]:02}:{datetime[6]:02}"
    return date, time_string

def display_data(date, time, temp, alarm_status="OFF"):
    # Clear the screen
    oled.fill(0)
    
    # Display date (top center, yellow stripe)
    date_x = (128 - len(date) * 8) // 2
    oled.text(date, date_x, 0)
    
    # Decorative divider below date
    oled.hline(0, 10, 128, 1)
    
    # Display time (large and centered)
    time_x = (128 - len(time) * 8) // 2
    oled.text(time, time_x, 20)
    
    # Display decorative lines around time
    oled.hline(0, 30, 128, 1)
    oled.hline(0, 40, 128, 1)
    
    # Display temperature and alarm status (centered at the bottom)
    bottom_text = f"T:{temp:.1f}C A:{alarm_status}"
    bottom_x = (128 - len(bottom_text) * 8) // 2
    oled.text(bottom_text, bottom_x, 50)
    
    # Update the screen
    oled.show()

def display_clock(button_select):
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        connect_to_wifi(SSID, PASSWORD)
    
    # Fetch time from API and set RTC
    date, time_string = fetch_time_from_api()
    
    if not date or not time_string:
        print("Failed to fetch initial time. Exiting clock function.")
        return
    
    # Track last weather update
    last_weather_minute = -1
    temp = None
    first_run = True

    while True:
        if not button_select.value():
            print("Exiting clock to menu...")
            return

        # Get time from RTC
        date, time_data = get_time_from_rtc()

        # Extract the minute value from the current time
        current_minute = int(time_data.split(":")[1])

        # Fetch weather on first run or at the start of a new hour
        if first_run or (current_minute == 0 and last_weather_minute != current_minute):
            temp = get_weather()
            last_weather_minute = current_minute
            first_run = False

        # Display the time and weather
        display_data(date, time_data, temp or 0)

        # Non-blocking wait for 1 second
        for _ in range(100):  # 100 iterations of 10 ms = 1 second
            if not button_select.value():
                print("Button pressed during clock update.")
                return
            time.sleep(0.01)

