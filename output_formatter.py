"""
Модуль для форматирования и вывода данных в консоль.

Содержит функции:
- вывода найденных фильмов;
- формирования описания поискового запроса;
- вывода последних запросов;
- вывода популярных запросов.
"""


def print_movies(movies):
    """
    Выводит найденные фильмы в консоль.

    Args:
        movies (list): список фильмов из MySQL.
    """

    if not movies:
        print("Фильмы не найдены.")
        return

    print()
    print("Результаты поиска:")

    for movie in movies:
        film_id, title, release_year, category_name, length = movie

        print(
            f"{film_id}: {title} | "
            f"{category_name} | "
            f"{release_year} | "
            f"{length} мин."
        )


def format_search_description(search_type, params):
    """
    Формирует понятное описание поискового запроса.

    Args:
        search_type (str): тип поиска.
        params (dict): параметры поиска.

    Returns:
        str: описание поискового запроса.
    """

    if search_type == "keyword":
        keyword = params.get("keyword", "")

        return f'Поиск по слову: "{keyword}"'

    if search_type in (
            "genre_year",
            "genre__years_range",
            "genre_years_range",
    ):
        genre = params.get("genre") or params.get("genre_name", "")

        if "years_range" in params:
            years = params.get("years_range", "")
        else:
            start_year = params.get("start_year", "")
            end_year = params.get("end_year", "")
            years = f"{start_year}–{end_year}"

        return f"Жанр: {genre}, годы: {years}"

    return "Неизвестный тип поиска"


def print_recent_searches(searches):
    """
    Выводит последние поисковые запросы.

    Args:
        searches (list): список запросов из MongoDB.
    """

    print()
    print("=" * 50)
    print("Последние поисковые запросы")
    print("=" * 50)

    if not searches:
        print("Поисковых запросов пока нет.")
        return

    for number, search in enumerate(searches, start=1):
        description = format_search_description(
            search_type=search["search_type"],
            params=search["params"],
        )

        timestamp = search["timestamp"]
        local_time = timestamp.astimezone()
        formatted_time = local_time.strftime(
            "%d.%m.%Y %H:%M"
        )

        results_count = search.get("results_count", 0)

        print(
            f"{number}. {description} | "
            f"Всего найдено: {results_count} | "
            f"{formatted_time}"
        )


def print_popular_searches(searches):
    """
    Выводит самые популярные поисковые запросы.

    Args:
        searches (list): результаты агрегации MongoDB.
    """

    print()
    print("=" * 50)
    print("Самые популярные поисковые запросы")
    print("=" * 50)

    if not searches:
        print("Статистики пока нет.")
        return

    for number, search in enumerate(searches, start=1):
        search_data = search["_id"]

        description = format_search_description(
            search_type=search_data["search_type"],
            params=search_data["params"],
        )

        search_count = search["search_count"]
        results_count = search.get("results_count", 0)
        last_used = search.get("last_used")

        if last_used:
            last_used = last_used.astimezone().strftime(
                "%d.%m.%Y %H:%M"
            )
        else:
            last_used = "Нет данных"

        print(
            f"{number}. {description} | "
            f"выполнен {search_count} раз(а) | "
            f"Всего найдено: {results_count} | "
            f"Последний поиск: {last_used}"
        )
