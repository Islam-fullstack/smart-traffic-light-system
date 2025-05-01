"""
smart_traffic_light.py - Модель умного светофора с адаптивным управлением.

Этот модуль реализует класс SmartTrafficLight для моделирования адаптивного светофора,
который динамически изменяет длительность фаз на основе загруженности направлений.
"""

import numpy as np
from traffic_model import TrafficModel, Car

class SmartTrafficLight:
    """
    Класс, реализующий умный алгоритм управления светофором с адаптивной фазировкой.
    
    Атрибуты:
        min_duration (int): Минимальная длительность фазы (в временных шагах).
        max_duration (int): Максимальная длительность фазы (в временных шагах).
        weights (dict): Весовые коэффициенты для оценки приоритета направлений.
        current_direction (str): Текущее активное направление ('NS' или 'EW').
        phase_duration (int): Текущая длительность активной фазы.
        current_duration (int): Рассчитанная длительность текущей фазы.
        total_cars_passed (int): Общее количество пропущенных автомобилей.
        waiting_times (list): Список времени ожидания для всех пропущенных автомобилей.
    """
    def __init__(self, min_duration=10, max_duration=60, weights=None):
        """
        Инициализация умного светофора с заданными параметрами.
        
        Параметры:
            min_duration (int): Минимальная длительность фазы (по умолчанию 10).
            max_duration (int): Максимальная длительность фазы (по умолчанию 60).
            weights (dict): Весовые коэффициенты для направлений (по умолчанию {'NS': 1.0, 'EW': 1.0}).
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
        Оценивает приоритет каждого направления на основе очередей и времени ожидания.
        
        Параметры:
            queues (dict): Длины очередей по всем направлениям.
        
        Возвращает:
            dict: Приоритеты для направлений 'NS' и 'EW'.
        """
        # Сумма очередей для N-S и E-W направлений
        ns_queue = queues['N'] + queues['S']
        ew_queue = queues['E'] + queues['W']
        
        # Среднее время ожидания по направлениям (если есть автомобили)
        ns_waiting = np.mean([car.waiting_time for car in queues['N'] + queues['S']]) if queues['N'] or queues['S'] else 0
        ew_waiting = np.mean([car.waiting_time for car in queues['E'] + queues['W']]) if queues['E'] or queues['W'] else 0
        
        # Расчет приоритетов с учетом весовых коэффициентов и времени ожидания
        ns_priority = (ns_queue * self.weights['NS']) + (ns_waiting * 0.5)
        ew_priority = (ew_queue * self.weights['EW']) + (ew_waiting * 0.5)
        
        return {'NS': ns_priority, 'EW': ew_priority}

    def update(self, traffic_model):
        """
        Обновляет состояние светофора и пропускает автомобили на каждом временном шаге.
        
        Параметры:
            traffic_model (TrafficModel): Модель трафика для взаимодействия с очередями автомобилей.
        """
        # Получаем длины очередей по всем направлениям
        queues = {direction: len(traffic_model.queues[direction]) for direction in ['N', 'S', 'E', 'W']}
        
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
        
        # Пропускаем автомобили в зависимости от текущего направления
        directions_to_clear = []
        if self.current_direction == 'NS':
            directions_to_clear = ['N', 'S']
        else:
            directions_to_clear = ['E', 'W']
        
        for direction in directions_to_clear:
            if traffic_model.queues[direction]:  # Если есть автомобили в очереди
                car = traffic_model.queues[direction].popleft()
                self.waiting_times.append(car.waiting_time)
                self.total_cars_passed += 1

    def get_current_phase_duration(self, queues):
        """
        Рассчитывает оптимальную длительность текущей фазы на основе очередей.
        
        Параметры:
            queues (dict): Длины очередей по всем направлениям.
        
        Возвращает:
            int: Рассчитанная длительность фазы.
        """
        # Определяем текущую сумму очередей и максимальную очередь
        if self.current_direction == 'NS':
            current_sum = queues['N'] + queues['S']
        else:
            current_sum = queues['E'] + queues['W']
        
        # Максимальная сумма очередей между N-S и E-W
        max_queue = max(queues['N'] + queues['S'], queues['E'] + queues['W'])
        
        # Избегаем деления на ноль
        if max_queue == 0:
            return self.min_duration
        
        # Рассчитываем длительность фазы по формуле
        duration = self.min_duration + (self.max_duration - self.min_duration) * (current_sum / max_queue)
        
        # Ограничиваем длительность в пределах min и max
        return int(round(np.clip(duration, self.min_duration, self.max_duration)))

    def get_state(self):
        """
        Возвращает текущее состояние светофора по всем направлениям.
        
        Возвращает:
            dict: Состояние светофора для каждого направления ('N', 'S', 'E', 'W').
        """
        state = {}
        if self.current_direction == 'NS':
            state = {'N': 'green', 'S': 'green', 'E': 'red', 'W': 'red'}
        else:
            state = {'N': 'red', 'S': 'red', 'E': 'green', 'W': 'green'}
        return state

def run_simulation():
    """
    Запускает симуляцию работы умного светофора с моделью трафика.
    
    Создает модель трафика с неравномерной интенсивностью (0.3 для N-S, 0.1 для E-W),
    умный светофор с параметрами min_duration=10, max_duration=60,
    запускает симуляцию на 300 временных шагов,
    собирает и выводит статистику: среднее время ожидания, максимальное время ожидания,
    количество пропущенных автомобилей.
    """
    # Создание модели трафика с неравномерной интенсивностью
    # Здесь предполагается, что TrafficModel был модифицирован для принятия словаря вероятностей
    # В оригинальном TrafficModel из traffic_model.py это не предусмотрено, поэтому
    # для корректной работы необходимо внести изменения в TrafficModel
    try:
        # Пытаемся создать TrafficModel с разными вероятностями для направлений
        traffic_model = TrafficModel(arrival_prob={'N': 0.3, 'S': 0.3, 'E': 0.1, 'W': 0.1})
    except TypeError:
        # Если оригинальный TrafficModel не поддерживает разные вероятности,
        # создаем с базовой вероятностью и предупреждаем пользователя
        print("Внимание: Оригинальный TrafficModel не поддерживает разные вероятности для направлений.")
        print("Результаты симуляции могут не отражать неравномерную загрузку.")
        traffic_model = TrafficModel(arrival_prob=0.2)
    
    # Создание умного светофора
    traffic_light = SmartTrafficLight(min_duration=10, max_duration=60)
    
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