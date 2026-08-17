"""
Модуль для получения статистики поисковых запросов из MongoDB.

Содержит функции:
- получения последних поисковых запросов;
- получения самых популярных поисковых запросов.
"""

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from local_settings import (
    MONGODB_URL_WRITE,
    MONGO_COLLECTION,
    MONGO_DATABASE,
)


def get_collection(client):
    """
    Возвращает коллекцию с поисковыми запросами.

    Args:
        client (MongoClient): подключение к MongoDB.

    Returns:
        Collection: коллекция поисковых запросов.
    """

    database = client[MONGO_DATABASE]
    return database[MONGO_COLLECTION]


def get_recent_searches(limit=5):
    """
    Получает 5 последних уникальных поисковых запросов.
    """

    # Группируем одинаковые запросы по типу поиска и параметрам.
    # Для каждой группы оставляем только самый последний запрос,
    # затем выбираем 5 последних уникальных запросов.
    pipeline = [
        # Разделяем документы на группы одинаковых запросов
        # и присваиваем им ранг по времени.
        {
            "$setWindowFields": {
                "partitionBy": {
                    "search_type": "$search_type",
                    "params": "$params",
                },
                "sortBy": {
                    "timestamp": -1,
                },
                "output": {
                    "rank": {
                        "$rank": {},
                    }
                },
            }
        },
        # Оставляем только последний документ каждой группы.
        {
            "$match": {
                "rank": 1,
            }
        },
        {
            "$sort": {
                "timestamp": -1,
            }
        },
        {
            "$limit": limit,
        },
        {
            "$project": {
                "_id": 0,
                "search_type": 1,
                "params": 1,
                "timestamp": 1,
                "results_count": 1,
            }
        },
    ]

    try:
        with MongoClient(
            MONGODB_URL_WRITE,
            tz_aware=True,
        ) as client:
            collection = get_collection(client)

            searches = collection.aggregate(pipeline)

            return list(searches)

    except PyMongoError as error:
        print(
            f"Ошибка получения последних запросов: {error}"
        )
        return []


def get_popular_searches(limit=5):
    """
    Получает самые популярные поисковые запросы.

    Одинаковые запросы объединяются в одну группу.
    Для каждой группы подсчитывается количество повторений.

    Args:
        limit (int): максимальное количество запросов.

    Returns:
        list: список популярных поисковых запросов.
    """

    # Сначала сортируем запросы от новых к старым.
    # Затем объединяем одинаковые запросы и считаем,
    # сколько раз выполнялся каждый из них.
    pipeline = [
        # Сортировка нужна, чтобы $first ниже получил
        # данные именно последнего выполнения запроса.
        {
            "$sort": {
                "timestamp": -1,
            }
        },
        # Группируем одинаковые поисковые запросы.
        {
            "$group": {
                "_id": {
                    "search_type": "$search_type",
                    "params": "$params",
                },
                "search_count": {
                    "$sum": 1,
                },
                # Берём количество результатов
                # из последнего выполнения запроса.
                "results_count": {
                    "$first": "$results_count",
                },
                # Сохраняем дату последнего использования запроса.
                "last_used": {
                    "$first": "$timestamp",
                },
            }
        },
        {
            "$sort": {
                "search_count": -1,
                "last_used": -1,
            }
        },
        {
            "$limit": limit,
        },
    ]

    try:
        with MongoClient(
            MONGODB_URL_WRITE,
            tz_aware=True,
        ) as client:
            collection = get_collection(client)

            searches = collection.aggregate(pipeline)

            return list(searches)

    except PyMongoError as error:
        print(f"Ошибка получения популярных запросов: {error}")
        return []