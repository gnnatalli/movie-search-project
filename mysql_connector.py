"""
Модуль для работы с базой данных MySQL (sakila).

Здесь находятся функции:
- подключение к базе;
- поиск фильмов;
- получение жанров.
"""

import mysql.connector
from local_settings import dbconfig


def get_connection():
    """
    Создает подключение к базе MySQL.
    """
    return mysql.connector.connect(**dbconfig)


def get_categories():
    """
    Получает список всех жанров из базы sakila.

    Returns:
        list: список жанров (id, название)
    """

    connection = get_connection()
    cursor = connection.cursor()

    # SQL-запрос для получения жанров
    query = """
        SELECT category_id, name
        FROM category
        ORDER BY name;
    """

    cursor.execute(query)

    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return categories


def get_year_range():
    """
    Получает минимальный и максимальный год выпуска фильмов.

    Returns:
        tuple: минимальный и максимальный год.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # SQL-запрос для определения диапазона годов в базе
    query = """
        SELECT
            MIN(release_year),
            MAX(release_year)
        FROM film;
    """

    cursor.execute(query)

    year_range = cursor.fetchone()

    cursor.close()
    connection.close()

    return year_range


def search_by_keyword(keyword, limit=10, offset=0):
    """
    Ищет фильмы по ключевому слову в названии.

    Args:
        keyword (str): слово или часть названия фильма.
        limit (int): количество результатов на одной странице.
        offset (int): количество пропущенных результатов.

    Returns:
        list: найденные фильмы.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Ищем ключевое слово во всём названии фильма.
    # LEFT JOIN позволяет получить жанры фильма.
    # GROUP_CONCAT объединяет несколько жанров в одну строку,
    # поэтому один фильм не дублируется в результатах.
    query = """
            SELECT f.film_id, 
                   f.title, 
                   f.release_year, 
                   GROUP_CONCAT( 
                       DISTINCT c.name
                ORDER BY c.name
                SEPARATOR ', '
            ) AS genres, 
                   f.length
            FROM film AS f
                     LEFT JOIN film_category AS fc
                               ON f.film_id = fc.film_id
                     LEFT JOIN category AS c
                               ON fc.category_id = c.category_id
            WHERE LOWER(f.title) LIKE %s
            GROUP BY f.film_id, 
                     f.title, 
                     f.release_year, 
                     f.length
            ORDER BY f.title
                LIMIT %s 
            OFFSET %s; 
            """


    # %keyword% позволяет найти слово в любой части названия.
    # limit ограничивает количество результатов,
    # offset используется для пагинации.
    cursor.execute(
        query,
        (f"%{keyword.lower()}%", limit, offset),
    )

    films = cursor.fetchall()

    cursor.close()
    connection.close()

    return films


def search_by_genre_and_year(
        genre_id,
        start_year,
        end_year,
        limit=10,
        offset=0
):
    """
    Ищет фильмы по жанру и диапазону годов.

    Args:
        genre_id (int): идентификатор жанра.
        start_year (int): начальный год.
        end_year (int): конечный год.
        limit (int): максимальное количество результатов.
        offset (int): количество пропускаемых результатов.

    Returns:
        list: список найденных фильмов.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Соединяем фильмы с таблицей категорий
    # и фильтруем одновременно по жанру и диапазону годов.
    query = """
        SELECT
            f.film_id,
            f.title,
            f.release_year,
            c.name,
            f.length
        FROM film AS f
        JOIN film_category AS fc
            ON f.film_id = fc.film_id
        JOIN category AS c
            ON fc.category_id = c.category_id
        WHERE c.category_id = %s
          AND f.release_year BETWEEN %s AND %s
        ORDER BY f.title
        LIMIT %s OFFSET %s;
    """

    # BETWEEN включает начальный и конечный год.
    # LIMIT и OFFSET используются для постраничного вывода.
    cursor.execute(
        query,
        (
            genre_id,
            start_year,
            end_year,
            limit,
            offset
        )
    )

    films = cursor.fetchall()

    cursor.close()
    connection.close()

    return films


def count_movies_by_keyword(keyword):
    """
    Возвращает общее количество фильмов,
    найденных по ключевому слову.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Отдельный COUNT нужен, чтобы узнать общее количество
    # найденных фильмов независимо от текущей страницы.
    query = """
        SELECT COUNT(*)
        FROM film
        WHERE LOWER(title) LIKE %s;
    """

    cursor.execute(
        query,
        (f"%{keyword.lower()}%",),
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0]


