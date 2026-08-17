"""
Модуль для сохранения поисковых запросов в MongoDB.

Каждый поиск сохраняется как отдельный документ:
- время запроса;
- тип поиска;
- параметры поиска;
- общее количество найденных результатов.
"""

from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from local_settings import (
    MONGODB_URL_WRITE,
    MONGO_COLLECTION,
    MONGO_DATABASE,
)


def save_search(search_type, params, results_count):
    """
    Сохраняет поисковый запрос в MongoDB.

    Args:
        search_type (str): тип поиска.
            Например: "keyword" или "genre__years_range".
        params (dict): параметры поискового запроса.
        results_count (int): общее количество найденных фильмов.

    Returns:
        bool: True, если запись выполнена успешно,
        иначе False.
    """

    # Формируем документ, который будет записан в MongoDB
    search_log = {
        "timestamp": datetime.now(timezone.utc),
        "search_type": search_type,
        "params": params,
        "results_count": results_count,
    }

    try:
        # MongoClient создаёт подключение к серверу MongoDB
        with MongoClient(MONGODB_URL_WRITE) as client:
            database = client[MONGO_DATABASE]
            collection = database[MONGO_COLLECTION]

            # Каждый поиск сохраняется как новый документ
            collection.insert_one(search_log)

        return True

    except PyMongoError as error:
        print(f"Ошибка записи в MongoDB: {error}")
        return False

