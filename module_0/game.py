"""
Module 0 final task.
"""
import numpy as np

LEFT = 1  # left border of the range
RIGHT = 100  # right border of the range


def generate_predict(left, right):
    """
    Returns the center point of the interval [left, right].
    :param left: left border of the interval
    :param right: right border of the interval
    :return: the center point of the interval
    """
    return (left + right) // 2


def game_core_v3(number):
    """
    Functions guess the number using dichotomy and returns count of used tries.
    :param number: number to guess
    :return: count of the tries
    """
    count = 1
    left = LEFT - 1
    right = RIGHT + 1

    predict = generate_predict(left, right)
    while number != predict:
        count += 1
        if number > predict:
            left = predict
        elif number < predict:
            right = predict

        predict = generate_predict(left, right)
    return count


def score_game(game_core):
    """
    Takes function with game implementation and collects statistical meaningful
    information about implementation quality - mean amount of tries to guess random number.
    :param game_core: implementation (int)->int
    :return: mean amount of tries
    """
    count_ls = []
    np.random.seed(1)
    random_array = np.random.randint(LEFT, RIGHT + 1, size=1000)
    for number in random_array:
        count_ls.append(game_core(number))
    return int(np.mean(count_ls))


if __name__ == "__main__":
    print(f"Ваш алгоритм угадывает число в среднем за {score_game(game_core_v3)} попыток")
