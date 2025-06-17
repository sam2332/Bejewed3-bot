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

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bejeweled 3 Grid Visualizer & Bot')
        self.grid_widget = GameGridWidget()
        self.refresh_button = QPushButton('Refresh Now')
        self.refresh_button.clicked.connect(self.update_grid)
        self.play_button = QPushButton('Play')
        self.playing = False
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.toggle_play)
        layout = QVBoxLayout()
        layout.addWidget(self.grid_widget)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.play_button)
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1500)  # update every second
        self.update_grid()

    def update_grid(self):
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        self.game_grid = gather_game_grid(screenshot, grid_width, grid_height, grid_columns, grid_rows)
        self.grid_widget.update_grid(self.game_grid)
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

def run_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_gui()
