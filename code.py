from os import getenv
import board
import busio
from digitalio import DigitalInOut
import adafruit_connection_manager
import adafruit_requests
from adafruit_esp32spi import adafruit_esp32spi
import time
import board
import random
from adafruit_matrixportal.matrix import Matrix
import displayio
import gc

# Configuration
REQUEST_TIMEOUT = 0.1  # Maximum time to spend on network operations per frame

ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")
api_key = getenv("AZLM_CROCHET_FRAME_SERVER_API_KEY")

DATA_URL = f"http://azlm-crochet-frame-server.noshado.ws/api/settings?apiKey={api_key}"

# Network setup
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

pool = adafruit_connection_manager.get_radio_socketpool(esp)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp)
requests = adafruit_requests.Session(pool, ssl_context)

def fetch_settings():
    try:
        if not esp.is_connected:
            esp.connect_AP(ssid, password)
        r = requests.get(DATA_URL)
        new_data = r.json()
        r.close()
        return new_data
    except Exception as e:
        print("Error fetching settings:", e)
        return None

# Initial settings fetch
while True:
    try:
        initial_data = fetch_settings()
        if initial_data:
            break
    except Exception as e:
        print("Initial settings fetch failed, retrying:", e)
        time.sleep(1)

DEFAULT_COLORS = [
    16711680,  # Red
    16744448,  # Orange-Red
    16776960,  # Yellow
    65280,     # Green
    65535,     # Cyan
    255,       # Blue
    8388863,   # Light Blue
    16711935,  # Magenta
    16777215,  # White
    16761024,  # Orange
    12648384,  # Pink
    12632319   # Light Pink
]

NUM_SPARKLES = initial_data.get('num_sparkles', 10)
SPARKLE_SIZE = initial_data.get('sparkle_size', 1)
RAINBOW_COLORS = initial_data.get('colors', DEFAULT_COLORS)
SPEED = initial_data.get('speed', 10)

def rgb_to_gbr(color):
    # Extract RGB components
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    # Combine in BGR format
    return (b << 16) | (g << 8) | r

MATRIX_WIDTH = 64
MATRIX_HEIGHT = 64
matrix = Matrix(width=MATRIX_WIDTH, height=MATRIX_HEIGHT)
display = matrix.display

root_group = displayio.Group()
display.root_group = root_group

sparkles_group = displayio.Group()
root_group.append(sparkles_group)

# Add padding to keep sparkles away from edges
EDGE_PADDING = 0

class Sparkle:
    def __init__(self):
        self.current_x = random.randint(EDGE_PADDING, MATRIX_WIDTH - SPARKLE_SIZE - EDGE_PADDING)
        self.current_y = random.randint(EDGE_PADDING, MATRIX_HEIGHT - SPARKLE_SIZE - EDGE_PADDING)
        self.tilegrid = None
        self.color_index = random.randint(0, len(RAINBOW_COLORS) - 1)
    
    def update(self):
        # Keep sparkles away from edges
        self.current_x = random.randint(EDGE_PADDING, MATRIX_WIDTH - SPARKLE_SIZE - EDGE_PADDING)
        self.current_y = random.randint(EDGE_PADDING, MATRIX_HEIGHT - SPARKLE_SIZE - EDGE_PADDING)
        
        # Update color
        self.color_index = (self.color_index + 1) % len(RAINBOW_COLORS)
        if self.tilegrid:
            self.tilegrid.x = self.current_x
            self.tilegrid.y = self.current_y
            self.tilegrid.pixel_shader = palettes[self.color_index]

# Create bitmap for sparkle
def create_sparkle_bitmap(size):
    bitmap = displayio.Bitmap(size, size, 2)
    if size == 1:
        bitmap[0, 0] = 1
    else:
        for x in range(size):
            for y in range(size):
                bitmap[x, y] = 1
    return bitmap

sparkle_bitmap = create_sparkle_bitmap(SPARKLE_SIZE)

# Create a palette for each color to avoid constant palette updates
palettes = []
for color in RAINBOW_COLORS:
    pal = displayio.Palette(2)
    pal[0] = 0x000000  # Background color (black)
    pal[1] = rgb_to_gbr(color)  # Convert RGB to BGR
    palettes.append(pal)

# Keep track of currently active colors
active_colors = set()

def get_new_color():
    return 0xFFFF00  # Always return yellow

sparkle_pool = [Sparkle() for _ in range(NUM_SPARKLES)]

for sparkle in sparkle_pool:
    sparkle.tilegrid = displayio.TileGrid(
        sparkle_bitmap,
        pixel_shader=palettes[sparkle.color_index],
        x=sparkle.current_x,
        y=sparkle.current_y
    )
    sparkles_group.append(sparkle.tilegrid)

while True:
    try:
        # Update all sparkles
        for sparkle in sparkle_pool:
            sparkle.update()
        
        # Convert milliseconds to seconds for sleep    
        time.sleep(SPEED / 1000)
            
    except Exception as e:
        print("Error:", e)
        time.sleep(0.5)