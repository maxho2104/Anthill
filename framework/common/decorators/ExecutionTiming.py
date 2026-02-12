import time
import functools


def exec_timing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        # Получаем имя функции
        func_name = func.__name__

        # Проверяем, является ли функция методом класса
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
        else:
            class_name = "нет"

        # Выполняем функцию
        result = func(*args, **kwargs)

        # Вычисляем время выполнения
        end_time = time.time()
        execution_time = end_time - start_time

        # Выводим информацию
        print(f"Класс: {class_name}")
        print(f"Функция: {func_name}")
        print(f"Аргументы: args={args}, kwargs={kwargs}")
        print(f"Время выполнения: {execution_time:.6f} с.")

        return result

    return wrapper