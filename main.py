import pyxel
from levels import LEVEL_1_BLOCKS
import random

# --- Constants ---
TILE_SIZE = 16
GRID_WIDTH = 15
GRID_HEIGHT = 13
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

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
        self.load_level(LEVEL_1_BLOCKS)
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

        wall_sections = [
            (range(1, GRID_WIDTH - 1), 0, (0, -1), 'h'),      # Top (arrow points up)
            (range(1, GRID_WIDTH - 1), GRID_HEIGHT - 1, (0, 1), 'h'), # Bottom (arrow points down)
            (0, range(1, GRID_HEIGHT - 1), (-1, 0), 'v'),      # Left (arrow points left)
            (GRID_WIDTH - 1, range(1, GRID_HEIGHT - 1), (1, 0), 'v') # Right (arrow points right)
        ]
        random.shuffle(wall_sections)

        for block in blocks:
            exit_color = exit_map.get(block.color); placed = False
            if not exit_color: continue
            max_w = max(w for w, h in block.shape) - min(w for w, h in block.shape) + 1
            max_h = max(h for w, h in block.shape) - min(h for w, h in block.shape) + 1

            for x_range, y_range, direction, axis in wall_sections:
                exit_len = max_w if axis == 'h' else max_h
                possible_starts = list(x_range) if isinstance(x_range, range) else list(y_range)
                random.shuffle(possible_starts)
                for start_coord in possible_starts:
                    if (start_coord + exit_len) > (GRID_WIDTH -1 if axis == 'h' else GRID_HEIGHT - 1): continue
                    coords_to_place = []
                    if axis == 'h': coords_to_place = [(start_coord + i, y_range) for i in range(exit_len)]
                    else: coords_to_place = [(x_range, start_coord + i) for i in range(exit_len)]
                    if all(c not in used_wall_coords for c in coords_to_place):
                        for ex, ey in coords_to_place:
                            board[ey][ex] = exit_color
                            exits.append({"x": ex, "y": ey, "direction": direction})
                            used_wall_coords.add((ex, ey))
                        placed = True; break
                if placed: break
        return board, exits

    def update(self):
        if pyxel.btnp(pyxel.KEY_R): self.load_level(LEVEL_1_BLOCKS)
        if self.win_message: return
        self.handle_input()
        self.update_animations()
        self.check_win_condition()

    def handle_input(self):
        active_blocks = [b for b in self.blocks if b.state == "active"]
        if not active_blocks: self.selected_block = None; return
        if self.selected_block not in active_blocks: self.selected_block = active_blocks[0]

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mx, my = pyxel.mouse_x // TILE_SIZE, pyxel.mouse_y // TILE_SIZE
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
        else:
            # If move is not valid, check if it's an exit collision
            self.check_for_exit_collision(block, next_x, next_y, (dx, dy))

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
                if block.shred_progress >= TILE_SIZE: block.state = "done"

    def check_win_condition(self):
        if self.blocks and all(b.state == "done" for b in self.blocks):
            self.win_message = "STAGE CLEAR! (R to Restart)"

    def draw(self):
        pyxel.cls(C_BLACK)
        self.draw_board()
        self.draw_blocks()
        self.draw_cursor()
        if self.win_message:
            pyxel.text(SCREEN_WIDTH/2 - 48, SCREEN_HEIGHT/2, self.win_message, C_BLACK) # Changed color to C_BLACK

    def draw_board(self):
        for y in range(GRID_HEIGHT): # Draw board tiles
            for x in range(GRID_WIDTH): pyxel.rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE, self.board[y][x])
        for exit in self.exits: # Draw arrows on exits
            cx, cy = exit["x"] * TILE_SIZE + TILE_SIZE // 2, exit["y"] * TILE_SIZE + TILE_SIZE // 2 # Center of tile
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
                if dx == -1: pyxel.clip(0, 0, (block.x + 1) * TILE_SIZE - p, SCREEN_HEIGHT)
                elif dx == 1: pyxel.clip(block.x * TILE_SIZE + p, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
                elif dy == -1: pyxel.clip(0, 0, SCREEN_WIDTH, (block.y + 1) * TILE_SIZE - p)
                elif dy == 1: pyxel.clip(0, block.y * TILE_SIZE + p, SCREEN_WIDTH, SCREEN_HEIGHT)
            for tile_x, tile_y in block.get_tiles():
                pyxel.rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE, block.color)
            pyxel.clip()

    def draw_cursor(self):
        if self.selected_block and self.selected_block.state == "active":
            # Calculate bounding box of the entire block
            min_x = min(t[0] for t in self.selected_block.get_tiles())
            max_x = max(t[0] for t in self.selected_block.get_tiles())
            min_y = min(t[1] for t in self.selected_block.get_tiles())
            max_y = max(t[1] for t in self.selected_block.get_tiles())

            cursor_x = min_x * TILE_SIZE - 1
            cursor_y = min_y * TILE_SIZE - 1
            cursor_w = (max_x - min_x + 1) * TILE_SIZE + 2
            cursor_h = (max_y - min_y + 1) * TILE_SIZE + 2

            # Draw a solid black border
            pyxel.rectb(cursor_x, cursor_y, cursor_w, cursor_h, C_BLACK)

if __name__ == '__main__':
    Game()
