# --- Level Definitions ---

# For simplicity, we use the color index numbers directly.
# 8:Red, 9:Blue, 10:Yellow, 11:Green

LEVEL_1_BLOCKS = [
    {'x': 2, 'y': 5, 'shape': [(0, 0), (1, 0)], 'color': 8}, # Red 1x2
    {'x': 11, 'y': 2, 'shape': [(0, 0), (0, 1)], 'color': 9}, # Blue 2x1
    {'x': 4, 'y': 2, 'shape': [(0, 0), (1, 0), (1, 1), (2, 0)], 'color': 10}, # Yellow T-shape
    {'x': 6, 'y': 8, 'shape': [(0, 0), (1, 0), (0, 1)], 'color': 11} # Green L-shape
]

LEVEL_2_BLOCKS = [
    {'x': 3, 'y': 3, 'shape': [(0, 0), (1, 0), (2, 0)], 'color': 8}, # Red 1x3
    {'x': 8, 'y': 5, 'shape': [(0, 0), (0, 1), (0, 2)], 'color': 9}, # Blue 3x1
    {'x': 5, 'y': 10, 'shape': [(0, 0), (1, 0), (0, 1)], 'color': 10}, # Yellow L-shape
    {'x': 10, 'y': 8, 'shape': [(0, 0), (1, 0), (2, 0), (3, 0)], 'color': 11} # Green 1x4
]