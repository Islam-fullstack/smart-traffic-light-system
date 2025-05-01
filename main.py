"""
main.py - Основной файл для запуска симуляции системы умных светофоров.

Примеры использования:
1. Базовый запуск с умным алгоритмом: python main.py
2. Традиционный алгоритм с визуализацией: python main.py -a traditional -v
3. Умный алгоритм в час пик: python main.py -p ns_peak -t 1000
4. Полное сравнение алгоритмов: python main.py --compare
"""

import argparse
import os
import pandas as pd

# Импорт классов из предыдущих файлов
from traffic_model import TrafficModel
from traditional_traffic_light import TraditionalTrafficLight
from smart_traffic_light import SmartTrafficLight
from visualization import TrafficVisualization
from comparison import run_experiment, compare_algorithms

def parse_arguments():
    """
    Обрабатывает аргументы командной строки.
    
    Возвращает:
        argparse.Namespace: Объект с обработанными аргументами
    """
    parser = argparse.ArgumentParser(description='Симуляция системы управления светофорами')
    parser.add_argument('-a', '--algorithm', 
                        choices=['traditional', 'smart'],
                        default='smart',
                        help='Выбор алгоритма управления светофорами')
    parser.add_argument('-t', '--simulation-time',
                        type=int,
                        default=500,
                        help='Длительность симуляции в шагах')
    parser.add_argument('-p', '--traffic-pattern',
                        choices=['uniform', 'ns_peak', 'ew_peak', 'high_load'],
                        default='uniform',
                        help='Шаблон трафика')
    parser.add_argument('-v', '--visualization',
                        action='store_true',
                        help='Включить визуализацию симуляции')
    parser.add_argument('-o', '--output',
                        default='results.csv',
                        help='Путь для сохранения результатов')
    parser.add_argument('--compare',
                        action='store_true',
                        help='Запустить полное сравнение алгоритмов')
    
    return parser.parse_args()

def configure_traffic_pattern(pattern):
    """
    Возвращает параметры интенсивности трафика для каждого направления.
    
    Параметры:
        pattern (str): Шаблон трафика
        
    Возвращает:
        dict: Вероятности появления автомобилей по направлениям
    """
    patterns = {
        'uniform': {'N': 0.2, 'S': 0.2, 'E': 0.2, 'W': 0.2},
        'ns_peak': {'N': 0.4, 'S': 0.4, 'E': 0.1, 'W': 0.1},
        'ew_peak': {'N': 0.1, 'S': 0.1, 'E': 0.4, 'W': 0.4},
        'high_load': {'N': 0.3, 'S': 0.3, 'E': 0.3, 'W': 0.3}
    }
    
    return patterns.get(pattern, patterns['uniform'])

def main():
    """
    Основная функция для запуска симуляции.
    """
    # Обработка аргументов командной строки
    args = parse_arguments()
    
    # Настройка шаблона трафика
    arrival_prob = configure_traffic_pattern(args.traffic_pattern)
    
    # Если указан флаг сравнения, запускаем сравнение алгоритмов
    if args.compare:
        print("Запуск полного сравнения алгоритмов...")
        df = compare_algorithms()
        
        # Сохранение и вывод результатов
        df.to_csv('comparison_results.csv', index=False)
        print("\nРезультаты сравнения алгоритмов:")
        print(df.groupby(['scenario', 'algorithm']).agg({
            'avg_waiting': 'mean',
            'cars_passed': 'sum'
        }))
        return
    
    # Создание модели трафика
    model = TrafficModel(arrival_prob=arrival_prob)
    
    # Создание контроллера светофоров
    if args.algorithm == 'traditional':
        controller = TraditionalTrafficLight(duration_ns=30, duration_ew=30, yellow_duration=5)
    else:
        controller = SmartTrafficLight(min_duration=10, max_duration=60)
    
    # Запуск визуализации, если указан флаг
    if args.visualization:
        print("Запуск симуляции с визуализацией...")
        viz = TrafficVisualization(model, controller)
        ani = viz.start_animation(frames=args.simulation_time)
        
        # Сохранение анимации, если указан путь
        if args.output.endswith('.mp4') or args.output.endswith('.gif'):
            print(f"Сохранение анимации в {args.output}...")
            writer = 'ffmpeg' if args.output.endswith('.mp4') else 'pillow'
            viz.save_animation(ani, filename=args.output, writer=writer)
    
    # Запуск симуляции без визуализации
    else:
        print("Запуск симуляции без визуализации...")
        result = run_experiment(
            algorithm=args.algorithm,
            arrival_prob=arrival_prob,
            duration=args.simulation_time
        )
        
        # Создание DataFrame и сохранение результатов
        df = pd.DataFrame([result])
        df.to_csv(args.output, index=False)
        
        # Вывод сводки результатов в консоль
        print("\nРезультаты симуляции:")
        print(f"Алгоритм: {result['algorithm']}")
        print(f"Сценарий: {args.traffic_pattern}")
        print(f"Среднее время ожидания: {result['avg_waiting']:.2f}")
        print(f"Максимальное время ожидания: {result['max_waiting']}")
        print(f"Количество пропущенных автомобилей: {result['cars_passed']}")
        print(f"Средняя длина очереди: {result['avg_queue_length']:.2f}")
        print(f"Процент времени с пустыми очередями: {result['empty_queue_percentage']:.2f}%")
        print(f"Результаты сохранены в {args.output}")

if __name__ == "__main__":
    main()