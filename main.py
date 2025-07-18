import pyxel
from levels import LEVEL_1_BLOCKS, LEVEL_2_BLOCKS
import random

# --- Constants ---
TILE_SIZE = 16
GRID_WIDTH = 15
GRID_HEIGHT = 13
UI_HEIGHT = 24 # Height for UI elements at the top
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE + UI_HEIGHT

# --- Color Palette ---
C_BLACK, C_WALL, C_FLOOR, C_ARROW = 0, 1, 7, 0
C_RED_BLOCK, C_RED_EXIT = 8, 2
C_BLUE_BLOCK, C_BLUE_EXIT = 9, 3
C_YELLOW_BLOCK, C_YELLOW_EXIT = 10, 4
C_GREEN_BLOCK, C_GREEN_EXIT = 11, 5

class Block:
    def __init__(self, x, y, shape, color):
        self.x, self.y, self.shape, self.color = x, y, shape, color
        self.state = "active"
        self.shred_progress = 0
        self.shred_direction = (0, 0)

    def get_tiles(self, x=None, y=None):
        base_x = x if x is not None else self.x
        base_y = y if y is not None else self.y
        return [(base_x + dx, base_y + dy) for dx, dy in self.shape]

class Game:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Block Shredder", fps=60)
        self.score = 0
        self.current_stage_num = 1
        self.levels = [LEVEL_1_BLOCKS, LEVEL_2_BLOCKS] # Add LEVEL_2_BLOCKS here
        self.win_message = ""
        self.load_level(self.levels[self.current_stage_num - 1])
        pyxel.run(self.update, self.draw)

    def load_level(self, level_block_data):
        self.set_color_palette()
        self.blocks = [Block(**data) for data in level_block_data]
        self.board, self.exits = self.create_board_from_blocks(self.blocks)
        self.selected_block = self.blocks[0] if self.blocks else None
        self.win_message = ""

    def set_color_palette(self):
        pyxel.colors[C_WALL] = 0x495057; pyxel.colors[C_FLOOR] = 0xDEE2E6
        pyxel.colors[C_RED_BLOCK] = 0xF03E3E; pyxel.colors[C_RED_EXIT] = 0xFFC9C9
        pyxel.colors[C_BLUE_BLOCK] = 0x4263EB; pyxel.colors[C_BLUE_EXIT] = 0xD0E0FF
        pyxel.colors[C_YELLOW_BLOCK] = 0xF59F00; pyxel.colors[C_YELLOW_EXIT] = 0xFFECB3
        pyxel.colors[C_GREEN_BLOCK] = 0x2FB844; pyxel.colors[C_GREEN_EXIT] = 0xD3F9D8

    def create_board_from_blocks(self, blocks):
        board = [[C_WALL] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        for y in range(1, GRID_HEIGHT - 1): board[y][1:-1] = [C_FLOOR] * (GRID_WIDTH - 2)
        
        exits = []
        exit_map = {C_RED_BLOCK: C_RED_EXIT, C_BLUE_BLOCK: C_BLUE_EXIT,
                      C_YELLOW_BLOCK: C_YELLOW_EXIT, C_GREEN_BLOCK: C_GREEN_EXIT}
        used_wall_coords = set()

        # Define all possible wall segments for exits
        all_wall_segments = []
        # Top wall
        for x in range(1, GRID_WIDTH - 1): all_wall_segments.append({'x': x, 'y': 0, 'dir': (0, -1), 'axis': 'h'})
        # Bottom wall
        for x in range(1, GRID_WIDTH - 1): all_wall_segments.append({'x': x, 'y': GRID_HEIGHT - 1, 'dir': (0, 1), 'axis': 'h'})
        # Left wall
        for y in range(1, GRID_HEIGHT - 1): all_wall_segments.append({'x': 0, 'y': y, 'dir': (-1, 0), 'axis': 'v'})
        # Right wall
        for y in range(1, GRID_HEIGHT - 1): all_wall_segments.append({'x': GRID_WIDTH - 1, 'y': y, 'dir': (1, 0), 'axis': 'v'})

        # Shuffle the order of blocks to place exits for
        blocks_to_place_exits_for = list(blocks)
        random.shuffle(blocks_to_place_exits_for)

        for block in blocks_to_place_exits_for:
            exit_color = exit_map.get(block.color)
            if not exit_color: continue

            block_width = max(w for w, h in block.shape) - min(w for w, h in block.shape) + 1
            block_height = max(h for w, h in block.shape) - min(h for w, h in block.shape) + 1

            placed = False
            # Try to place exit on a random side until successful
            sides_to_try = ['top', 'bottom', 'left', 'right']
            random.shuffle(sides_to_try)

            for side in sides_to_try:
                possible_exit_segments = []
                if side == 'top':
                    for x_start in range(1, GRID_WIDTH - block_width): # Ensure block fits
                        segment = [(x_start + i, 0) for i in range(block_width)]
                        possible_exit_segments.append({'coords': segment, 'dir': (0, -1)})
                elif side == 'bottom':
                    for x_start in range(1, GRID_WIDTH - block_width): # Ensure block fits
                        segment = [(x_start + i, GRID_HEIGHT - 1) for i in range(block_width)]
                        possible_exit_segments.append({'coords': segment, 'dir': (0, 1)})
                elif side == 'left':
                    for y_start in range(1, GRID_HEIGHT - block_height): # Ensure block fits
                        segment = [(0, y_start + i) for i in range(block_height)]
                        possible_exit_segments.append({'coords': segment, 'dir': (-1, 0)})
                elif side == 'right':
                    for y_start in range(1, GRID_HEIGHT - block_height): # Ensure block fits
                        segment = [(GRID_WIDTH - 1, y_start + i) for i in range(block_height)]
                        possible_exit_segments.append({'coords': segment, 'dir': (1, 0)})
                
                random.shuffle(possible_exit_segments) # Shuffle positions on this side

                for segment_info in possible_exit_segments:
                    segment_coords = segment_info['coords']
                    segment_dir = segment_info['dir']
                    
                    # Check if this segment is free
                    if all((x, y) not in used_wall_coords for x, y in segment_coords):
                        # Place the exit
                        for ex, ey in segment_coords:
                            board[ey][ex] = exit_color
                            exits.append({"x": ex, "y": ey, "direction": segment_dir})
                            used_wall_coords.add((ex, ey))
                        placed = True
                        break
                if placed: break
        return board, exits

    def update(self):
        if pyxel.btnp(pyxel.KEY_R): self.load_level(self.levels[self.current_stage_num - 1])
        if self.win_message: return
        self.handle_input()
        self.update_animations()
        self.check_win_condition()

    def handle_input(self):
        active_blocks = [b for b in self.blocks if b.state == "active"]
        if not active_blocks: self.selected_block = None; return
        if self.selected_block not in active_blocks: self.selected_block = active_blocks[0]

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mx, my = pyxel.mouse_x // TILE_SIZE, (pyxel.mouse_y - UI_HEIGHT) // TILE_SIZE # Adjust for UI_HEIGHT
            for block in active_blocks: 
                if (mx, my) in block.get_tiles(): self.selected_block = block; return
        if pyxel.btnp(pyxel.KEY_TAB):
            try: self.selected_block = active_blocks[(active_blocks.index(self.selected_block) + 1) % len(active_blocks)]
            except (ValueError, IndexError): self.selected_block = active_blocks[0]

        if not self.selected_block: return
        dx, dy = 0, 0
        if pyxel.btnp(pyxel.KEY_LEFT): dx = -1
        elif pyxel.btnp(pyxel.KEY_RIGHT): dx = 1
        elif pyxel.btnp(pyxel.KEY_UP): dy = -1
        elif pyxel.btnp(pyxel.KEY_DOWN): dy = 1
        if dx or dy: self.move_block(self.selected_block, dx, dy)

    def move_block(self, block, dx, dy):
        next_x, next_y = block.x + dx, block.y + dy
        
        # Check if the move is valid (not hitting solid walls or other blocks)
        if self.is_move_valid(block, next_x, next_y):
            block.x, block.y = next_x, next_y
            # After a valid move, check if the block is now on an exit
            self.check_for_exit(block, dx, dy) # Pass dx, dy here
        # If move is not valid, block doesn't move, and no further action is needed here

    def is_move_valid(self, block, next_x, next_y):
        active_blocks = [b for b in self.blocks if b.state == "active" and b is not block]
        for x, y in block.get_tiles(next_x, next_y):
            # Check if outside the main playable area (inner walls)
            if not (1 <= x < GRID_WIDTH - 1 and 1 <= y < GRID_HEIGHT - 1):
                # If it's outside the inner playable area, check if it's an exit
                exit_map = {C_RED_BLOCK: C_RED_EXIT, C_BLUE_BLOCK: C_BLUE_EXIT,
                              C_YELLOW_BLOCK: C_YELLOW_EXIT, C_GREEN_BLOCK: C_GREEN_EXIT}
                if self.board[y][x] == exit_map.get(block.color): # It's a valid exit
                    continue # Allow movement onto exit tiles
                else:
                    return False # It's a solid outer wall or wrong exit
            
            # Check collision with other active blocks
            for other in active_blocks: 
                if (x, y) in other.get_tiles(): return False
        return True

    def check_for_exit(self, block, move_dx, move_dy):
        exit_map = {C_RED_BLOCK: C_RED_EXIT, C_BLUE_BLOCK: C_BLUE_EXIT,
                      C_YELLOW_BLOCK: C_YELLOW_EXIT, C_GREEN_BLOCK: C_GREEN_EXIT}
        target_exit_color_id = exit_map.get(block.color)
        if not target_exit_color_id: return

        # Check if any part of the block is currently on a correct exit tile
        for block_tile_x, block_tile_y in block.get_tiles():
            if 0 <= block_tile_x < GRID_WIDTH and 0 <= block_tile_y < GRID_HEIGHT:
                if self.board[block_tile_y][block_tile_x] == target_exit_color_id:
                    # Found a part of the block on a correct exit tile
                    # Now find the corresponding exit info to get the shred direction
                    for exit_info in self.exits:
                        if exit_info["x"] == block_tile_x and exit_info["y"] == block_tile_y:
                            # Check if the move direction matches the exit direction
                            if exit_info["direction"] == (move_dx, move_dy):
                                block.state = "shredding"
                                block.shred_direction = exit_info["direction"]
                                return # Block is shredding, no need to check further

    def update_animations(self):
        for block in self.blocks:
            if block.state == "shredding":
                block.shred_progress += 0.5
                if block.shred_progress >= TILE_SIZE:
                    if block.state != "done": # Ensure score is added only once
                        self.score += 1
                        print(f"Score incremented! New score: {self.score}") # DEBUG PRINT
                    block.state = "done"

    def check_win_condition(self):
        if self.blocks and all(b.state == "done" for b in self.blocks):
            self.win_message = "STAGE CLEAR! (R to Restart)"
            # If all blocks are done, advance to next stage
            if self.current_stage_num < len(self.levels):
                self.current_stage_num += 1
                self.load_level(self.levels[self.current_stage_num - 1])
            else:
                self.win_message = "ALL STAGES CLEAR! (R to Restart)"

    def draw(self):
        pyxel.cls(C_BLACK)
        
        # Draw UI area
        pyxel.rect(0, 0, SCREEN_WIDTH, UI_HEIGHT, C_WALL) # Background for UI
        pyxel.text(4, 8, f"SCORE: {self.score}", 7) # Score
        pyxel.text(SCREEN_WIDTH - 60, 8, f"STAGE: {self.current_stage_num}", 7) # Stage number

        self.draw_board()
        self.draw_blocks()
        self.draw_cursor()
        if self.win_message:
            pyxel.text(SCREEN_WIDTH/2 - 48, SCREEN_HEIGHT/2, self.win_message, C_BLACK) # Changed color to C_BLACK

    def draw_board(self):
        for y in range(GRID_HEIGHT): # Draw board tiles
            for x in range(GRID_WIDTH): pyxel.rect(x*TILE_SIZE, y*TILE_SIZE + UI_HEIGHT, TILE_SIZE, TILE_SIZE, self.board[y][x]) # Offset by UI_HEIGHT
        for exit in self.exits: # Draw arrows on exits
            cx, cy = exit["x"] * TILE_SIZE + TILE_SIZE // 2, exit["y"] * TILE_SIZE + TILE_SIZE // 2 + UI_HEIGHT # Offset by UI_HEIGHT
            dx, dy = exit["direction"]
            
            # Draw a simple arrow (triangle) pointing outwards
            # The tip of the arrow is at (cx, cy), base is opposite
            # Adjusted coordinates for better alignment
            pyxel.tri(cx + dx*4, cy + dy*4, cx - dx*4 + dy*2, cy - dy*4 - dx*2, cx - dx*4 - dy*2, cy - dy*4 + dx*2, C_ARROW)

    def draw_blocks(self):
        for block in self.blocks:
            if block.state == "done": continue
            if block.state == "shredding":
                dx, dy = block.shred_direction; p = block.shred_progress
                if dx == -1: pyxel.clip(0, UI_HEIGHT, (block.x + 1) * TILE_SIZE - p, SCREEN_HEIGHT)
                elif dx == 1: pyxel.clip(block.x * TILE_SIZE + p, UI_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)
                elif dy == -1: pyxel.clip(0, UI_HEIGHT, SCREEN_WIDTH, (block.y + 1) * TILE_SIZE - p + UI_HEIGHT)
                elif dy == 1: pyxel.clip(0, block.y * TILE_SIZE + p + UI_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)
            for tile_x, tile_y in block.get_tiles():
                pyxel.rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE + UI_HEIGHT, TILE_SIZE, TILE_SIZE, block.color) # Offset by UI_HEIGHT
            pyxel.clip()

    def draw_cursor(self):
        if self.selected_block and self.selected_block.state == "active" and (pyxel.frame_count // 10) % 2 == 0:
            # Calculate bounding box of the entire block
            min_x = min(t[0] for t in self.selected_block.get_tiles())
            max_x = max(t[0] for t in self.selected_block.get_tiles())
            min_y = min(t[1] for t in self.selected_block.get_tiles())
            max_y = max(t[1] for t in self.selected_block.get_tiles())

            cursor_x = min_x * TILE_SIZE - 1
            cursor_y = min_y * TILE_SIZE - 1 + UI_HEIGHT # Offset by UI_HEIGHT
            cursor_w = (max_x - min_x + 1) * TILE_SIZE + 2
            cursor_h = (max_y - min_y + 1) * TILE_SIZE + 2

            # Draw a solid white border (for blinking effect)
            pyxel.rectb(cursor_x, cursor_y, cursor_w, cursor_h, C_BLACK) # Changed to black (C_BLACK)

if __name__ == '__main__':
    Game()
