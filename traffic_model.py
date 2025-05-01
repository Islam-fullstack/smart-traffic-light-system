"""
traffic_model.py - Модель транспортного потока для системы умных светофоров.

Этот модуль реализует класс TrafficModel для моделирования четырехстороннего перекрестка,
генерации автомобилей и отслеживания времени ожидания в очередях. Также реализован
класс Car для представления автомобилей.
"""

import numpy as np
from collections import deque

class Car:
    """
    Класс, представляющий автомобиль в транспортном потоке.
    
    Атрибуты:
        arrival_time (int): Время прибытия автомобиля на перекресток.
        direction (str): Направление движения автомобиля ('N', 'S', 'E', 'W').
        waiting_time (int): Время ожидания автомобиля в очереди.
    """
    def __init__(self, arrival_time, direction):
        self.arrival_time = arrival_time  # Время прибытия на перекресток
        self.direction = direction        # Направление движения (N, S, E, W)
        self.waiting_time = 0             # Время ожидания в очереди (обновляется в step())

class TrafficModel:
    """
    Модель транспортного потока для четырехстороннего перекрестка.
    
    Атрибуты:
        arrival_prob (float): Вероятность появления нового автомобиля на каждом шаге.
        queues (dict): Очереди автомобилей по направлениям ('N', 'S', 'E', 'W').
        current_time (int): Текущее время моделирования (количество временных шагов).
    """
    def __init__(self, arrival_prob=0.1):
        self.queues = {
            'N': deque(),
            'S': deque(),
            'E': deque(),
            'W': deque()
        }
        self.current_time = 0

        # Поддержка числа или словаря с вероятностями
        if isinstance(arrival_prob, dict):
            # Используем вероятности из словаря, если они есть
            self.arrival_prob = {
                'N': arrival_prob.get('N', 0.0),
                'S': arrival_prob.get('S', 0.0),
                'E': arrival_prob.get('E', 0.0),
                'W': arrival_prob.get('W', 0.0)
            }
        else:
            # Используем одну вероятность для всех направлений
            self.arrival_prob = {
                'N': arrival_prob,
                'S': arrival_prob,
                'E': arrival_prob,
                'W': arrival_prob
            }

    def step(self):
        """
        Выполняет один временной шаг моделирования:
        - Генерирует новые автомобили.
        - Обновляет время ожидания всех автомобилей.
        """
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
        """
        Возвращает текущую длину очереди автомобилей в заданном направлении.
        
        Параметры:
            direction (str): Направление ('N', 'S', 'E', 'W').
        
        Возвращает:
            int: Длина очереди для указанного направления.
        """
        return len(self.queues[direction])

def main():
    """
    Пример использования модели TrafficModel:
    - Создает модель с вероятностью появления автомобилей 0.2.
    - Выполняет 100 временных шагов моделирования.
    - Выводит статистику по очередям и среднему времени ожидания.
    """
    # Создание модели с вероятностью появления автомобиля 0.2
    model = TrafficModel(arrival_prob=0.2)
    
    # Выполнение 100 временных шагов моделирования
    for _ in range(100):
        model.step()
    
    # Вывод длины очередей по направлениям
    print("Queue lengths after 100 steps:")
    for direction in ['N', 'S', 'E', 'W']:
        print(f"{direction}: {model.get_queue_length(direction)}")
    
    # Расчет общего времени ожидания и количества автомобилей
    total_waiting_time = 0
    total_cars = 0
    
    for queue in model.queues.values():
        for car in queue:
            total_waiting_time += car.waiting_time
            total_cars += 1
    
    # Расчет и вывод среднего времени ожидания
    average_waiting_time = total_waiting_time / total_cars if total_cars > 0 else 0
    print(f"Average waiting time: {average_waiting_time:.2f}")

# Запуск примера при запуске скрипта
if __name__ == "__main__":
    main()