from machine import Pin, I2C, RTC
from ssd1306 import SSD1306_I2C
import network
import urequests
import time

# Wi-Fi credentials --hiding them for now
SSID = "Bennington XXXXXX"
PASSWORD = "xxxxxx"

# I2C pins and the weather API details- hiding my API for public
I2C_SDA = 0
I2C_SCL = 1
API_KEY = "dc32fe9d53256xxxxxxxxxxxxxxxx"
CITY_ID = "5233742"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Here we configure I2C and the OLED display, plus the RTC
i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
rtc = RTC()

def connect_to_wifi(ssid, password):
    # Here we try to connect to the given Wi-Fi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    print("Connecting to Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(1)
        print("Still trying...")
    print("Connected to Wi-Fi at:", wlan.ifconfig()[0])

def get_weather():
    # Here we reach out to the weather API
    try:
        url = f"{BASE_URL}?id={CITY_ID}&appid={API_KEY}&units=metric"
        response = urequests.get(url)
        weather_data = response.json()
        temp = float(weather_data['main']['temp'])
        response.close()
        return temp
    except Exception as e:
        print("Couldn't get weather:", e)
        return None

def fetch_time_from_api():
    # Here we get the current time from a time API and use it to set the RTC
    try:
        url = "http://worldtimeapi.org/api/timezone/America/New_York"
        response = urequests.get(url)
        time_data = response.json()
        response.close()
        
        datetime_str = time_data['datetime']
        date_part, time_part = datetime_str.split("T")
        time_part = time_part.split(".")[0]
        hour, minute, second = map(int, time_part.split(":"))
        year, month, day = map(int, date_part.split("-"))

        # Here we set our RTC clock with the fetched time
        rtc.datetime((year, month, day, 0, hour, minute, second, 0))

        time_string = f"{hour:02}:{minute:02}:{second:02}"
        return date_part, time_string
    except Exception as e:
        print("Couldn't get time:", e)
        return None, None

def get_time_from_rtc():
    #  read the current time from RTC
    datetime = rtc.datetime()
    date = f"{datetime[0]}-{datetime[1]:02}-{datetime[2]:02}"
    time_string = f"{datetime[4]:02}:{datetime[5]:02}:{datetime[6]:02}"
    return date, time_string

def display_data(date, time, temp, alarm_status="OFF"):
    #clear the screen before drawing new data
    oled.fill(0)
    
    # Date at the top
    date_x = (128 - len(date) * 8) // 2
    oled.text(date, date_x, 0)
    oled.hline(0, 10, 128, 1)
    
    # Time in the middle, nice and centered
    time_x = (128 - len(time) * 8) // 2
    oled.text(time, time_x, 20)
    oled.hline(0, 30, 128, 1)
    oled.hline(0, 40, 128, 1)
    
    # Temperature and alarm info at the bottom
    bottom_text = f"T:{temp:.1f}C A:{alarm_status}"
    bottom_x = (128 - len(bottom_text) * 8) // 2
    oled.text(bottom_text, bottom_x, 50)
    oled.show()

def display_clock(button_select):
    # we ensure we're online first
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        connect_to_wifi(SSID, PASSWORD)
    
    # Let's get the initial time from the API and set the clock
    date, time_string = fetch_time_from_api()
    if not date or not time_string:
        print("No time data retrieved. Returning...")
        return
    
    # We'll remember when we last updated the weather
    last_weather_minute = -1
    temp = None
    first_run = True

    while True:
        if not button_select.value():
            print("Exiting clock mode...")
            return

        # Get current time from RTC each loop
        date, time_data = get_time_from_rtc()
        current_minute = int(time_data.split(":")[1])

        # We update the weather on first run or every new hour
        if first_run or (current_minute == 0 and last_weather_minute != current_minute):
            temp = get_weather()
            last_weather_minute = current_minute
            first_run = False

        display_data(date, time_data, temp or 0)

        # Wait one second, but check if the button is pressed
        for _ in range(100):
            if not button_select.value():
                print("Button pressed, returning to menu.")
                return
            time.sleep(0.01)
