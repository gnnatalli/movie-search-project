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

    query = """
        SELECT
            film_id,
            title,
            release_year
        FROM film
        WHERE title LIKE %s
        ORDER BY title
        LIMIT %s OFFSET %s;
    """

    search_value = f"%{keyword}%"

    cursor.execute(
        query,
        (search_value, limit, offset)
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

    query = """
        SELECT
            f.film_id,
            f.title,
            f.release_year,
            c.name
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

