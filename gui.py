import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QPixmap
import numpy as np
import pyautogui
from bot import gather_game_grid, grid_width, grid_height, grid_columns, grid_rows, left, top, width, height, find_best_move, click_at, grid_to_screen,reset_mouse_position,move_to, is_in_rankup_menu, is_in_badges, is_in_unlock_menu
import time
class GameGridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.labels = [[QLabel() for _ in range(grid_columns)] for _ in range(grid_rows)]
        for r in range(grid_rows):
            for c in range(grid_columns):
                label = self.labels[r][c]
                label.setFixedSize(40, 40)
                self.grid_layout.addWidget(label, r, c)

    def update_grid(self, game_grid):
        for r in range(grid_rows):
            for c in range(grid_columns):
                color = game_grid[r][c]
                qcolor = QColor(*color)
                pixmap = QPixmap(40, 40)
                pixmap.fill(qcolor)
                self.labels[r][c].setPixmap(pixmap)

class GridChangeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.labels = [[QLabel() for _ in range(grid_columns)] for _ in range(grid_rows)]
        for r in range(grid_rows):
            for c in range(grid_columns):
                label = self.labels[r][c]
                label.setFixedSize(20, 20)
                self.grid_layout.addWidget(label, r, c)

    def update_grid_change(self, grid_change):
        if grid_change is None:
            for r in range(grid_rows):
                for c in range(grid_columns):
                    self.labels[r][c].clear()
            return
        max_change = np.max(grid_change) if np.max(grid_change) > 0 else 1
        for r in range(grid_rows):
            for c in range(grid_columns):
                value = grid_change[r][c]
                # Map value to a color (red intensity)
                intensity = int(255 * value / max_change)
                qcolor = QColor(intensity, 0, 0)
                pixmap = QPixmap(20, 20)
                pixmap.fill(qcolor)
                self.labels[r][c].setPixmap(pixmap)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bejeweled 3 Grid Visualizer & Bot')
        self.grid_widget = GameGridWidget()
        self.grid_change_widget = GridChangeWidget()  # Add grid change widget
        self.refresh_button = QPushButton('Refresh Now')
        self.refresh_button.clicked.connect(self.update_grid)
        self.play_button = QPushButton('Play')
        self.playing = False
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.toggle_play)
        self.score_total = 0  # Running total of move scores
        self.score_label = QLabel('Total Score: 0')  # Label to display running total
        layout = QVBoxLayout()
        layout.addWidget(self.grid_widget)
        layout.addWidget(QLabel('Grid Change:'))
        layout.addWidget(self.grid_change_widget)  # Add to layout
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.score_label)  # Add the score label to the layout
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1500)  # update every second
        self.game_grid = None
        self.previous_grid = None
        self.screenshot = None
        self.score_total = 0
        self.grid_change = None
        self.update_grid()

    def update_grid(self):
        self.previous_grid = getattr(self, 'game_grid', None)
        if self.previous_grid is not None:
            prev = np.array(self.previous_grid)
            curr = np.array(gather_game_grid(pyautogui.screenshot(region=(left, top, width, height)), grid_width, grid_height, grid_columns, grid_rows))
            # Compute sum of absolute differences per cell (across color channels)
            self.grid_change = np.sum(np.abs(prev - curr), axis=-1)
        else:
            self.grid_change = None
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        self.game_grid = gather_game_grid(screenshot, grid_width, grid_height, grid_columns, grid_rows)
        self.grid_widget.update_grid(self.game_grid)
        self.grid_change_widget.update_grid_change(self.grid_change)  # Update grid change widget
        self.screenshot = screenshot

    def update(self):
        self.update_grid()
        if self.playing:
            try:
                self.play_move()
            except Exception as e:
                print(f"Error during play move: {e}")
                self.playing = False
                self.play_button.setChecked(False)
                self.play_button.setText('Play')

    def toggle_play(self):
        time.sleep(3)
        self.playing = self.play_button.isChecked()
        reset_mouse_position()
        self.play_button.setText('Stop' if self.playing else 'Play')

    def play_move(self):
        if is_in_rankup_menu(self.screenshot):
            click_at(x=404, y=383)
        elif is_in_badges(self.screenshot):
            click_at(x=403, y=560)
        elif is_in_unlock_menu(self.screenshot):
            click_at(x=404, y=383)
        else:
            best_move, best_score = find_best_move(self.game_grid)
            if best_move:
                (r1, c1), (r2, c2) = best_move
                x1, y1 = grid_to_screen(r1, c1)
                x2, y2 = grid_to_screen(r2, c2)
                click_at(x=x1, y=y1)
                time.sleep(0.7)
                click_at(x=x2, y=y2)
                time.sleep(0.3)
                move_to(10,10)
                self.score_total += best_score  # Update running total
                self.score_label.setText(f'Total Score: {self.score_total}')  # Update label
            else:
                #find the most changed cell and click it and then an adjacent cell
                if self.grid_change is not None:
                    max_change_index = np.unravel_index(np.argmax(self.grid_change, axis=None), self.grid_change.shape)
                    r, c = max_change_index
                    x, y = grid_to_screen(r, c)
                    click_at(x=x, y=y)
                    time.sleep(0.3)
                    # Click an adjacent cell
                    if c < grid_columns - 1:
                        x_adj, y_adj = grid_to_screen(r, c + 1)
                        click_at(x=x_adj, y=y_adj)

def run_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_gui()