def count_movies_by_genre_and_year(
        genre_id,
        start_year,
        end_year
):
    """
    Возвращает общее количество фильмов
    по жанру и диапазону годов.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # DISTINCT гарантирует, что каждый фильм
    # учитывается в общем количестве только один раз.
    query = """
        SELECT COUNT(DISTINCT f.film_id)
        FROM film AS f
        JOIN film_category AS fc
            ON f.film_id = fc.film_id
        WHERE fc.category_id = %s
          AND f.release_year BETWEEN %s AND %s;
    """

    cursor.execute(
        query,
        (
            genre_id,
            start_year,
            end_year,
        )
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0]


def get_film_by_id(film_id):
    """Возвращает подробную информацию о фильме по его ID."""

    connection = get_connection()
    # Buffered cursor полностью считывает результат запроса
    # и предотвращает ошибку "Unread result found".
    cursor = connection.cursor(buffered=True)

    # Получаем подробную информацию для страницы фильма.
    # LEFT JOIN позволяет получить фильм даже в том случае,
    # если для него не указан жанр.
    # COALESCE заменяет отсутствующий жанр текстом "Без жанра".
    query = """
            SELECT f.film_id, 
                   f.title, 
                   f.description, 
                   f.release_year, 
                   COALESCE( 
                           GROUP_CONCAT( 
                               DISTINCT c.name
                    ORDER BY c.name
                    SEPARATOR ', '
                ), 
                           'Без жанра' 
                   ) AS genres, 
                   f.rental_duration, 
                   f.rental_rate, 
                   f.length, 
                   f.replacement_cost, 
                   f.rating
            FROM film AS f
                     LEFT JOIN film_category AS fc
                               ON f.film_id = fc.film_id
                     LEFT JOIN category AS c
                               ON fc.category_id = c.category_id
            WHERE f.film_id = %s
            GROUP BY f.film_id, 
                     f.title, 
                     f.description, 
                     f.release_year, 
                     f.rental_duration, 
                     f.rental_rate, 
                     f.length, 
                     f.replacement_cost, 
                     f.rating LIMIT 1; 
            """

    cursor.execute(query, (film_id,))
    film = cursor.fetchone()

    cursor.close()
    connection.close()

    return film


def search_by_year_range(
        start_year,
        end_year,
        limit=10,
        offset=0
):
    """
    Ищет фильмы по диапазону годов без ограничения по жанру.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Поиск только по диапазону годов без выбора жанра.
    # Эта функция используется для "Все фильмы",
    # "Фильмы последнего года" и варианта "Все жанры".
    query = """
        SELECT
            f.film_id,
            f.title,
            f.release_year,
        COALESCE(
            GROUP_CONCAT(
                DISTINCT c.name
                ORDER BY c.name
                SEPARATOR ', '
            ),
            'Без жанра'
        ) AS genres,
        f.length
        FROM film AS f
        LEFT JOIN film_category AS fc
            ON f.film_id = fc.film_id
        LEFT JOIN category AS c
            ON fc.category_id = c.category_id
        WHERE f.release_year BETWEEN %s AND %s
        GROUP BY
            f.film_id,
            f.title,
            f.release_year,
            f.length
        ORDER BY f.title
        LIMIT %s OFFSET %s;
    """

    cursor.execute(
        query,
        (
            start_year,
            end_year,
            limit,
            offset,
        )
    )

    films = cursor.fetchall()

    cursor.close()
    connection.close()

    return films


def count_movies_by_year_range(start_year, end_year):
    """
    Возвращает количество фильмов
    в заданном диапазоне годов.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Получаем общее количество фильмов в диапазоне годов.
    # Это значение используется для статистики и пагинации.
    query = """
        SELECT COUNT(*)
        FROM film
        WHERE release_year BETWEEN %s AND %s;
    """

    cursor.execute(
        query,
        (
            start_year,
            end_year,
        )
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0]
