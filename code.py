# SPDX-FileCopyrightText: 2023 Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import random
from adafruit_matrixportal.matrix import Matrix
import displayio
import gc

MATRIX_WIDTH = 64
MATRIX_HEIGHT = 64
FRAME_RATE = 1  # Target frames per second

matrix = Matrix(width=MATRIX_WIDTH, height=MATRIX_HEIGHT)
display = matrix.display

# Create a root group for all display elements
root_group = displayio.Group()
display.root_group = root_group

# Create a group for sparkle effect
sparkles_group = displayio.Group()
root_group.append(sparkles_group)

# Create a bitmap for a small sparkle (1x1 pixel)
sparkle_bitmap = displayio.Bitmap(1, 1, 2)
sparkle_bitmap[0, 0] = 1  # Set the pixel to "on"

# Rainbow colors
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

# Main loop with consistent timing
last_frame_time = time.monotonic()
frame_interval = 1.0 / FRAME_RATE

while True:
    try:
        current_time = time.monotonic()
        elapsed = current_time - last_frame_time
        
        # Only update if it's time for the next frame
        if elapsed >= frame_interval:
            # Clear previous sparkles
            while len(sparkles_group) > 0:
                sparkles_group.pop()
            
            # Add new sparkles (using a fixed number for more consistent performance)
            num_sparkles = random.randint(1000, 2000)  # Random number between 100 and 1000
            for _ in range(num_sparkles):
                # Create palette
                palette = displayio.Palette(2)
                palette[0] = 0x000000  # Transparent
                palette[1] = random.choice(RAINBOW_COLORS)
                
                # Create the sparkle
                sparkle = displayio.TileGrid(
                    sparkle_bitmap,
                    pixel_shader=palette,
                    x=random.randint(0, MATRIX_WIDTH),
                    y=random.randint(0, MATRIX_HEIGHT)
                )
                sparkles_group.append(sparkle)
            
            # Display the sparkles
            display.refresh()
            
            # Run garbage collection to prevent memory issues
            gc.collect()
            
            # Update the last frame time
            last_frame_time = current_time
            
    except Exception as e:
        print("Error:", e)
        time.sleep(0.5)