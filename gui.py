import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSlider, QWidget,
    QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

def create_app():
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()  # твой класс главного окна
    window.show()
    return app
    
class HeatModel:
    def __init__(self, nx=50, ny=50, dx=1.0, dt=0.2, alpha=0.1, nsteps=200, injection_rate=0.0):
        self.nx = nx
        self.ny = ny
        self.dx = dx
        self.dt = dt
        self.alpha = alpha
        self.nsteps = nsteps
        self.injection_rate = injection_rate  # параметр закачки
        self.T = np.zeros((nx, ny))
        # Начальная температура с градиентом
        for i in range(nx):
            self.T[i, :] = 150 - i * (100 / (nx - 1))

        # Граничные условия
        self.T[0, :] = 150
        self.T[-1, :] = 50
        self.T[:, 0] = 150
        self.T[:, -1] = 50

    def solve_heat(self):
        T = self.T.copy()
        results = [T.copy()]
        for step in range(self.nsteps):
            T_new = T.copy()
            for i in range(1, self.nx - 1):
                for j in range(1, self.ny - 1):
                    d2Tdx2 = (T[i + 1, j] - 2 * T[i, j] + T[i - 1, j]) / self.dx ** 2
                    d2Tdy2 = (T[i, j + 1] - 2 * T[i, j] + T[i, j - 1]) / self.dx ** 2
                    T_new[i, j] = T[i, j] + self.alpha * self.dt * (d2Tdx2 + d2Tdy2)

            # Пример влияния закачки: повышаем температуру в центре резервуара пропорционально injection_rate
            center_x, center_y = self.nx // 2, self.ny // 2
            T_new[center_x, center_y] += self.injection_rate * 5  # усиливаем эффект

            # Копируем для следующего шага
            T = T_new
            results.append(T.copy())
        return results


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Прогноз дрейфа температуры геотермального резервуара — Неделя 4")

        # Начальный параметр закачки — 0 (нет закачки)
        self.injection_rate = 0.0

        # Создаем модель с параметром закачки
        self.model = HeatModel(injection_rate=self.injection_rate)
        self.T_results = self.model.solve_heat()

        # Создаем график matplotlib
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # Создаем ползунок для выбора шага времени
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.T_results) - 1)
        self.slider.valueChanged.connect(self.update_plot)

        # Кнопки управления анимацией
        self.btn_start = QPushButton("Старт")
        self.btn_pause = QPushButton("Пауза")
        self.btn_reset = QPushButton("Сброс")
        self.btn_apply = QPushButton("Применить закачку")

        self.btn_start.clicked.connect(self.start_animation)
        self.btn_pause.clicked.connect(self.pause_animation)
        self.btn_reset.clicked.connect(self.reset_animation)
        self.btn_apply.clicked.connect(self.apply_injection)

        # Таймер для анимации
        self.timer = QTimer()
        self.timer.setInterval(100)  # 100 мс между кадрами (можно менять)
        self.timer.timeout.connect(self.next_frame)

        # Поле ввода параметра закачки
        self.input_injection = QLineEdit()
        self.input_injection.setPlaceholderText("Введите скорость закачки (например, 0.0)")

        # Разметка кнопок и ввода
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addWidget(QLabel("Скорость закачки:"))
        btn_layout.addWidget(self.input_injection)
        btn_layout.addWidget(self.btn_apply)

        # Основной вертикальный слой
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.slider)
        layout.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Начальное состояние
        self.current_step = 0
        self.im = self.ax.imshow(
            self.T_results[0], cmap="hot", origin="lower", vmin=50, vmax=150
        )
        self.colorbar = self.figure.colorbar(self.im, ax=self.ax)
        self.title = self.ax.set_title("Температурный срез, шаг 0")

    def update_plot(self, step):
        self.current_step = step
        self.im.set_data(self.T_results[step])
        self.title.set_text(
            f"Температурный срез, шаг {step}\nМин: {self.T_results[step].min():.2f}°C, Макс: {self.T_results[step].max():.2f}°C"
        )
        self.canvas.draw_idle()

    def start_animation(self):
        self.timer.start()

    def pause_animation(self):
        self.timer.stop()

    def reset_animation(self):
        self.timer.stop()
        self.current_step = 0
        self.slider.setValue(0)

    def next_frame(self):
        if self.current_step < len(self.T_results) - 1:
            self.current_step += 1
        else:
            self.current_step = 0
        self.slider.setValue(self.current_step)

    def apply_injection(self):
        # Считать параметр закачки из поля ввода
        try:
            val = float(self.input_injection.text())
            if val < 0:
                raise ValueError("Скорость закачки не может быть отрицательной.")
            self.injection_rate = val
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", f"Неверное значение скорости закачки:\n{e}")
            return

        # Пересчитать модель с новым параметром закачки
        self.model = HeatModel(injection_rate=self.injection_rate)
        self.T_results = self.model.solve_heat()

        # Обновить слайдер
        self.slider.setMaximum(len(self.T_results) - 1)
        self.slider.setValue(0)
        self.update_plot(0)

        QMessageBox.information(self, "Обновлено", f"Параметр закачки установлен: {self.injection_rate}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())