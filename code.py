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
POLLING_INTERVAL = 5  # Check for new settings every 5 seconds
REQUEST_TIMEOUT = 0.1  # Maximum time to spend on network operations per frame

# Polling states
POLL_IDLE = 0
POLL_CONNECTING = 1
POLL_FETCHING = 2

ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")

DATA_URL = "http://azlm-crochet-frame-server.noshado.ws/api/settings"

# Network setup
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

pool = adafruit_connection_manager.get_radio_socketpool(esp)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp)
requests = adafruit_requests.Session(pool, ssl_context)

class SettingsPoller:
    def __init__(self):
        self.state = POLL_IDLE
        self.last_poll_time = time.monotonic()
        self.response = None
    
    def update(self):
        current_time = time.monotonic()
        
        # Only start polling if enough time has passed
        if self.state == POLL_IDLE:
            if current_time - self.last_poll_time >= POLLING_INTERVAL:
                self.state = POLL_CONNECTING
                return None
            return None
            
        # Handle connection state
        if self.state == POLL_CONNECTING:
            try:
                if not esp.is_connected:
                    esp.connect_AP(ssid, password)
                self.state = POLL_FETCHING
            except Exception as e:
                print("Connection error:", e)
                self.state = POLL_IDLE
                self.last_poll_time = current_time
            return None
            
        # Handle fetching state
        if self.state == POLL_FETCHING:
            try:
                self.response = requests.get(DATA_URL)
                new_data = self.response.json()
                self.response.close()
                self.response = None
                self.state = POLL_IDLE
                self.last_poll_time = current_time
                return new_data
            except Exception as e:
                print("Fetch error:", e)
                if self.response:
                    self.response.close()
                    self.response = None
                self.state = POLL_IDLE
                self.last_poll_time = current_time
            return None

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

NUM_SPARKLES = initial_data['num_sparkles']
FRAME_RATE = initial_data['frame_rate']
TRANSITION_TIME = initial_data['transition_time']
SPARKLE_SIZE = initial_data['sparkle_size']
NUM_PALETTES = initial_data['num_palettes']

MATRIX_WIDTH = 64
MATRIX_HEIGHT = 64
matrix = Matrix(width=MATRIX_WIDTH, height=MATRIX_HEIGHT)
display = matrix.display

root_group = displayio.Group()
display.root_group = root_group

sparkles_group = displayio.Group()
root_group.append(sparkles_group)

def create_sparkle_bitmap(size):
    bitmap = displayio.Bitmap(size, size, 2)
    for x in range(size):
        for y in range(size):
            bitmap[x, y] = 1
    return bitmap

def create_sparkle(bitmap, palette_index):
    sparkle = Sparkle()
    sparkle.tilegrid = displayio.TileGrid(
        bitmap,
        pixel_shader=sparkle_palettes[sparkle.palette_index],
        x=sparkle.current_x,
        y=sparkle.current_y
    )
    return sparkle

sparkle_bitmap = create_sparkle_bitmap(SPARKLE_SIZE)

RAINBOW_COLORS = [
    0xFF0000,  # Red
    0xFF8000,  # Orange
    0xFFFF00,  # Yellow
    0x00FF00,  # Green
    0x00FFFF,  # Cyan
    0x0000FF,  # Blue
    0x8000FF,  # Purple
    0xFF00FF,  # Magenta
    0xFFFFFF,  # White
    0xFFC0C0,  # Light Pink
    0xC0FFC0,  # Light Green
    0xC0C0FF,  # Light Blue
]

last_frame_time = time.monotonic()
last_poll_time = time.monotonic()
frame_interval = 1.0 / FRAME_RATE

def hex_to_rgb(hex_color):
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    return (r, g, b)

def rgb_to_hex(r, g, b):
    return (r << 16) | (g << 8) | b

def lerp(start, end, t):
    return int(start + (end - start) * t)

def lerp_color(start_color, end_color, t):
    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)
    
    r = lerp(start_rgb[0], end_rgb[0], t)
    g = lerp(start_rgb[1], end_rgb[1], t)
    b = lerp(start_rgb[2], end_rgb[2], t)
    
    return rgb_to_hex(r, g, b)

sparkle_palettes = []
current_colors = []
target_colors = []

for _ in range(NUM_PALETTES):
    palette = displayio.Palette(2)
    palette[0] = 0x000000
    current_color = random.choice(RAINBOW_COLORS)
    target_color = random.choice(RAINBOW_COLORS)
    palette[1] = current_color
    sparkle_palettes.append(palette)
    current_colors.append(current_color)
    target_colors.append(target_color)

