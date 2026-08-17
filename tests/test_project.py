import pytest
import mysql.connector
from fastapi.testclient import TestClient

from local_settings import dbconfig
from mysql_connector import (
    count_movies_by_genre_and_year,
    count_movies_by_year_range,
    count_movies_by_keyword,
    get_categories,
    get_year_range,
    search_by_genre_and_year,
    search_by_year_range,
    search_by_keyword,
)
from web_app import app


client = TestClient(app)


@pytest.fixture
def cursor():
    """Создаёт курсор для тестирования подключения к MySQL."""

    with mysql.connector.connect(**dbconfig) as connection:
        with connection.cursor() as cursor:
            yield cursor


def test_connection(cursor):
    """Проверяет подключение к MySQL."""

    cursor.execute("SELECT 1")
    result = cursor.fetchone()

    assert result == (1,)


def test_get_categories():
    """Проверяет получение жанров."""

    categories = get_categories()

    assert isinstance(categories, list)
    assert len(categories) > 0


def test_get_year_range():
    """Проверяет получение минимального и максимального года."""

    min_year, max_year = get_year_range()

    assert min_year <= max_year


def test_search_by_keyword():
    """Проверяет поиск по ключевому слову."""

    movies = search_by_keyword(
        "academy",
        limit=10,
        offset=0,
    )

    assert isinstance(movies, list)
    assert len(movies) > 0
    assert len(movies) <= 10


def test_keyword_pagination():
    """Проверяет, что пагинация возвращает следующую страницу."""

    first_page = search_by_keyword(
        "a",
        limit=10,
        offset=0,
    )

    second_page = search_by_keyword(
        "a",
        limit=10,
        offset=10,
    )

    assert len(first_page) == 10
    assert len(second_page) == 10
    assert first_page != second_page


def test_count_movies_by_keyword():
    """Проверяет подсчёт всех результатов поиска."""

    count = count_movies_by_keyword("a")

    assert isinstance(count, int)
    assert count > 10


def test_search_by_genre_and_year():
    """Проверяет поиск по жанру и диапазону годов."""

    movies = search_by_genre_and_year(
        1,
        1990,
        2026,
        limit=10,
        offset=0,
    )

    assert isinstance(movies, list)
    assert len(movies) > 0
    assert len(movies) <= 10


def test_count_movies_by_genre_and_year():
    """Проверяет общее количество фильмов по жанру."""

    count = count_movies_by_genre_and_year(
        1,
        1990,
        2026,
    )

    assert isinstance(count, int)
    assert count > 10


def test_home_page():
    """Проверяет запуск веб-интерфейса."""

    response = client.get("/")

    assert response.status_code == 200
    assert "Поиск фильмов" in response.text


def test_keyword_results_are_unique():
    """Проверяет, что один фильм не дублируется из-за нескольких жанров."""

    movies = search_by_keyword(
        "dino",
        limit=100,
        offset=0,
    )

    film_ids = [movie[0] for movie in movies]

    assert len(film_ids) == len(set(film_ids))


def test_keyword_count_matches_search():
    """Проверяет соответствие поиска и общего количества результатов."""

    movies = search_by_keyword(
        "dino",
        limit=100,
        offset=0,
    )

    count = count_movies_by_keyword("dino")

    assert len(movies) == count


def test_search_by_year_range():
    movies = search_by_year_range(
        start_year=2026,
        end_year=2026,
        limit=10,
        offset=0
    )

    assert isinstance(movies, list)

    for movie in movies:
        assert movie[2] == 2026


def test_count_movies_by_year_range():
    movies = search_by_year_range(
        start_year=2026,
        end_year=2026,
        limit=100,
        offset=0
    )

    count = count_movies_by_year_range(
        start_year=2026,
        end_year=2026
    )

    assert count == len(movies)