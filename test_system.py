"""
test_system.py - Тестирование компонентов системы управления светофорами.

Этот модуль реализует тесты для проверки корректности работы всех компонентов системы:
- Модели трафика
- Традиционного светофора
- Умного светофора

Используется библиотека unittest для тестирования.
"""

import unittest
import numpy as np
from traffic_model import TrafficModel, Car
from traditional_traffic_light import TraditionalTrafficLight
from smart_traffic_light import SmartTrafficLight
from comparison import run_experiment

class TestTrafficModel(unittest.TestCase):
    """Тестирование класса TrafficModel."""
    
    def test_car_generation(self):
        """Проверяет корректность генерации автомобилей."""
        # Тест с вероятностью 1.0 (все автомобили должны появляться)
        model = TrafficModel(arrival_prob=1.0)
        for _ in range(5):  # Несколько шагов для стабильности
            model.step()
        
        # Проверка, что автомобили появились во всех направлениях
        for direction in ['N', 'S', 'E', 'W']:
            with self.subTest(direction=direction):
                self.assertGreater(len(model.queues[direction]), 0)
    
    def test_waiting_time(self):
        """Проверяет правильность подсчета времени ожидания."""
        # Создаем модель с нулевой вероятностью появления новых автомобилей
        model = TrafficModel(arrival_prob=0.0)
        
        # Добавляем тестовый автомобиль
        test_car = Car(arrival_time=0, direction='N')
        model.queues['N'].append(test_car)
        
        # Выполняем несколько шагов моделирования
        for _ in range(5):
            model.step()
        
        # Проверяем, что время ожидания увеличилось на количество шагов
        self.assertEqual(test_car.waiting_time, 5)
    
    def test_queue_length(self):
        """Проверяет точность определения длины очереди."""
        model = TrafficModel(arrival_prob=0.0)
        
        # Добавляем 3 автомобиля в очередь севера
        for _ in range(3):
            model.queues['N'].append(Car(arrival_time=0, direction='N'))
        
        # Проверяем, что get_queue_length возвращает правильное значение
        self.assertEqual(model.get_queue_length('N'), 3)

class TestTraditionalTrafficLight(unittest.TestCase):
    """Тестирование класса TraditionalTrafficLight."""
    
    def test_phase_switching(self):
        """Проверяет правильность переключения фаз светофора."""
        light = TraditionalTrafficLight(duration_ns=2, duration_ew=2, yellow_duration=1)
        model = TrafficModel(arrival_prob=0.0)

        # Ожидаемая последовательность фаз
        expected_phases = [0, 1, 2, 3, 0]  # Полный цикл и еще один шаг

        # Выполняем шаги и проверяем последовательность фаз
        for expected_phase in expected_phases:
            with self.subTest(phase=expected_phase):
                # Выполняем столько шагов, сколько нужно для завершения текущей фазы
                while light.phase_timer < light.phase_durations[light.current_phase]:
                    light.update(model)
                self.assertEqual(light.current_phase, expected_phase)
                light.phase_timer = 0  # Сбрасываем таймер для следующей фазы
    
    def test_get_state(self):
        """Проверяет корректность метода get_state()."""
        light = TraditionalTrafficLight()
        model = TrafficModel(arrival_prob=0.0)
        
        # Тест всех фаз
        for phase in range(4):
            light.current_phase = phase
            state = light.get_state()
            
            with self.subTest(phase=phase):
                if phase == 0:  # N-S зеленый
                    self.assertEqual(state['N'], 'green')
                    self.assertEqual(state['S'], 'green')
                    self.assertEqual(state['E'], 'red')
                    self.assertEqual(state['W'], 'red')
                elif phase == 1 or phase == 3:  # Все красные
                    for direction in ['N', 'S', 'E', 'W']:
                        self.assertEqual(state[direction], 'red')
                elif phase == 2:  # E-W зеленый
                    self.assertEqual(state['N'], 'red')
                    self.assertEqual(state['S'], 'red')
                    self.assertEqual(state['E'], 'green')
                    self.assertEqual(state['W'], 'green')
    
    def test_integration_with_model(self):
        """Проверяет интеграцию с моделью трафика."""
        light = TraditionalTrafficLight(duration_ns=2, duration_ew=2, yellow_duration=1)
        model = TrafficModel(arrival_prob=1.0)  # Все автомобили появляются
        
        # Добавляем автомобили в очередь
        for _ in range(3):
            model.step()
        
        # Сбрасываем текущее время модели для простоты тестирования
        model.current_time = 0
        
        # Фаза 0: N-S зеленый
        light.current_phase = 0
        light.phase_timer = 0
        light.update(model)
        
        # Проверяем, что автомобили были удалены из очередей N и S
        self.assertLess(len(model.queues['N']), 3)
        self.assertLess(len(model.queues['S']), 3)
        self.assertEqual(len(model.queues['E']), 3)
        self.assertEqual(len(model.queues['W']), 3)

