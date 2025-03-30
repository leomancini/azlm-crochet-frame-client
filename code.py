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

print("Starting rainbow sparkles...")

# Main loop with simplified approach
while True:
    try:
        # Clear previous sparkles
        while len(sparkles_group) > 0:
            sparkles_group.pop()
        
        # Add new sparkles
        num_sparkles = random.randint(500, 1000)
        for _ in range(num_sparkles):
            # Create palette
            palette = displayio.Palette(2)
            palette[0] = 0x000000  # Transparent
            palette[1] = random.choice(RAINBOW_COLORS)
            
            # Create the sparkle
            sparkle = displayio.TileGrid(
                sparkle_bitmap,
                pixel_shader=palette,
                x=random.randint(0, MATRIX_WIDTH-1),
                y=random.randint(0, MATRIX_HEIGHT-1)
            )
            sparkles_group.append(sparkle)
        
        # Display the sparkles
        display.refresh()
        
        # Short delay to control animation speed
        time.sleep(0.05)
        
        # Run garbage collection to prevent memory issues
        gc.collect()
        
    except Exception as e:
        print("Error:", e)
        time.sleep(0.5)