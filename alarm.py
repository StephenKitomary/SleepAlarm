from machine import Pin, I2C, PWM
import network
import time
from umqtt.simple import MQTTClient
import ssl
import ubinascii
import random
import ssd1306

# ------------------ Configuration ------------------
WIFI_SSID = "Benningtonxxxx"
WIFI_PASS = ""

MQTT_BROKER = "6191b55xxxxxxxxxxx71.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "StephenKitomary"
MQTT_PASSWORD = "xxxxxxxxxxxx"
MQTT_CLIENT_ID = "pico-alarm-client" 

# MQTT Topics
TOPIC_ALARM_START = b"alarm/start"
TOPIC_ALARM_TARGET = b"alarm/targetLocation"
TOPIC_ESP32_SCAN = b"esp32/scan"
TOPIC_ESP32_LOCATION = b"esp32/location"

# I2C Pins for OLED
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1

# Buzzer Pin
BUZZER_PIN = 16

# Possible locations
TARGET_LOCATIONS = ["bathroom", "kitchen", "otherroom"]

# ------------------ Hardware Setup ------------------

i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)


buzzer = PWM(Pin(BUZZER_PIN))
buzzer.duty_u16(0)  


alarm_active = False
target_location = None
client = None

def update_oled(line1="", line2="", line3="", line4=""):
   
    oled.fill(0)
    if line1: oled.text(line1, 0, 0)
    if line2: oled.text(line2, 0, 16)
    if line3: oled.text(line3, 0, 32)
    if line4: oled.text(line4, 0, 48)
    oled.show()

def connect_to_wifi():
   
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)

    print("Connecting to Wi-Fi...")
    update_oled("Connecting", "to Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(1)
        print("Trying to connect...")
    print("Connected to Wi-Fi")
    ip = wlan.ifconfig()[0]
    print("IP Address:", ip)
    update_oled("Wi-Fi connected", ip)

def mqtt_callback(topic, msg):
    global alarm_active, target_location
    # Handle messages from ESP32 location
    if topic == TOPIC_ESP32_LOCATION:
        detected_location = msg.decode()
        print("Detected NFC location:", detected_location)
        update_oled("NFC Detected:", detected_location)
        # If alarm is active and this is the correct location
        if alarm_active and detected_location == target_location:
            alarm_active = False
            buzzer.duty_u16(0)  
            client.publish(TOPIC_ALARM_START, "OFF")
            print("Alarm deactivated - reached correct location:", target_location)
            update_oled("Alarm off!", "Location OK!")
            time.sleep(2)
            update_oled("System Idle")

def connect_to_mqtt():
    """Connect to the MQTT broker with SSL."""
    print("Connecting to MQTT Broker...")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_NONE  
    new_client = MQTTClient(
        client_id=MQTT_CLIENT_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASSWORD,
        keepalive=60,
        ssl=context
    )
    new_client.set_callback(mqtt_callback)
    new_client.connect()
    new_client.subscribe(TOPIC_ESP32_LOCATION)
    print(f"Subscribed to topic: {TOPIC_ESP32_LOCATION.decode()}")
    update_oled("MQTT Connected", "Subscribed:", "esp32/location")
    return new_client

def trigger_alarm():
    global alarm_active, target_location
    target_location = random.choice(TARGET_LOCATIONS)
    alarm_active = True

  
    buzzer.freq(500)
    buzzer.duty_u16(5000)  # Turn the buzzer on

    # Publish alarm start and target location
    client.publish(TOPIC_ALARM_START, "ON")
    client.publish(TOPIC_ALARM_TARGET, target_location)
    print("Alarm triggered! Target location:", target_location)
    update_oled("ALARM TRIGGERED!", "Target:", target_location, "Scan NFC to stop")

    # Tell the ESP32 to start scanning
    client.publish(TOPIC_ESP32_SCAN, "start")


connect_to_wifi()
client = connect_to_mqtt()

print("Waiting 5 seconds before triggering alarm...")
update_oled("System Idle", "Alarm in 5s...")
time.sleep(5)
trigger_alarm()

while True:
    client.check_msg()
    time.sleep(0.1)

