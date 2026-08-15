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

    pipeline = [
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

    pipeline = [
        {
            "$sort": {
                "timestamp": -1,
            }
        },
        {
            "$group": {
                "_id": {
                    "search_type": "$search_type",
                    "params": "$params",
                },
                "search_count": {
                    "$sum": 1,
                },
                "results_count": {
                    "$first": "$results_count",
                },
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