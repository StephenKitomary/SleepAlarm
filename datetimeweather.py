from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import network
import urequests
import time

#WIFI Details
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
        print(weather_data)
        temp_min = weather_data['main']['temp_min']
        temp_max = weather_data['main']['temp_max']
    
        response.close()
        return temp_min, temp_max
    except Exception as e:
        print("Error fetching weather data:", e)
        return None, None


#get time for Vermont
#According to the worldtime API, Vernmont doesnt exist, so will use New York instead.
    
def get_time():
    try:
        url = "http://worldtimeapi.org/api/timezone/America/New_York"
        response = urequests.get(url)
        time_data = response.json()
        datetime = time_data['datetime']
        response.close()
        # Extract date and time 
        print(f"here is a json file for datetime just for troubleshooting: {datetime}")
        date = datetime.split("T")[0]
        #time data is in the format of hh:mm:ss, but prefer to take only hh:mm 
        time_list = datetime.split("T")[1].split(":")[0:2]
        time_string = ":".join([str(x) for x in time_list])
        #We return a tupple of date and time
        return date, time
    except Exception as e: 
        print("Error fetching time data:", e)
        #returning also a tupple of None, None to match the valid structure
        return None, None

# Function to display data on OLED
def display_data(date, time, temp_min, temp_max):

    """We could create another function to determine the starting point of a character to display on a screen"""
    #Clear the Screen
    oled.fill(0)  
    oled.text(f"{date}", 0, 0)
    
    # Display time
    oled.text(f"{time}", 0, 20)
    
    # Display weather data
    if temp_min is not None and temp_max is not None:
        oled.text(f"Min: {temp_min}C", 0, 28)
        oled.text(f"Max: {temp_max}C", 0, 40)
    else:
        oled.text("Weather: N/A", 0, 28)

    oled.show()

#Connect to WiFi
connect_to_wifi(SSID, PASSWORD)


while True:
    # Fetch time, date, and weather data
    date, time_data = get_time()
    temp_min, temp_max = get_weather()

    
    if date and time_data:
        display_data(date, time_data, temp_min, temp_max)

    time.sleep(60)  # Update every 60 seconds