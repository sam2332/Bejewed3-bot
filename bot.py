# %%
# Bejeweled 3 Bot
# This bot plays Bejeweled 3 by analyzing the game grid and making optimal moves.
# %%
# Import required libraries
import pygetwindow as gw
import pyautogui
from PIL import Image
import numpy as np


# %%
# Find the Bejeweled 3 window and get its position and size
window_title = 'Bejeweled 3'
window = None
for w in gw.getAllWindows():
    if window_title.lower() in w.title.lower():
        window = w
        break
if window is None:
    raise Exception(f'Window titled "{window_title}" not found!')
left, top, width, height = window.left, window.top, window.width, window.height
print(f'Window position: ({left}, {top}), size: ({width}x{height})')

# %%
left += 270  # Adjust for window border
top += 70 # Adjust for window title bar
# Define the region to capture the game area
width -= 310  # Adjust for window border
height -= 130  # Adjust for window title bar and bottom border

# %%
# Take a screenshot of the Bejeweled 3 window region
screenshot = pyautogui.screenshot(region=(left, top, width, height))



# %%
from collections import defaultdict
import numpy as np

grid_width = 64
grid_height = 64
grid_columns = 8
grid_rows = 8
import colorsys

import colorsys

def adjust_to_color_bucket(color, shift_step=0.01, max_shift=0.07):
    r, g, b = [x / 255.0 for x in color]
    h_original, s, v = colorsys.rgb_to_hsv(r, g, b)

    shifts = [0] + [i * shift_step for i in range(1, int(max_shift / shift_step) + 1)]
    for shift in shifts:
        for adjusted_h in [(h_original + shift) % 1.0, (h_original - shift) % 1.0]:
            # White
            if s < 0.2 and v > 0.8:
                return (255, 255, 255)
            # Light Gray
            if s < 0.2 and v > 0.5:
                return (255,255,255)
            # Gray
            if s < 0.2 and v > 0.3:
                return (255,255,255)

            # Yellow
            if 0.12 <= adjusted_h <= 0.18 and v >= 0.7:
                return (255, 240, 0)

            # Orange
            if 0.03 <= adjusted_h <= 0.12 and s >= 0.4 and v >= 0.4:
                return (255, 140, 0)

            # Pink
            if (0.9 <= adjusted_h <= 1.0 or 0.0 <= adjusted_h <= 0.06) and s < 0.6 and v >= 0.7:
                return (255, 182, 193)

            # Red
            if (0.94 <= adjusted_h <= 1.0 or 0.0 <= adjusted_h <= 0.05) and s >= 0.4 and v >= 0.4:
                return (255, 0, 0)

            # Purple
            if 0.68 <= adjusted_h <= 0.93 and s >= 0.25 and v >= 0.4:
                return (239, 25, 251)

            # Blue
            if 0.52 <= adjusted_h <= 0.68 and s >= 0.25 and v >= 0.4:
                return (10, 126, 242)

            # Teal/Cyan
            if 0.46 <= adjusted_h <= 0.54 and s >= 0.25 and v >= 0.5:
                return (10, 126, 242)

    # Fallback: return original unbucketed color
    return (round(r * 255), round(g * 255), round(b * 255))


from PIL import Image

def avg_color(pixels):
    r = sum(p[0] for p in pixels) / len(pixels)
    g = sum(p[1] for p in pixels) / len(pixels)
    b = sum(p[2] for p in pixels) / len(pixels)
    return (int(r), int(g), int(b))

import numpy as np
from PIL import Image

