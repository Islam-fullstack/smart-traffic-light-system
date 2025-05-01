"""
traditional_traffic_light.py - Модель традиционного светофора для системы управления трафиком.

Этот модуль реализует класс TraditionalTrafficLight для моделирования работы традиционного светофора,
а также функцию run_simulation() для демонстрации его работы в сочетании с моделью трафика.
"""

import numpy as np
from traffic_model import TrafficModel, Car

class TraditionalTrafficLight:
    """
    Класс, реализующий традиционный алгоритм работы светофора.
    
    Атрибуты:
        phase_durations (list): Длительность каждой фазы в цикле светофора.
        current_phase (int): Индекс текущей фазы.
        phase_timer (int): Таймер для отслеживания времени в текущей фазе.
        total_cars_passed (int): Общее количество пропущенных автомобилей.
        waiting_times (list): Список времени ожидания для всех пропущенных автомобилей.
    """
    def __init__(self, duration_ns=30, duration_ew=30, yellow_duration=5):
        """
        Инициализация светофора с заданными длительностями фаз.
        
        Параметры:
            duration_ns (int): Длительность фазы для направлений N-S (в секундах).
            duration_ew (int): Длительность фазы для направлений E-W (в секундах).
            yellow_duration (int): Длительность фазы "все красные" между основными фазами.
        """
        # Длительность фаз: N-S зеленый → все красные → E-W зеленый → все красные
        self.phase_durations = [duration_ns, yellow_duration, duration_ew, yellow_duration]
        self.current_phase = 0  # Текущая фаза (0-3)
        self.phase_timer = 0    # Таймер для текущей фазы
        
        self.total_cars_passed = 0  # Общее количество пропущенных автомобилей
        self.waiting_times = []     # Время ожидания для пропущенных автомобилей

    def update(self, traffic_model):
        """
        Обновляет состояние светофора и пропускает автомобили при зеленом сигнале.
        
        Параметры:
            traffic_model (TrafficModel): Модель трафика для взаимодействия с очередями автомобилей.
        """
        self.phase_timer += 1  # Увеличение таймера текущей фазы
        
        # Проверка необходимости перехода к следующей фазе
        if self.phase_timer >= self.phase_durations[self.current_phase]:
            self.current_phase = (self.current_phase + 1) % len(self.phase_durations)
            self.phase_timer = 0  # Сброс таймера
        
        # Определение направлений, которым открыт проезд в текущей фазе
        directions_to_clear = []
        if self.current_phase == 0:  # Фаза 0: N-S зеленый
            directions_to_clear = ['N', 'S']
        elif self.current_phase == 2:  # Фаза 2: E-W зеленый
            directions_to_clear = ['E', 'W']
        else:  # Фазы 1 и 3: все красные
            directions_to_clear = []

        # Пропуск автомобилей из соответствующих очередей
        for direction in directions_to_clear:
            if traffic_model.queues[direction]:  # Если есть автомобили в очереди
                car = traffic_model.queues[direction].popleft()
                self.waiting_times.append(car.waiting_time)
                self.total_cars_passed += 1

    def get_state(self):
        """
        Возвращает текущее состояние светофора по всем направлениям.
        
        Возвращает:
            dict: Состояние светофора для каждого направления ('N', 'S', 'E', 'W').
        """
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

def run_simulation():
    """
    Запускает симуляцию работы традиционного светофора с моделью трафика.
    
    Создает модель трафика и светофор, запускает симуляцию на 300 временных шагов,
    собирает и выводит статистику: среднее время ожидания, максимальное время ожидания,
    количество пропущенных автомобилей.
    """
    # Создание модели трафика с вероятностью появления автомобиля 0.2
    traffic_model = TrafficModel(arrival_prob=0.2)
    
    # Создание светофора с фазами 30 секунд для N-S и E-W, 5 секунд для промежуточных
    traffic_light = TraditionalTrafficLight(duration_ns=30, duration_ew=30, yellow_duration=5)
    
    # Запуск симуляции на 300 временных шагов
    for _ in range(300):
        traffic_model.step()          # Генерация новых автомобилей
        traffic_light.update(traffic_model)  # Обновление состояния светофора и пропуск автомобилей
    
    # Сбор статистики
    average_waiting = np.mean(traffic_light.waiting_times) if traffic_light.waiting_times else 0
    max_waiting = max(traffic_light.waiting_times) if traffic_light.waiting_times else 0
    total_passed = traffic_light.total_cars_passed
    
    # Вывод результатов
    print(f"Total cars passed: {total_passed}")
    print(f"Average waiting time: {average_waiting:.2f}")
    print(f"Maximum waiting time: {max_waiting}")

# Запуск симуляции при запуске скрипта
if __name__ == "__main__":
    run_simulation()