class Sparkle:
    def __init__(self):
        self.current_x = random.randint(0, MATRIX_WIDTH - SPARKLE_SIZE)
        self.current_y = random.randint(0, MATRIX_HEIGHT - SPARKLE_SIZE)
        self.target_x = random.randint(0, MATRIX_WIDTH - SPARKLE_SIZE)
        self.target_y = random.randint(0, MATRIX_HEIGHT - SPARKLE_SIZE)
        self.tilegrid = None
        self.palette_index = random.randrange(NUM_PALETTES)
    
    def update_position(self, progress):
        x = lerp(self.current_x, self.target_x, progress)
        y = lerp(self.current_y, self.target_y, progress)
        if self.tilegrid:
            self.tilegrid.x = int(x)
            self.tilegrid.y = int(y)
    
    def set_new_target(self):
        self.current_x = self.target_x
        self.current_y = self.target_y
        self.target_x = random.randint(0, MATRIX_WIDTH - SPARKLE_SIZE)
        self.target_y = random.randint(0, MATRIX_HEIGHT - SPARKLE_SIZE)
        self.palette_index = random.randrange(NUM_PALETTES)

sparkle_pool = [Sparkle() for _ in range(NUM_SPARKLES)]

for sparkle in sparkle_pool:
    sparkle.tilegrid = displayio.TileGrid(
        sparkle_bitmap,
        pixel_shader=sparkle_palettes[sparkle.palette_index],
        x=sparkle.current_x,
        y=sparkle.current_y
    )
    sparkles_group.append(sparkle.tilegrid)

color_change_timer = 0

settings_poller = SettingsPoller()

while True:
    try:
        current_time = time.monotonic()
        elapsed = current_time - last_frame_time
        
        # Non-blocking settings poll
        new_settings = settings_poller.update()
        if new_settings:
            old_sparkle_size = SPARKLE_SIZE
            
            NUM_SPARKLES = new_settings['num_sparkles']
            FRAME_RATE = new_settings['frame_rate']
            TRANSITION_TIME = new_settings['transition_time']
            SPARKLE_SIZE = new_settings['sparkle_size']
            NUM_PALETTES = new_settings['num_palettes']
            frame_interval = 1.0 / FRAME_RATE
            
            # If sparkle size changed, recreate all sparkles
            if old_sparkle_size != SPARKLE_SIZE:
                print("Sparkle size changed, recreating sparkles...")
                # Create new bitmap
                sparkle_bitmap = create_sparkle_bitmap(SPARKLE_SIZE)
                
                # Remove all existing sparkles
                while len(sparkles_group):
                    sparkles_group.pop()
                
                # Clear sparkle pool
                sparkle_pool.clear()
                
                # Create new sparkles
                for _ in range(NUM_SPARKLES):
                    new_sparkle = create_sparkle(sparkle_bitmap, random.randrange(NUM_PALETTES))
                    sparkle_pool.append(new_sparkle)
                    sparkles_group.append(new_sparkle.tilegrid)
            else:
                # Just update sparkle count if size hasn't changed
                while len(sparkle_pool) < NUM_SPARKLES:
                    new_sparkle = create_sparkle(sparkle_bitmap, random.randrange(NUM_PALETTES))
                    sparkle_pool.append(new_sparkle)
                    sparkles_group.append(new_sparkle.tilegrid)
                
                while len(sparkle_pool) > NUM_SPARKLES:
                    removed_sparkle = sparkle_pool.pop()
                    sparkles_group.remove(removed_sparkle.tilegrid)
        
        if elapsed >= frame_interval:
            color_change_timer += elapsed
            transition_progress = min(color_change_timer / TRANSITION_TIME, 1.0)
            
            if transition_progress >= 1.0:
                color_change_timer = 0
                for i in range(NUM_PALETTES):
                    current_colors[i] = target_colors[i]
                    target_colors[i] = random.choice(RAINBOW_COLORS)
                for sparkle in sparkle_pool:
                    sparkle.set_new_target()
                transition_progress = 0
            
            for i, palette in enumerate(sparkle_palettes):
                interpolated_color = lerp_color(
                    current_colors[i],
                    target_colors[i],
                    transition_progress
                )
                palette[1] = interpolated_color
            
            for sparkle in sparkle_pool:
                sparkle.update_position(transition_progress)
            
            display.refresh()
            
            gc.collect()

            last_frame_time = current_time
            
    except Exception as e:
        print("Error:", e)
        time.sleep(0.5)