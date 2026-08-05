"""
Главный модуль консольного приложения для поиска фильмов.

Здесь находятся:
- главное меню;
- обработка выбора пользователя;
- запуск функций поиска.
"""

import mysql.connector

from output_formatter import (
    print_movies,
    print_popular_searches,
    print_recent_searches,
)
from log_stats import get_popular_searches, get_recent_searches
from log_writer import save_search
from mysql_connector import (
    get_categories,
    get_year_range,
    search_by_genre_and_year,
    search_by_keyword,
)


def show_main_menu():
    """Выводит главное меню приложения."""

    print()
    print("=" * 40)
    print("Поиск фильмов в базе Sakila")
    print("=" * 40)
    print("1. Поиск по ключевому слову")
    print("2. Поиск по жанру и диапазону годов")
    print("3. Статистика поисковых запросов")
    print("0. Выход")
    print("=" * 40)

def handle_keyword_search():
    """Обрабатывает поиск фильмов по ключевому слову."""

    keyword = input(
        "Введите слово или часть названия фильма: "
    ).strip()

    if not keyword:
        print("Ключевое слово не может быть пустым.")
        return

    offset = 0
    limit = 10

    # Считаем, сколько фильмов было показано пользователю
    total_results = 0

    while True:
        movies = search_by_keyword(
            keyword,
            limit=limit,
            offset=offset,
        )

        # Проверяем, вернул ли запрос фильмы
        if not movies:
            if offset == 0:
                print("Фильмы не найдены.")
            else:
                print("Больше результатов нет.")
            break

        # Показываем текущую страницу
        print_movies(movies)

        # Добавляем количество показанных фильмов
        total_results += len(movies)

        # Если найдено меньше 10 фильмов,
        # следующей страницы быть не может
        if len(movies) < limit:
            print("Это все результаты.")
            break

        choice = input(
            "Показать следующие 10 результатов? (y/n): "
        ).strip().lower()

        if choice != "y":
            break

        # Переходим к следующей странице
        offset += limit

    # Записываем поиск в MongoDB один раз,
    # когда пользователь закончил просмотр результатов
    save_search(
        search_type="keyword",
        params={
            "keyword": keyword,
        },
        results_count=total_results,
    )

def handle_genre_year_search():
    """Обрабатывает поиск фильмов по жанру и диапазону годов."""

    # Получаем доступные жанры и диапазон годов из MySQL
    categories = get_categories()
    min_year, max_year = get_year_range()

    print("\nДоступные жанры:")
    for category_id, category_name in categories:
        print(f"{category_id}. {category_name}")

    print(f"\nДоступный диапазон годов: {min_year}–{max_year}")

    try:
        genre_id = int(input("Введите номер жанра: ").strip())
        start_year = int(input("Введите начальный год: ").strip())
        end_year = int(input("Введите конечный год: ").strip())

    except ValueError:
        print("Ошибка: необходимо вводить целые числа.")
        return

    valid_genre_ids = [
        category_id
        for category_id, category_name in categories
    ]

    if genre_id not in valid_genre_ids:
        print("Жанра с таким номером нет.")
        return

    if not min_year <= start_year <= max_year:
        print(
            f"Начальный год должен быть "
            f"от {min_year} до {max_year}."
        )
        return

    if not min_year <= end_year <= max_year:
        print(
            f"Конечный год должен быть "
            f"от {min_year} до {max_year}."
        )
        return

    if start_year > end_year:
        print("Начальный год не может быть больше конечного.")
        return

    limit = 10
    offset = 0
    total_results = 0

    while True:
        movies = search_by_genre_and_year(
            genre_id=genre_id,
            start_year=start_year,
            end_year=end_year,
            limit=limit,
            offset=offset,
        )

        # Если фильмы не найдены
        if not movies:
            if offset == 0:
                print("Фильмы не найдены.")
            else:
                print("Больше результатов нет.")
            break

        # Показываем найденные фильмы
        print_movies(movies)

        # Считаем фильмы, которые были показаны пользователю
        total_results += len(movies)

        # Если получено меньше 10 фильмов,
        # следующей страницы точно нет
        if len(movies) < limit:
            print("Это все результаты.")
            break

        choice = input(
            "Показать следующие 10 результатов? (y/n): "
        ).strip().lower()

        if choice != "y":
            break

        # Переходим к следующей странице
        offset += limit

    genre_name = next(
        category_name
        for category_id, category_name in categories
        if category_id == genre_id
    )

    save_search(
        search_type="genre_year",
        params={
            "genre_id": genre_id,
            "genre_name": genre_name,
            "start_year": start_year,
            "end_year": end_year,
        },
        results_count=total_results,
    )

def show_search_statistics():
    """Получает и выводит статистику поисковых запросов."""

    recent_searches = get_recent_searches()
    popular_searches = get_popular_searches()

    print_recent_searches(recent_searches)
    print_popular_searches(popular_searches)

def main():
    """Запускает главное меню приложения."""

    while True:
        show_main_menu()

        choice = input("Выберите пункт меню: ").strip()

        try:
            if choice == "1":
                handle_keyword_search()

            elif choice == "2":
                handle_genre_year_search()

            elif choice == "3":
                show_search_statistics()

            elif choice == "0":
                print("Программа завершена.")
                break

            else:
                print("Неверный выбор. Введите 0, 1, 2 или 3.")

        except mysql.connector.Error as error:
            print(f"Ошибка работы с MySQL: {error}")

if __name__ == "__main__":
    main()