class TestSmartTrafficLight(unittest.TestCase):
    """Тестирование класса SmartTrafficLight."""
    
    def test_adaptive_phase_duration(self):
        """Проверяет адаптивность длительности фаз."""
        model = TrafficModel(arrival_prob=0.0)  # Без новых автомобилей
        light = SmartTrafficLight(min_duration=10, max_duration=60)
        
        # Искусственно создаем длинную очередь в N-S
        for _ in range(10):
            model.queues['N'].append(Car(arrival_time=0, direction='N'))
            model.queues['S'].append(Car(arrival_time=0, direction='S'))
        
        # Фаза 0: NS
        light.current_direction = 'NS'
        light.phase_duration = 0
        
        # Вычисляем ожидаемую длительность
        expected_duration = light.get_current_phase_duration({
            'N': 10, 'S': 10, 'E': 0, 'W': 0
        })
        
        # Выполняем шаги до завершения фазы
        for _ in range(expected_duration):
            light.update(model)
        
        # Проверяем, что фаза завершена
        self.assertEqual(light.phase_duration, expected_duration)
    
    def test_response_to_load(self):
        """Проверяет реакцию на изменение нагрузки."""
        light = SmartTrafficLight(min_duration=10, max_duration=60)
        model = TrafficModel(arrival_prob=0.0)  # Без новых автомобилей
        
        # Создаем длинные очереди в разных направлениях
        heavy_queues = {
            'N': 15, 'S': 15, 'E': 5, 'W': 5  # N-S перегружен
        }
        
        light.calculate_priority(heavy_queues)
        
        # Проверяем, что N-S имеет приоритет
        priorities = light.calculate_priority(heavy_queues)
        self.assertGreater(priorities['NS'], priorities['EW'])
        
        # Изменяем нагрузку, теперь E-W перегружен
        heavy_queues = {
            'N': 5, 'S': 5, 'E': 15, 'W': 15
        }
        
        light.calculate_priority(heavy_queues)
        
        # Проверяем, что E-W имеет приоритет
        priorities = light.calculate_priority(heavy_queues)
        self.assertGreater(priorities['EW'], priorities['NS'])
    
    def test_superiority_over_traditional(self):
        """Проверяет преимущества перед традиционным алгоритмом."""
        # Тест в условиях неравномерной нагрузки
        ns_peak = {'N': 0.5, 'S': 0.5, 'E': 0.1, 'W': 0.1}  # Увеличена нагрузка на N-S

        # Запуск традиционного алгоритма
        traditional_result = run_experiment(
            algorithm='traditional',
            arrival_prob=ns_peak,
            duration=1000  # Увеличена длительность симуляции
        )

        # Запуск умного алгоритма
        smart_result = run_experiment(
            algorithm='smart',
            arrival_prob=ns_peak,
            duration=1000  # Увеличена длительность симуляции
        )

        # Проверяем, что умный алгоритм показывает меньшее среднее время ожидания
        self.assertLess(smart_result['avg_waiting'], traditional_result['avg_waiting'])

def run_tests():
    """
    Запускает все тесты и возвращает результат.
    
    Возвращает:
        bool: True, если все тесты пройдены успешно
    """
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Запуск тестов системы управления светофорами...")
    all_tests_passed = run_tests()
    
    if all_tests_passed:
        print("\nВсе тесты пройдены успешно!")
    else:
        print("\nНекоторые тесты не прошли.")