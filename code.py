# SPDX-FileCopyrightText: 2023 Adafruit Industries
# SPDX-License-Identifier: MIT

from os import getenv
import time
import board
import busio
from digitalio import DigitalInOut
import terminalio
import adafruit_connection_manager
import adafruit_requests
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text import label

ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")

# Need to use HTTP, not HTTPS
JSON_URL = "http://azlm-crochet-frame-server.noshado.ws/"

matrix = Matrix(width=64, height=64)
display = matrix.display

text_area = label.Label(
    terminalio.FONT,
    text="STARTING",
    color=0xFFFFFF
)

text_area.x = 2
text_area.y = 6
display.root_group = text_area
display.refresh()

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

pool = adafruit_connection_manager.get_radio_socketpool(esp)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp)
requests = adafruit_requests.Session(pool, ssl_context)

wifi_test_result = "No data"
json_data = {}

text_area.text = "CONNECTING"
display.refresh()

try:
    while not esp.is_connected:
        try:
            esp.connect_AP(ssid, password)
        except OSError as e:
            print("could not connect to AP, retrying: ", e)
            text_area.text = "Retry WiFi"
            display.refresh()
            time.sleep(1)
            continue

    text_area.text = "CONNECTED"
    display.refresh()
    response = requests.get(JSON_URL)
    json_data = response.json()

except Exception as e:
    print("Error:", str(e))
    error_msg = str(e)
    if len(error_msg) > 15:
        error_msg = error_msg[:15] + "..."
    text_area.text = f"Error:\n{error_msg}"
    display.refresh()

display_items = []

for item in json_data:
    label = item.get('label', 'Unknown')
    value = item.get('value', '')
    color = item.get('color', 0xFFFFFF)

    display_text = f"{label}:\n{value}"

    display_items.append({
        "text": display_text,
        "color": color
    })

index = 0
while True:
    item = display_items[index]
    text_area.text = item["text"]
    text_area.color = item["color"]
    display.refresh()

    time.sleep(3)

    index = (index + 1) % len(display_items)
