import pytest
import mysql.connector
from fastapi.testclient import TestClient

from local_settings import dbconfig
from mysql_connector import (
    count_movies_by_genre_and_year,
    count_movies_by_keyword,
    get_categories,
    get_year_range,
    search_by_genre_and_year,
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