import sys
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QCheckBox
import numpy as np
import pyautogui
from bot import gather_game_grid, grid_width, grid_height, grid_columns, grid_rows, left, top, width, height, find_best_move, click_at, grid_to_screen,reset_mouse_position,move_to, is_in_rankup_menu, is_in_badges, is_in_unlock_menu
import time
class ClickableLabel(QLabel):
    clicked = pyqtSignal(int, int)
    def __init__(self, row, col, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
    def mousePressEvent(self, event):
        self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)

class GameGridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.labels = [[ClickableLabel(r, c) for c in range(grid_columns)] for r in range(grid_rows)]
        for r in range(grid_rows):
            for c in range(grid_columns):
                label = self.labels[r][c]
                label.setFixedSize(18, 18)  # Smaller for compact UI
                self.grid_layout.addWidget(label, r, c)
                label.clicked.connect(self.handle_label_click)

    def handle_label_click(self, row, col):
        # Copy coordinates to clipboard (customize as needed)
        clipboard = QApplication.clipboard()
        color_rgb = self.labels[row][col].pixmap().toImage().pixelColor(0, 0).getRgb()
        clipboard.setText(f"Color: {color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}")

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
                label.setFixedSize(10, 10)  # Smaller for compact UI
                self.grid_layout.addWidget(label, r, c)

    def update_grid_change(self, grid_change):
        if grid_change is None:
            for r in range(grid_rows):
                for c in range(grid_columns):
                    self.labels[r][c].clear()
            return
        # Amplify low deltas using square root scaling
        max_change = np.max(grid_change) if np.max(grid_change) > 0 else 1
        for r in range(grid_rows):
            for c in range(grid_columns):
                value = grid_change[r][c]
                intensity = int(255 * value / max_change)
                qcolor = QColor(intensity, 0, 0)
                pixmap = QPixmap(20, 20)
                pixmap.fill(qcolor)
                self.labels[r][c].setPixmap(pixmap)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bejeweled 3 Grid Visualizer & Bot')
        self.setStyleSheet('''
            QWidget { background-color: #232629; color: #f0f0f0; }
            QLabel { color: #f0f0f0; font-size: 10pt; }
            QPushButton { background-color: #333; color: #f0f0f0; border: 1px solid #444; border-radius: 4px; padding: 4px 8px; }
            QPushButton:checked { background-color: #555; }
            QCheckBox { color: #f0f0f0; font-size: 10pt; }
            QCheckBox::indicator { width: 13px; height: 13px; }
            QCheckBox::indicator:unchecked { background-color: #333; border: 1px solid #444; }
            QCheckBox::indicator:checked { background-color: #555; border: 1px solid #666; }
        ''')
        self.setFixedHeight(250)
        self.grid_widget = GameGridWidget()
        self.grid_change_widget = GridChangeWidget()
        self.grid_heatmap_widget = GridChangeWidget()
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.setFixedHeight(24)
        self.refresh_button.clicked.connect(self.update_grid)
        self.play_button = QPushButton('Play')
        self.play_button.setFixedHeight(24)
        self.playing = False
        self.play_button.setCheckable(True) 
        self.play_button.clicked.connect(self.toggle_play)
        self.score_label = QLabel('Score: 0')
        self.score_label.setFixedHeight(20)
        
        # Progress bar checkbox
        self.has_progress_bar_checkbox = QCheckBox('Has Progress Bar')
        self.has_progress_bar_checkbox.setFixedHeight(20)
        self.has_progress_bar = False  # Initialize the attribute
        self.has_progress_bar_checkbox.stateChanged.connect(self.toggle_progress_bar)
        
        # Log widget
        self.log_messages = []
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.last_screenshot_save = None  # Track last save time
        self.log_widget.setFixedWidth(220)
        self.log_widget.setStyleSheet('background-color: #181a1b; color: #f0f0f0; font-size: 9pt;')
        # Horizontal layout
        layout = QHBoxLayout()
        # Add widgets horizontally, with vertical sub-layouts for each grid
        grid_col = QVBoxLayout()
        grid_col.addWidget(QLabel('Grid'))
        grid_col.addWidget(self.grid_widget)
        change_col = QVBoxLayout()
        change_col.addWidget(QLabel('Delta'))
        change_col.addWidget(self.grid_change_widget)
        heatmap_col = QVBoxLayout()
        heatmap_col.addWidget(QLabel('Heatmap'))
        heatmap_col.addWidget(self.grid_heatmap_widget)
        # Add log next to heatmap
        log_col = QVBoxLayout()
        log_col.addWidget(QLabel('Log'))
        log_col.addWidget(self.log_widget)
        controls_col = QVBoxLayout()
        controls_col.addWidget(self.refresh_button)
        controls_col.addWidget(self.play_button)
        controls_col.addWidget(self.score_label)
        controls_col.addWidget(self.has_progress_bar_checkbox)
        controls_col.addStretch()
        layout.addLayout(grid_col)
        layout.addLayout(change_col)
        layout.addLayout(heatmap_col)
        layout.addLayout(log_col)
        layout.addLayout(controls_col)
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)
        self.game_grid = None
        self.previous_grid = None
        self.screenshot = None
        self.score_total = 0
        self.grid_change = None
        self.grid_heatmap = None
        self.grid_history = []
        self.update_grid()
        self.recent_moves = set()  # Track recent moves to avoid duplicates

    def log(self, message):
        self.log_messages.append(message)
        if len(self.log_messages) > 12:
            self.log_messages.pop(0)
        self.log_widget.setPlainText('\n'.join(self.log_messages))
        self.log_widget.verticalScrollBar().setValue(self.log_widget.verticalScrollBar().maximum())

    def update_grid(self):
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        new_grid = gather_game_grid(screenshot, grid_width, grid_height, grid_columns, grid_rows, self.has_progress_bar)
        # Update history
        self.grid_history.append(np.array(new_grid))
        if len(self.grid_history) > 3:
            self.grid_history.pop(0)
        # Compute heatmap if we have at least 2 frames
        if len(self.grid_history) > 1:
            # Per-frame difference (most recent two)
            prev = self.grid_history[-2]
            curr = self.grid_history[-1]
            per_frame_change = np.sum(np.abs(prev - curr), axis=-1)
            self.grid_change = per_frame_change
            # Heatmap over last 5
            diffs = [np.sum(np.abs(self.grid_history[i] - self.grid_history[i-1]), axis=-1) for i in range(1, len(self.grid_history))]
            heatmap = np.sum(diffs, axis=0)
            self.grid_heatmap = heatmap
        else:
            self.grid_change = None
            self.grid_heatmap = None
        self.game_grid = new_grid
        self.grid_widget.update_grid(self.game_grid)
        self.grid_change_widget.update_grid_change(self.grid_change)
        if hasattr(self, 'grid_heatmap_widget'):
            self.grid_heatmap_widget.update_grid_change(self.grid_heatmap)
        self.screenshot = screenshot

    def update(self):
        try:
            self.update_grid()
        except Exception as e:
            print("ooop")
        if self.playing:
            try:
                self.play_move()
            except Exception as e:
                self.log(f"Error during play move: {e}")
                print(f"Error during play move: {e}")
                self.playing = False
                self.play_button.setChecked(False)
                self.play_button.setText('Play')
                self.log('paused')

    def toggle_play(self):
        time.sleep(1)
        self.playing = self.play_button.isChecked()
        reset_mouse_position()
        self.play_button.setText('Stop' if self.playing else 'Play')
        if self.playing:
            self.log('starting')
        else:
            self.log('paused')

    def toggle_progress_bar(self, state):
        self.has_progress_bar = state == 2  # Qt.Checked = 2
        status = "enabled" if self.has_progress_bar else "disabled"
        self.log(f'Progress bar detection: {status}')

    def play_move(self):
        # Wait if most cells are changing (board is animating)
        if self.grid_change is not None:
            delta_threshold = 2  # Small value to ignore noise
            change_mask = self.grid_change > delta_threshold
            change_ratio = np.sum(change_mask) / (grid_rows * grid_columns)
            if change_ratio > 0.3:
                self.log('waiting (board animating)')
                time.sleep(0.5)
                return
        if is_in_rankup_menu(self.screenshot):
            self.log('menu: rankup')
            click_at(x=404, y=383)
        elif is_in_badges(self.screenshot):
            self.log('menu: badges')
            click_at(x=403, y=560)
        elif is_in_unlock_menu(self.screenshot):
            self.log('menu: unlock')
            click_at(x=404, y=383)
        else:
            best_move, best_score = find_best_move(self.game_grid,self.recent_moves)
            if best_move:
                (r1, c1), (r2, c2) = best_move
                self.log(f'best move ({r1},{c1}) <-> ({r2},{c2})')
                x1, y1 = grid_to_screen(r1, c1)
                x2, y2 = grid_to_screen(r2, c2)
                click_at(x=x1, y=y1)
                time.sleep(0.5)
                click_at(x=x2, y=y2)
                time.sleep(0.7)
                move_to(10,10)
                self.score_total += best_score  # Update running total
                self.score_label.setText(f'Total Score: {self.score_total}')  # Update label
                self.recent_moves.add(((r1, c1), (r2, c2)))  # Track recent moves
                self.recent_moves = set(list(self.recent_moves)[-10:])  # Keep only last 10 moves
            else:
                self.log('panicking: no move found, breathing')
                self._panicking_wait_count = 0
                self._panicking_timer = QTimer(self)
                self._panicking_timer.setInterval(1000)  # 1 second
                self._panicking_timer.timeout.connect(self._panicking_wait_step)
                self._panicking_timer.start()
                return  # Exit to let the timer handle the rest

    def _panicking_wait_step(self):
        self._panicking_wait_count += 1
        QApplication.processEvents()
        if self._panicking_wait_count >= 7:
            self._panicking_timer.stop()
            # Continue with the rest of the panicking logic
            if self.grid_change is not None:
                max_change_index = np.unravel_index(np.argmax(self.grid_change, axis=None), self.grid_change.shape)
                r, c = max_change_index
                self.log(f'panicking: most changed ({r},{c})')
                x, y = grid_to_screen(r, c)
                try:
                    click_at(x=x, y=y)
                    time.sleep(0.3)
                    direction = np.random.choice(['up', 'down', 'left', 'right'])
                    if direction == 'up':
                        x, y = grid_to_screen(r-1, c)
                    elif direction == 'down':
                        x, y = grid_to_screen(r+1, c)
                    elif direction == 'left':
                        x, y = grid_to_screen(r, c-1)
                    elif direction == 'right':
                        x, y = grid_to_screen(r, c+1)
                    self.log(f'panicking: end {direction} ({r},{c})')
                    click_at(x=x, y=y)
                except Exception as e:
                    self.log(f"Panicking stopped: {e}")
                    self.playing = False
                    self.play_button.setChecked(False)
                    self.play_button.setText('Play')
                    self.log('paused')

def run_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_gui()
