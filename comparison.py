"""
comparison.py - Сравнение традиционного и умного алгоритмов управления светофорами.

Этот модуль реализует функции для проведения экспериментов, анализа результатов
и визуализации производительности двух алгоритмов управления светофорами.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from traffic_model import TrafficModel, Car
from traditional_traffic_light import TraditionalTrafficLight
from smart_traffic_light import SmartTrafficLight

def run_experiment(algorithm='traditional', arrival_prob=0.2, duration=300):
    """
    Запускает симуляцию без визуализации и собирает метрики производительности.
    
    Параметры:
        algorithm (str): 'traditional' или 'smart'
        arrival_prob (float or dict): Вероятность появления автомобиля
        duration (int): Длительность симуляции в временных шагах
    
    Возвращает:
        dict: Словарь с метриками производительности
    """
    # Создание модели трафика
    model = TrafficModel(arrival_prob=arrival_prob)
    
    # Создание контроллера светофоров
    if algorithm == 'traditional':
        controller = TraditionalTrafficLight(duration_ns=30, duration_ew=30, yellow_duration=5)
    elif algorithm == 'smart':
        controller = SmartTrafficLight(min_duration=10, max_duration=60)
    else:
        raise ValueError("Неизвестный алгоритм. Используйте 'traditional' или 'smart'")
    
    # Список для хранения истории длин очередей
    queue_history = []
    
    # Запуск симуляции
    for _ in range(duration):
        model.step()
        controller.update(model)
        
        # Сохранение текущих длин очередей
        current_queues = {direction: len(model.queues[direction]) for direction in ['N', 'S', 'E', 'W']}
        queue_history.append(current_queues)
    
    # Расчет метрик
    waiting_times = controller.waiting_times if hasattr(controller, 'waiting_times') else []
    
    # Среднее время ожидания
    avg_waiting = np.mean(waiting_times) if waiting_times else 0
    
    # Максимальное время ожидания
    max_waiting = np.max(waiting_times) if waiting_times else 0
    
    # Количество пропущенных автомобилей
    cars_passed = controller.total_cars_passed if hasattr(controller, 'total_cars_passed') else 0
    
    # Средняя длина очереди (по всем направлениям и временным шагам)
    avg_queue_length = np.mean([sum(step.values()) for step in queue_history])
    
    # Процент времени с пустыми очередями
    empty_queue_steps = sum(1 for step in queue_history if sum(step.values()) == 0)
    empty_queue_percentage = (empty_queue_steps / duration) * 100
    
    return {
        'algorithm': algorithm,
        'avg_waiting': avg_waiting,
        'max_waiting': max_waiting,
        'cars_passed': cars_passed,
        'avg_queue_length': avg_queue_length,
        'empty_queue_percentage': empty_queue_percentage,
        'queue_history': queue_history
    }

def compare_algorithms():
    """
    Проводит эксперименты с разными сценариями нагрузки и алгоритмами управления светофорами.
    
    Возвращает:
        pd.DataFrame: Результаты экспериментов
    """
    # Определение сценариев нагрузки
    scenarios = {
        'uniform': {'N': 0.2, 'S': 0.2, 'E': 0.2, 'W': 0.2},
        'peak_ns': {'N': 0.4, 'S': 0.4, 'E': 0.1, 'W': 0.1},
        'peak_ew': {'N': 0.1, 'S': 0.1, 'E': 0.4, 'W': 0.4},
        'high_load': {'N': 0.3, 'S': 0.3, 'E': 0.3, 'W': 0.3}
    }
    
    results = []
    
    # Проведение экспериментов
    for scenario_name, scenario_prob in scenarios.items():
        print(f"Сценарий: {scenario_name}")
        
        # Традиционный алгоритм
        print("  Запуск традиционного алгоритма...")
        traditional_result = run_experiment(
            algorithm='traditional',
            arrival_prob=scenario_prob,
            duration=300
        )
        traditional_result['scenario'] = scenario_name
        results.append(traditional_result)
        
        # Умный алгоритм
        print("  Запуск умного алгоритма...")
        smart_result = run_experiment(
            algorithm='smart',
            arrival_prob=scenario_prob,
            duration=300
        )
        smart_result['scenario'] = scenario_name
        results.append(smart_result)
    
    # Создание DataFrame
    df = pd.DataFrame(results)
    
    # Сохранение результатов в CSV
    os.makedirs('plots', exist_ok=True)
    df.to_csv('comparison_results.csv', index=False)
    
    return df

def plot_results(df):
    """
    Создает сравнительные графики на основе результатов экспериментов.
    
    Параметры:
        df (pd.DataFrame): DataFrame с результатами
    """
    # Столбчатые диаграммы для сравнения среднего времени ожидания
    plt.figure(figsize=(12, 6))
    bar_data = df.pivot(index='scenario', columns='algorithm', values='avg_waiting')
    bar_data.plot(kind='bar', title='Среднее время ожидания по сценариям')
    plt.xlabel('Сценарий')
    plt.ylabel('Среднее время ожидания')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('plots/avg_waiting_comparison.png')
    plt.close()
    
    # Линейные графики изменения длины очередей со временем
    scenarios = df['scenario'].unique()
    
    for scenario in scenarios:
        scenario_data = df[df['scenario'] == scenario]
        fig, axs = plt.subplots(2, 1, figsize=(12, 10))
        
        # Получение истории очередей
        traditional_queues = scenario_data[scenario_data['algorithm'] == 'traditional']['queue_history'].iloc[0]
        smart_queues = scenario_data[scenario_data['algorithm'] == 'smart']['queue_history'].iloc[0]
        
        # Преобразование в массивы
        traditional_array = np.array([[q for q in step.values()] for step in traditional_queues])
        smart_array = np.array([[q for q in step.values()] for step in smart_queues])
        
        # Построение графиков
        steps = range(len(traditional_array))
        
        axs[0].plot(steps, np.sum(traditional_array, axis=1), label='Традиционный')
        axs[0].plot(steps, np.sum(smart_array, axis=1), label='Умный')
        axs[0].set_title(f'Изменение общей длины очередей - {scenario}')
        axs[0].set_xlabel('Временной шаг')
        axs[0].set_ylabel('Общая длина очереди')
        axs[0].legend()
        
        axs[1].plot(steps, traditional_array[:, 0], label='Традиционный N')
        axs[1].plot(steps, smart_array[:, 0], label='Умный N')
        axs[1].plot(steps, traditional_array[:, 1], label='Традиционный S')
        axs[1].plot(steps, smart_array[:, 1], label='Умный S')
        axs[1].set_title(f'Изменение очереди N/S - {scenario}')
        axs[1].set_xlabel('Временной шаг')
        axs[1].set_ylabel('Длина очереди')
        axs[1].legend()
        
        plt.tight_layout()
        plt.savefig(f'plots/queue_trend_{scenario}.png')
        plt.close()
    
    # Тепловые карты эффективности алгоритмов при разных нагрузках
    metrics = ['avg_waiting', 'cars_passed', 'avg_queue_length', 'empty_queue_percentage']
    
    for metric in metrics:
        pivot_table = df.pivot(index='algorithm', columns='scenario', values=metric)
        plt.figure(figsize=(10, 6))
        plt.title(f'Тепловая карта: {metric}')
        plt.imshow(pivot_table, cmap='YlOrRd', aspect='auto')
        
        # Добавление значений в ячейки
        for i in range(pivot_table.shape[0]):
            for j in range(pivot_table.shape[1]):
                plt.text(j, i, f"{pivot_table.iloc[i, j]:.2f}", ha='center', va='center')
        
        plt.xticks(range(len(pivot_table.columns)), pivot_table.columns)
        plt.yticks(range(len(pivot_table.index)), pivot_table.index)
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(f'plots/heatmap_{metric}.png')
        plt.close()

def main():
    """
    Основная функция для запуска полного сравнения алгоритмов.
    """
    print("Запуск сравнения алгоритмов управления светофорами...")
    
    # Проведение экспериментов
    df = compare_algorithms()
    
    # Визуализация результатов
    print("Создание графиков...")
    plot_results(df)
    
    print("Сравнение завершено. Результаты сохранены в каталог 'plots'.")

if __name__ == "__main__":
    main()