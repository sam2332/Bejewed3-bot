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

def adjust_to_color_bucket(color):
    r, g, b = [x / 255.0 for x in color]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    # White
    if s < 0.15 and v > 0.85:
        return (255, 255, 255)

    # Yellow
    if 0.15 <= h <= 0.18 and v >= 0.8:
        return (255, 240, 0)

    # Orange
    if 0.05 <= h <= 0.12 and s >= 0.5 and v >= 0.5:
        return (255, 140, 0)

    # Pink
    if (0.9 <= h <= 1.0 or 0.0 <= h <= 0.05) and s < 0.5 and v >= 0.8:
        return (255, 182, 193)

    # Red
    if (0.9 <= h <= 1.0 or 0.0 <= h <= 0.05) and s >= 0.5 and v >= 0.5:
        return (255, 0, 0)

    # Purple
    if 0.72 <= h <= 0.9 and s >= 0.3 and v >= 0.5:
        return (239, 25, 251)

    # Blue (tighter range to exclude greenish-cyan tones)
    if 0.56 <= h <= 0.68 and s >= 0.3 and v >= 0.5:
        return (10, 126, 242)
    # Teal/Cyan
    if 0.48 <= h <= 0.54 and s >= 0.3 and v >= 0.6:
        return (10, 126, 242)
    return (round(r * 255), round(g * 255), round(b * 255))



def avg_color(pixels):
    # Calculate the average for each channel
    arr = np.array(pixels)
    return tuple(int(arr[:, i].mean()) for i in range(3))

def gather_game_grid(screenshot, grid_width, grid_height, grid_columns, grid_rows):
    game = list()    
    # add a dot at the center of each grid cell
    for row in range(grid_rows):
        _rowArray = list()
        for col in range(grid_columns):
            x_center = col * grid_width + grid_width // 2
            y_center = row * grid_height + grid_height // 2
            # Collect a 3x3 grid of pixels around the center
            pixels = []
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    x = x_center + dx
                    y = y_center + dy
                    if 0 <= x < screenshot.width and 0 <= y < screenshot.height:
                        pixels.append(screenshot.getpixel((x, y)))
            if pixels:
                color = adjust_to_color_bucket(avg_color(pixels))
            else:
                color = (0, 0, 0)
            _rowArray.append(color)
        game.append(_rowArray)
            
    return game
game_grid = gather_game_grid(screenshot, grid_width, grid_height, grid_columns, grid_rows)
game_grid


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

def find_best_move(grid):
    rows, cols = len(grid), len(grid[0])
    best_score = 0
    best_move = None
    for r in range(rows-1, -1, -1):
        for c in range(cols-1, -1, -1):
            # Try horizontal swap
            if c < cols - 1 and grid[r][c] != grid[r][c+1]:  # Only swap if different
                grid[r][c], grid[r][c+1] = grid[r][c+1], grid[r][c]
                score = count_match(grid, r, c) + count_match(grid, r, c+1)
                if score > best_score:
                    best_score = score
                    best_move = ((r, c), (r, c+1))
                grid[r][c], grid[r][c+1] = grid[r][c+1], grid[r][c]
            # Try vertical swap
            if r < rows - 1 and grid[r][c] != grid[r+1][c]:  # Only swap if different
                grid[r][c], grid[r+1][c] = grid[r+1][c], grid[r][c]
                score = count_match(grid, r, c) + count_match(grid, r+1, c)
                if score > best_score:
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

