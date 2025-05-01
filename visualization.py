"""
visualization.py - Визуализация модели управления светофорами.

Этот модуль реализует класс TrafficVisualization для отображения состояния перекрестка,
времени ожидания, длин очередей и статистики в реальном времени с использованием matplotlib.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle

from traffic_model import TrafficModel, Car
from smart_traffic_light import SmartTrafficLight  # Можно использовать и TraditionalTrafficLight

class TrafficVisualization:
    """
    Класс для визуализации модели трафика и работы светофоров.
    
    Атрибуты:
        model (TrafficModel): Модель трафика.
        controller (SmartTrafficLight): Контроллер светофоров.
        fig (matplotlib.figure.Figure): Фигура matplotlib для отображения графиков.
        axs (numpy.ndarray): Массив осей графиков (2x2).
        waiting_time_data (list): История среднего времени ожидания.
        bar_rects (dict): Словарь с прямоугольниками для гистограммы очередей.
        text_stats (matplotlib.text.Text): Текстовая статистика.
        car_patches (dict): Словарь с элементами для отображения автомобилей.
    """
    def __init__(self, model, controller):
        """
        Инициализация визуализации с заданной моделью и контроллером.
        
        Параметры:
            model (TrafficModel): Модель трафика.
            controller (SmartTrafficLight): Контроллер светофоров.
        """
        self.model = model
        self.controller = controller
        
        # Инициализация данных для графиков
        self.waiting_time_data = []
        
        # Создание фигуры и осей
        self.fig, self.axs = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('Система управления трафиком на перекрестке', fontsize=16)
        
        # Инициализация графиков
        self.setup_plot()
    
    def setup_plot(self):
        """
        Настраивает все подграфики (4 области визуализации).
        """
        # 1. Схема перекрестка
        ax = self.axs[0, 0]
        ax.set_title('Схема перекрестка')
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.axis('off')
        
        # Рисуем дороги
        ax.add_patch(Rectangle((-1, -0.1), 2, 0.2, color='gray'))
        ax.add_patch(Rectangle((-0.1, -1), 0.2, 2, color='gray'))
        
        # Инициализация автомобилей
        self.car_patches = {
            'N': [],  # Автомобили с севера
            'S': [],  # Автомобили с юга
            'E': [],  # Автомобили с востока
            'W': []   # Автомобили с запада
        }
        
        # Инициализация светофоров
        self.traffic_light_patches = {
            'N': ax.add_patch(Rectangle((0.7, 0.1), 0.05, 0.1, color='gray')),
            'S': ax.add_patch(Rectangle((-0.75, -0.2), 0.05, 0.1, color='gray')),
            'E': ax.add_patch(Rectangle((0.1, 0.7), 0.1, 0.05, color='gray')),
            'W': ax.add_patch(Rectangle((-0.2, -0.75), 0.1, 0.05, color='gray'))
        }
        
        # 2. График времени ожидания
        ax = self.axs[0, 1]
        ax.set_title('Среднее время ожидания')
        ax.set_xlabel('Временные шаги')
        ax.set_ylabel('Время ожидания')
        ax.grid(True)
        self.waiting_time_line, = ax.plot([], [], 'b-', lw=2)
        self.waiting_time_avg_line, = ax.plot([], [], 'r--', lw=1)
        
        # 3. Гистограмма длин очередей
        ax = self.axs[1, 0]
        ax.set_title('Длина очередей по направлениям')
        directions = ['N', 'S', 'E', 'W']
        self.bar_rects = ax.barh(directions, [0]*4, color=['blue', 'green', 'red', 'purple'])
        ax.set_xlim(0, 20)  # Максимальная длина очереди для отображения
        
        # 4. Текстовая статистика
        ax = self.axs[1, 1]
        ax.axis('off')
        self.text_stats = ax.text(0.1, 0.5, '', fontsize=12, verticalalignment='center')
    
    def update_cars(self):
        """
        Обновляет отображение автомобилей на схеме перекрестка.
        """
        # Удаление старых автомобилей
        for direction in self.car_patches:
            for patch in self.car_patches[direction]:
                patch.remove()
            self.car_patches[direction] = []
        
        # Добавление новых автомобилей
        positions = {
            'N': (-0.2, 0.2),  # Север
            'S': (0.2, -0.2),  # Юг
            'E': (0.2, 0.2),   # Восток
            'W': (-0.2, -0.2)  # Запад
        }
        
        for direction in ['N', 'S', 'E', 'W']:
            queue = self.model.queues[direction]
            for i in range(len(queue)):
                x, y = positions[direction]
                # Расположение автомобилей в линию
                if direction in ['N', 'S']:
                    patch = self.axs[0, 0].add_patch(
                        Rectangle((x, y - i*0.05), 0.03, 0.03, color='black'))
                else:
                    patch = self.axs[0, 0].add_patch(
                        Rectangle((x - i*0.05, y), 0.03, 0.03, color='black'))
                self.car_patches[direction].append(patch)
    
    def update_traffic_lights(self):
        """
        Обновляет цвета светофоров в соответствии с текущим состоянием.
        """
        state = self.controller.get_state()
        for direction, patch in self.traffic_light_patches.items():
            color = 'green' if state[direction] == 'green' else 'red'
            patch.set_color(color)
    
    def update_waiting_time(self, frame):
        """
        Обновляет график среднего времени ожидания.
        """
        if self.controller.waiting_times:
            current_avg = np.mean(self.controller.waiting_times[-min(10, len(self.controller.waiting_times)):])
        else:
            current_avg = 0
        
        self.waiting_time_data.append(current_avg)
        
        # Обновление линий графика
        self.waiting_time_line.set_data(range(len(self.waiting_time_data)), self.waiting_time_data)
        self.waiting_time_avg_line.set_data([0, len(self.waiting_time_data)], 
                                           [current_avg, current_avg])
        
        # Автоматическое масштабирование
        self.axs[0, 1].relim()
        self.axs[0, 1].autoscale_view()
    
    def update_queue_lengths(self):
        """
        Обновляет гистограмму длин очередей.
        """
        for i, direction in enumerate(['N', 'S', 'E', 'W']):
            length = len(self.model.queues[direction])
            self.bar_rects[i].set_width(length)
        
        # Автоматическое обновление пределов оси X
        max_length = max(len(self.model.queues[d]) for d in ['N', 'S', 'E', 'W'])
        self.axs[1, 0].set_xlim(0, max(max_length + 1, 5))
    
    def update_statistics(self):
        """
        Обновляет текстовую статистику.
        """
        stats = (
            f"Пропущено автомобилей: {self.controller.total_cars_passed}\n"
            f"Текущая фаза: {self.controller.current_direction}\n"
            f"Текущая длительность: {self.controller.phase_duration}/{self.controller.current_duration}\n"
            f"Текущее время: {self.model.current_time}"
        )
        self.text_stats.set_text(stats)
    
    def update_visualization(self, frame):
        """
        Обновляет все элементы визуализации на каждом шаге симуляции.
        
        Параметры:
            frame (int): Номер текущего кадра (не используется).
        """
        # Шаг моделирования
        self.model.step()
        self.controller.update(self.model)
        
        # Обновление отдельных частей визуализации
        self.update_cars()
        self.update_traffic_lights()
        self.update_waiting_time(frame)
        self.update_queue_lengths()
        self.update_statistics()
        
        return self.get_all_artists()
    
    def get_all_artists(self):
        """
        Возвращает все элементы matplotlib для анимации.
        
        Возвращает:
            list: Список всех обновляемых элементов.
        """
        artists = [
            self.waiting_time_line, self.waiting_time_avg_line,
            self.text_stats
        ]
        
        # Добавление всех автомобилей
        for direction in self.car_patches:
            artists.extend(self.car_patches[direction])
        
        # Добавление всех светофоров
        for patch in self.traffic_light_patches.values():
            artists.append(patch)
        
        # Добавление всех столбцов гистограммы
        artists.extend(self.bar_rects)
        
        return artists
    
    def start_animation(self, frames=300, interval=200):
        """
        Запускает анимацию с заданными параметрами.
        
        Параметры:
            frames (int): Количество кадров анимации.
            interval (int): Интервал между кадрами в миллисекундах.
        """
        ani = animation.FuncAnimation(
            self.fig, 
            self.update_visualization, 
            frames=frames, 
            interval=interval,
            blit=True
        )
        plt.tight_layout()
        plt.show()
        return ani
    
    def save_animation(self, ani, filename='traffic_simulation.mp4', writer='ffmpeg'):
        """
        Сохраняет анимацию в файл.
        
        Параметры:
            ani (FuncAnimation): Анимация для сохранения.
            filename (str): Имя файла для сохранения.
            writer (str): Используемый writer ('ffmpeg' или 'pillow').
        """
        if writer == 'ffmpeg':
            Writer = animation.writers['ffmpeg']
            writer = Writer(fps=5, metadata=dict(artist='Me'), bitrate=1800)
        elif writer == 'pillow':
            writer = animation.PillowWriter(fps=5)
        
        ani.save(filename, writer=writer)

def main():
    """
    Основная функция для запуска визуализации.
    """
    # Создание модели трафика с неравномерной интенсивностью
    # Требуется модифицированный TrafficModel из traffic_model.py
    try:
        model = TrafficModel(arrival_prob={'N': 0.3, 'S': 0.3, 'E': 0.1, 'W': 0.1})
    except TypeError:
        print("Внимание: Оригинальный TrafficModel не поддерживает разные вероятности для направлений.")
        print("Используется базовая вероятность 0.2 для всех направлений.")
        model = TrafficModel(arrival_prob=0.2)
    
    # Создание умного светофора
    controller = SmartTrafficLight(min_duration=10, max_duration=60)
    
    # Создание визуализации
    viz = TrafficVisualization(model, controller)
    
    # Запуск анимации
    ani = viz.start_animation(frames=300)
    
    # Сохранение анимации (при необходимости)
    # viz.save_animation(ani, filename='smart_traffic_simulation.mp4', writer='ffmpeg')

# Запуск основной функции при запуске скрипта
if __name__ == "__main__":
    main()