def gather_game_grid(screenshot, grid_width, grid_height, grid_columns, grid_rows, has_progress_bar=False):
    y_offset = 5
    if has_progress_bar:
        y_offset = 30
    screenshot_np = np.array(screenshot)
    height, width = screenshot_np.shape[:2]

    # Prepare debug image
    test_np = np.ones((grid_rows * grid_height + y_offset, grid_columns * grid_width, 3), dtype=np.uint8) * 255
    #paste the screenshot into the debug image
    test_np[y_offset:y_offset + height, :width] = screenshot_np

    game = []

    for row in range(grid_rows):
        row_array = []
        for col in range(grid_columns):
            x_center = col * grid_width + grid_width // 2
            y_center = row * grid_height + grid_height // 2
            y_center += y_offset

            # Region to sample
            sample_half = 5
            x1 = max(x_center - sample_half, 0)
            x2 = min(x_center + sample_half, width)
            y1 = max(y_center - sample_half, 0)
            y2 = min(y_center + sample_half, height)

            region = screenshot_np[y1:y2, x1:x2]
            if region.size == 0:
                row_array.append((0, 0, 0))
                continue

            avg = tuple(region.mean(axis=(0, 1)).astype(int))
            bucketed = adjust_to_color_bucket(avg)
            row_array.append(bucketed)

            # Draw black border + color box on debug image
            box_size = 14
            bx1 = max(x_center - box_size // 2, 0)
            bx2 = min(x_center + box_size // 2, width)
            by1 = max(y_center + y_offset - box_size // 2, 0)
            by2 = min(y_center + y_offset + box_size // 2, height + y_offset)

            # Draw black square
            test_np[by1:by2, bx1:bx2] = 0
            # Fill inside with color
            inner_pad = 2
            test_np[by1+inner_pad:by2-inner_pad, bx1+inner_pad:bx2-inner_pad] = avg

        game.append(row_array)

    Image.fromarray(test_np).save("test_image.png")
    return game



# %%
from colorsys import rgb_to_hsv

def debug_hsv(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = rgb_to_hsv(r, g, b)
    return h, s, v

for c in [(252, 242, 33), (255, 255, 205), (255, 254, 134)]:
    print(c, debug_hsv(c))

# %%
from IPython.display import display, HTML

def show_color_grid(game_grid):
    html = '<table style="border-collapse:collapse;">'
    for row in game_grid:
        html += '<tr>'
        for color in row:
            rgb = f'rgb{color}'
            html += f'<td style="width:32px;height:32px;background:{rgb};border:1px solid #333;">{rgb}</td>'
        html += '</tr>'
    html += '</table>'
    display(HTML(html))




# %%
import time

def colors_match(c1, c2, tolerance=30):
    return all(abs(a - b) < tolerance for a, b in zip(c1, c2))

def count_match(grid, r, c):
    color = grid[r][c]
    # Horizontal
    count_h = 1
    for dc in [-1, 1]:
        cc = c + dc
        while 0 <= cc < len(grid[0]) and colors_match(grid[r][cc], color):
            count_h += 1
            cc += dc
    # Vertical
    count_v = 1
    for dr in [-1, 1]:
        rr = r + dr
        while 0 <= rr < len(grid) and colors_match(grid[rr][c], color):
            count_v += 1
            rr += dr
    return max(count_h if count_h >= 3 else 0, count_v if count_v >= 3 else 0)

def find_best_move(grid, previous_moves = None):
    if previous_moves is None:
        previous_moves = set()
    rows, cols = len(grid), len(grid[0])
    best_score = 0
    best_move = None
    for r in range(rows-1, -1, -1):
        for c in range(cols-1, -1, -1):
            # Try horizontal swap
            if c < cols - 1 and grid[r][c] != grid[r][c+1]:  # Only swap if different
                grid[r][c], grid[r][c+1] = grid[r][c+1], grid[r][c]
                score = count_match(grid, r, c) + count_match(grid, r, c+1)
                if score > best_score and ((r, c), (r, c+1)) not in previous_moves:
                    best_score = score
                    best_move = ((r, c), (r, c+1))
                grid[r][c], grid[r][c+1] = grid[r][c+1], grid[r][c]
            # Try vertical swap
            if r < rows - 1 and grid[r][c] != grid[r+1][c]:  # Only swap if different
                grid[r][c], grid[r+1][c] = grid[r+1][c], grid[r][c]
                score = count_match(grid, r, c) + count_match(grid, r+1, c)
                if score > best_score and ((r, c), (r+1, c)) not in previous_moves:
                    best_score = score
                    best_move = ((r, c), (r+1, c))
                grid[r][c], grid[r+1][c] = grid[r+1][c], grid[r][c]
    return best_move, best_score

def check_match(grid, r, c):
    color = grid[r][c]
    # Horizontal
    count = 1
    for dc in [-1, 1]:
        cc = c + dc
        while 0 <= cc < len(grid[0]) and colors_match(grid[r][cc], color):
            count += 1
            cc += dc
    if count >= 3:
        return True
    # Vertical
    count = 1
    for dr in [-1, 1]:
        rr = r + dr
        while 0 <= rr < len(grid) and colors_match(grid[rr][c], color):
            count += 1
            rr += dr
    return count >= 3

def grid_to_screen(row, col):
    x = left + col * grid_width + grid_width // 2
    y = top + row * grid_height + grid_height // 2
    return x, y


# %%
def get_mouse_position():
    """Get the current mouse position."""
    return pyautogui.position()
last_mouse_position = (None, None)
def click_at(x, y):
    """Click at the specified screen coordinates."""
    global last_mouse_position
    current_pos = pyautogui.position()
    if last_mouse_position != (None, None) and current_pos != last_mouse_position:
        print(f"Mouse position has changed from {last_mouse_position} to {current_pos}. Stopping bot.")
        raise ValueError("Mouse position has changed since last click. Stopping bot.")
    
    last_mouse_position = (x, y)
    pyautogui.click(x=x, y=y)
def move_to(x, y):
    """Move the mouse to the specified screen coordinates."""
    global last_mouse_position
    current_pos = pyautogui.position()
    if last_mouse_position != (None, None) and current_pos != last_mouse_position:
        print(f"Mouse position has changed from {last_mouse_position} to {current_pos}. Stopping bot.")
        raise ValueError("Mouse position has changed since last move. Stopping bot.")
    
    last_mouse_position = (x, y)
    pyautogui.moveTo(x=x, y=y)
# %%
def screen_position_to_screenshot_position(x, y):
    """Convert screen coordinates to screenshot coordinates."""
    return x - left, y - top

# %%
def close_color(rgb,rgb2,tolerance=30):
    """Check if two colors are close enough to be considered the same."""
    return all(abs(a - b) < tolerance for a, b in zip(rgb, rgb2))
 

# %%
def is_in_rankup_menu(screenshot):
    
    correct_color = (126, 2, 77)
    pos = (479, 150)
    color = screenshot.getpixel(screen_position_to_screenshot_position(*pos))
    return (close_color(correct_color,color))


def is_in_badges(screenshot):
    correct_color = (159, 33, 111)
    pos = (531, 75)
    color = screenshot.getpixel(screen_position_to_screenshot_position(*pos))
    return (close_color(correct_color,color))



def is_in_unlock_menu(screenshot):
    correct_color = (181, 54, 133)
    pos = (563, 199)
    color = screenshot.getpixel(screen_position_to_screenshot_position(*pos))
 
    return (close_color(correct_color,color))
is_in_badges(screenshot)


# %%
def screenshot_diff(screenshot1, screenshot2):
    """Calculate the difference between two screenshots."""
    arr1 = np.array(screenshot1)
    arr2 = np.array(screenshot2)
    diff = np.abs(arr1 - arr2)
    return np.mean(diff)


# %%

def main():
    time.sleep(5)  # Allow time for the display to render
    last_mouse_position = (None, None)
    old_screenshot = None
    while True:
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        game_grid = gather_game_grid(screenshot, grid_width, grid_height, grid_columns, grid_rows)
        best_move, best_score = find_best_move(game_grid)
        if is_in_rankup_menu(screenshot):
            click_at(x=404, y=383)
        elif is_in_badges(screenshot):
            
            click_at(x=403, y=560)
        elif is_in_unlock_menu(screenshot):
            click_at(x=404, y=383)
        else:
            #print(best_move)
            if best_move:
                (r1, c1), (r2, c2) = best_move
                x1, y1 = grid_to_screen(r1, c1)
                x2, y2 = grid_to_screen(r2, c2)
                
                print(f"Swapping ({r1},{c1}) <-> ({r2},{c2}) at screen ({x1},{y1}) <-> ({x2},{y2}) with score {best_score}")
                click_at(x=x1, y=y1)
                time.sleep(0.1)
                click_at(x=x2, y=y2)
                move_to(0,0)
            else:
                print("No valid move found.")
        old_screenshot = screenshot
        time.sleep(1)  # Sleep to avoid busy waiting
def reset_mouse_position():
    """Reset the last mouse position to None."""
    global last_mouse_position
    last_mouse_position = (None, None)

