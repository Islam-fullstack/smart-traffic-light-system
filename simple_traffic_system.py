"""
simple_traffic_system.py - Полная система управления умными светофорами

Этот файл содержит все необходимые компоненты для моделирования и визуализации
работы традиционных и умных светофоров на перекрестке. Используются только
стандартные библиотеки Python, numpy и matplotlib.

Функционал:
- Моделирование транспортного потока
- Два типа контроллеров светофоров (традиционный и умный)
- Визуализация в реальном времени
- Сбор и анализ статистики
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import argparse
import sys
import os

class Car:
    """Класс для представления автомобиля"""
    def __init__(self, arrival_time, direction):
        """
        Инициализация автомобиля
        
        Параметры:
            arrival_time: время прибытия автомобиля
            direction: направление движения (N, S, E, W)
        """
        self.arrival_time = arrival_time  # Время прибытия на перекресток
        self.direction = direction        # Направление движения
        self.waiting_time = 0             # Время ожидания в очереди

class TrafficModel:
    """Модель транспортного потока для четырехстороннего перекрестка"""
    def __init__(self, arrival_prob=0.2):
        """
        Инициализация модели
        
        Параметры:
            arrival_prob: вероятность появления нового автомобиля
        """
        # Очереди автомобилей по направлениям
        self.queues = {
            'N': deque(),  # Север
            'S': deque(),  # Юг
            'E': deque(),  # Восток
            'W': deque()   # Запад
        }
        
        # Если arrival_prob - словарь, используем разные вероятности для направлений
        if isinstance(arrival_prob, dict):
            self.arrival_prob = arrival_prob
        else:
            self.arrival_prob = {dir: arrival_prob for dir in ['N', 'S', 'E', 'W']}
            
        self.current_time = 0  # Текущее время моделирования

    def step(self):
        """Выполняет один временной шаг моделирования"""
        self.current_time += 1
        
        # Генерация новых автомобилей
        for direction in self.queues:
            if np.random.rand() < self.arrival_prob[direction]:
                new_car = Car(arrival_time=self.current_time, direction=direction)
                self.queues[direction].append(new_car)
        
        # Обновление времени ожидания для всех автомобилей
        for queue in self.queues.values():
            for car in queue:
                car.waiting_time += 1

    def get_queue_length(self, direction):
        """Возвращает длину очереди в указанном направлении"""
        return len(self.queues[direction])

class TrafficLightController:
    """Абстрактный класс контроллера светофора"""
    def update(self, model):
        """Обновляет состояние светофора"""
        raise NotImplementedError

    def get_state(self):
        """Возвращает текущее состояние светофоров"""
        raise NotImplementedError

class TraditionalTrafficLight(TrafficLightController):
    """Традиционный светофор с фиксированными фазами"""
    def __init__(self, duration_ns=30, duration_ew=30, yellow_duration=5):
        """
        Инициализация традиционного светофора
        
        Параметры:
            duration_ns: длительность фазы N-S зеленый
            duration_ew: длительность фазы E-W зеленый
            yellow_duration: длительность фазы все красные
        """
        # Длительность фаз: N-S зеленый → все красные → E-W зеленый → все красные
        self.phase_durations = [duration_ns, yellow_duration, duration_ew, yellow_duration]
        self.current_phase = 0  # Текущая фаза (0-3)
        self.phase_timer = 0    # Таймер для текущей фазы
        
        self.total_cars_passed = 0  # Общее количество пропущенных автомобилей
        self.waiting_times = []     # Время ожидания для пропущенных автомобилей

    def update(self, model):
        """
        Обновляет состояние светофора и пропускает автомобили
        
        Параметры:
            model: модель трафика
        """
        self.phase_timer += 1
        
        # Проверка необходимости перехода к следующей фазе
        if self.phase_timer >= self.phase_durations[self.current_phase]:
            self.current_phase = (self.current_phase + 1) % len(self.phase_durations)
            self.phase_timer = 0  # Сброс таймера
        
        # Определение направлений, которым открыт проезд
        directions_to_clear = []
        if self.current_phase == 0:  # Фаза 0: N-S зеленый
            directions_to_clear = ['N', 'S']
        elif self.current_phase == 2:  # Фаза 2: E-W зеленый
            directions_to_clear = ['E', 'W']
        else:  # Фазы 1 и 3: все красные
            directions_to_clear = []

        # Пропуск автомобилей из соответствующих очередей
        for direction in directions_to_clear:
            if model.queues[direction]:  # Если есть автомобили в очереди
                car = model.queues[direction].popleft()
                self.waiting_times.append(car.waiting_time)
                self.total_cars_passed += 1

    def get_state(self):
        """Возвращает текущее состояние светофора по всем направлениям"""
        state = {}
        if self.current_phase == 0:  # N-S зеленый
            state = {'N': 'green', 'S': 'green', 'E': 'red', 'W': 'red'}
        elif self.current_phase == 1:  # Все красные
            state = {'N': 'red', 'S': 'red', 'E': 'red', 'W': 'red'}
        elif self.current_phase == 2:  # E-W зеленый
            state = {'N': 'red', 'S': 'red', 'E': 'green', 'W': 'green'}
        elif self.current_phase == 3:  # Все красные
            state = {'N': 'red', 'S': 'red', 'E': 'red', 'W': 'red'}
        return state

class SmartTrafficLight(TrafficLightController):
    """Умный светофор с адаптивным управлением"""
    def __init__(self, min_duration=10, max_duration=60, weights=None):
        """
        Инициализация умного светофора
        
        Параметры:
            min_duration: минимальная длительность фазы
            max_duration: максимальная длительность фазы
            weights: весовые коэффициенты для направлений
        """
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.weights = weights if weights else {'NS': 1.0, 'EW': 1.0}
        self.current_direction = 'NS'  # Начальное направление
        self.phase_duration = 0        # Текущий счетчик длительности фазы
        self.current_duration = 0      # Рассчитанная длительность текущей фазы
        self.total_cars_passed = 0     # Общее количество пропущенных автомобилей
        self.waiting_times = []        # Время ожидания для пропущенных автомобилей

    def calculate_priority(self, queues):
        """
        Оценивает приоритет каждого направления
        
        Параметры:
            queues: длины очередей по направлениям
            
        Возвращает:
            приоритеты для направлений
        """
        # Сумма очередей для N-S и E-W направлений
        ns_queue = queues['N'] + queues['S']
        ew_queue = queues['E'] + queues['W']
        
        # Расчет приоритетов с учетом весовых коэффициентов
        ns_priority = ns_queue * self.weights['NS']
        ew_priority = ew_queue * self.weights['EW']
        
        return {'NS': ns_priority, 'EW': ew_priority}

    def update(self, model):
        """
        Обновляет состояние светофора и пропускает автомобили
        
        Параметры:
            model: модель трафика
        """
        # Получаем длины очередей по всем направлениям
        queues = {direction: len(model.queues[direction]) for direction in ['N', 'S', 'E', 'W']}
        
        # Если фаза только начинается, вычисляем ее длительность
        if self.phase_duration == 0:
            self.current_duration = self.get_current_phase_duration(queues)
        
        # Проверяем, не истекла ли текущая фаза
        if self.phase_duration >= self.current_duration or self.phase_duration >= self.max_duration:
            # Получаем приоритеты направлений
            priorities = self.calculate_priority(queues)
            
            # Выбираем направление с максимальным приоритетом
            if priorities['NS'] > priorities['EW']:
                self.current_direction = 'NS'
            else:
                self.current_direction = 'EW'
            
            # Сбрасываем счетчик фазы и вычисляем новую длительность
            self.phase_duration = 0
            self.current_duration = self.get_current_phase_duration(queues)
        else:
            self.phase_duration += 1
        
        # Пропускаем автомобили из соответствующих очередей
        directions_to_clear = []
        if self.current_direction == 'NS':
            directions_to_clear = ['N', 'S']
        else:
            directions_to_clear = ['E', 'W']
        
        for direction in directions_to_clear:
            if model.queues[direction]:  # Если есть автомобили в очереди
                car = model.queues[direction].popleft()
                self.waiting_times.append(car.waiting_time)
                self.total_cars_passed += 1

    def get_current_phase_duration(self, queues):
        """
        Рассчитывает оптимальную длительность текущей фазы
        
        Параметры:
            queues: длины очередей по направлениям
            
        Возвращает:
            рассчитанная длительность фазы
        """
        # Определяем текущую сумму очередей и максимальную очередь
        if self.current_direction == 'NS':
            current_sum = queues['N'] + queues['S']
        else:
            current_sum = queues['E'] + queues['W']
        
        max_queue = max(queues['N'] + queues['S'], queues['E'] + queues['W'])
        
        # Избегаем деления на ноль
        if max_queue == 0:
            return self.min_duration
        
        # Рассчитываем длительность фазы по формуле
        duration = self.min_duration + (self.max_duration - self.min_duration) * (current_sum / max_queue)
        
        # Ограничиваем длительность в пределах min и max
        return int(round(np.clip(duration, self.min_duration, self.max_duration)))

    def get_state(self):
        """Возвращает текущее состояние светофора по всем направлениям"""
        state = {}
        if self.current_direction == 'NS':
            state = {'N': 'green', 'S': 'green', 'E': 'red', 'W': 'red'}
        else:
            state = {'N': 'red', 'S': 'red', 'E': 'green', 'W': 'green'}
        return state

class Simulation:
    """Класс для запуска симуляции и сбора статистики"""
    def __init__(self, algorithm='traditional', traffic_pattern='uniform', duration=500):
        """
        Инициализация симуляции
        
        Параметры:
            algorithm: тип алгоритма ('traditional' или 'smart')
            traffic_pattern: шаблон трафика
            duration: длительность симуляции
        """
        # Настройка шаблона трафика
        self.traffic_patterns = {
            'uniform': {'N': 0.2, 'S': 0.2, 'E': 0.2, 'W': 0.2},
            'ns_peak': {'N': 0.4, 'S': 0.4, 'E': 0.1, 'W': 0.1},
            'ew_peak': {'N': 0.1, 'S': 0.1, 'E': 0.4, 'W': 0.4},
            'high_load': {'N': 0.3, 'S': 0.3, 'E': 0.3, 'W': 0.3}
        }
        
        self.traffic_pattern = traffic_pattern
        self.duration = duration
        
        # Создание модели трафика
        self.model = TrafficModel(self.traffic_patterns[traffic_pattern])
        
        # Создание контроллера светофоров
        if algorithm == 'traditional':
            self.controller = TraditionalTrafficLight(duration_ns=30, duration_ew=30, yellow_duration=5)
        else:
            self.controller = SmartTrafficLight(min_duration=10, max_duration=60)

    def run(self):
        """Запуск симуляции"""
        # Список для хранения истории длин очередей
        queue_history = []
        
        # Запуск симуляции
        for _ in range(self.duration):
            self.model.step()
            self.controller.update(self.model)
            
            # Сохранение текущих длин очередей
            current_queues = {direction: len(self.model.queues[direction]) for direction in ['N', 'S', 'E', 'W']}
            queue_history.append(current_queues)
        
        # Расчет метрик
        waiting_times = self.controller.waiting_times if hasattr(self.controller, 'waiting_times') else []
        
        # Среднее время ожидания
        avg_waiting = np.mean(waiting_times) if waiting_times else 0
        
        # Максимальное время ожидания
        max_waiting = np.max(waiting_times) if waiting_times else 0
        
        # Количество пропущенных автомобилей
        cars_passed = self.controller.total_cars_passed if hasattr(self.controller, 'total_cars_passed') else 0
        
        # Средняя длина очереди (по всем направлениям и временным шагам)
        avg_queue_length = np.mean([sum(step.values()) for step in queue_history])
        
        # Процент времени с пустыми очередями
        empty_queue_steps = sum(1 for step in queue_history if sum(step.values()) == 0)
        empty_queue_percentage = (empty_queue_steps / self.duration) * 100
        
        return {
            'algorithm': self.controller.__class__.__name__,
            'pattern': self.traffic_pattern,
            'avg_waiting': avg_waiting,
            'max_waiting': max_waiting,
            'cars_passed': cars_passed,
            'avg_queue_length': avg_queue_length,
            'empty_queue_percentage': empty_queue_percentage
        }

class Visualization:
    """Класс для визуализации модели в реальном времени"""
    def __init__(self, model, controller):
        """
        Инициализация визуализации
        
        Параметры:
            model: модель трафика
            controller: контроллер светофоров
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
        """Настраивает все подграфики"""
        # 1. Схема перекрестка
        ax = self.axs[0, 0]
        ax.set_title('Схема перекрестка')
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.axis('off')
        
        # Рисуем дороги
        ax.add_patch(plt.Rectangle((-1, -0.1), 2, 0.2, color='gray'))
        ax.add_patch(plt.Rectangle((-0.1, -1), 0.2, 2, color='gray'))
        
        # Инициализация автомобилей
        self.car_patches = {
            'N': [],  # Автомобили с севера
            'S': [],  # Автомобили с юга
            'E': [],  # Автомобили с востока
            'W': []   # Автомобили с запада
        }
        
        # Инициализация светофоров
        self.traffic_light_patches = {
            'N': ax.add_patch(plt.Rectangle((0.7, 0.1), 0.05, 0.1, color='gray')),
            'S': ax.add_patch(plt.Rectangle((-0.75, -0.2), 0.05, 0.1, color='gray')),
            'E': ax.add_patch(plt.Rectangle((0.1, 0.7), 0.1, 0.05, color='gray')),
            'W': ax.add_patch(plt.Rectangle((-0.2, -0.75), 0.1, 0.05, color='gray'))
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
    
    def update_visualization(self, frame):
        """
        Обновляет все элементы визуализации
        
        Параметры:
            frame: номер текущего кадра
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
    
    def update_cars(self):
        """Обновляет отображение автомобилей"""
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
                        plt.Rectangle((x, y - i*0.05), 0.03, 0.03, color='black'))
                else:
                    patch = self.axs[0, 0].add_patch(
                        plt.Rectangle((x - i*0.05, y), 0.03, 0.03, color='black'))
                self.car_patches[direction].append(patch)
    
    def update_traffic_lights(self):
        """Обновляет цвета светофоров"""
        state = self.controller.get_state()
        for direction, patch in self.traffic_light_patches.items():
            color = 'green' if state[direction] == 'green' else 'red'
            patch.set_color(color)
    
    def update_waiting_time(self, frame):
        """Обновляет график среднего времени ожидания"""
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
        """Обновляет гистограмму длин очередей"""
        for i, direction in enumerate(['N', 'S', 'E', 'W']):
            length = len(self.model.queues[direction])
            self.bar_rects[i].set_width(length)
        
        # Автоматическое обновление пределов оси X
        max_length = max(len(self.model.queues[d]) for d in ['N', 'S', 'E', 'W'])
        self.axs[1, 0].set_xlim(0, max(max_length + 1, 5))
    
    def update_statistics(self):
        """Обновляет текстовую статистику"""
        stats = (
            f"Пропущено автомобилей: {self.controller.total_cars_passed}\n"
            f"Текущая фаза: {self.controller.current_direction}\n"
            f"Текущая длительность: {self.controller.phase_duration}/{self.controller.current_duration}\n"
            f"Текущее время: {self.model.current_time}"
        )
        self.text_stats.set_text(stats)
    
    def get_all_artists(self):
        """Возвращает все элементы matplotlib для анимации"""
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
        """Запускает анимацию"""
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

def main():
    """Основная функция для запуска примеров"""
    parser = argparse.ArgumentParser(description='Симуляция системы управления светофорами')
    parser.add_argument('-a', '--algorithm', 
                        choices=['traditional', 'smart'],
                        default='smart',
                        help='Выбор алгоритма управления светофорами')
    parser.add_argument('-d', '--duration',
                        type=int,
                        default=500,
                        help='Длительность симуляции в шагах')
    parser.add_argument('-v', '--visualize',
                        action='store_true',
                        help='Включить визуализацию симуляции')
    
    args = parser.parse_args()
    
    print("Запуск примера с традиционным алгоритмом:")
    traditional_sim = Simulation('traditional', 'ns_peak', args.duration)
    traditional_results = traditional_sim.run()
    print(f"Среднее время ожидания: {traditional_results['avg_waiting']:.2f}")
    print(f"Количество пропущенных автомобилей: {traditional_results['cars_passed']}")
    
    print("\nЗапуск примера с умным алгоритмом:")
    smart_sim = Simulation('smart', 'ns_peak', args.duration)
    smart_results = smart_sim.run()
    print(f"Среднее время ожидания: {smart_results['avg_waiting']:.2f}")
    print(f"Количество пропущенных автомобилей: {smart_results['cars_passed']}")
    
    print("\nСравнение алгоритмов:")
    print("Традиционный:")
    print(f"Среднее время ожидания: {traditional_results['avg_waiting']:.2f}")
    print(f"Количество пропущенных автомобилей: {traditional_results['cars_passed']}")
    print("\nУмный:")
    print(f"Среднее время ожидания: {smart_results['avg_waiting']:.2f}")
    print(f"Количество пропущенных автомобилей: {smart_results['cars_passed']}")
    
    # Построение графиков сравнения
    plt.figure(figsize=(10, 5))
    algorithms = ['Традиционный', 'Умный']
    waiting_times = [traditional_results['avg_waiting'], smart_results['avg_waiting']]
    cars_passed = [traditional_results['cars_passed'], smart_results['cars_passed']]
    
    plt.subplot(1, 2, 1)
    plt.bar(algorithms, waiting_times, color=['red', 'green'])
    plt.title('Среднее время ожидания')
    plt.ylabel('Время')
    
    plt.subplot(1, 2, 2)
    plt.bar(algorithms, cars_passed, color=['blue', 'orange'])
    plt.title('Количество пропущенных автомобилей')
    plt.ylabel('Автомобили')
    
    plt.tight_layout()
    plt.savefig('comparison.png')
    plt.show()
    
    # Запуск визуализации, если указан флаг
    if args.visualize:
        print("\nЗапуск визуализации...")
        model = TrafficModel({'N': 0.3, 'S': 0.3, 'E': 0.1, 'W': 0.1})
        controller = SmartTrafficLight(min_duration=10, max_duration=60)
        viz = Visualization(model, controller)
        viz.start_animation(frames=300)

if __name__ == "__main__":
    main()