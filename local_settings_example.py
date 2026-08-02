"""
Пример настроек подключения к базам данных.

Для запуска проекта необходимо:
1. Скопировать этот файл.
2. Переименовать копию в local_settings.py.
3. Заполнить собственные данные подключения.
"""


# Настройки подключения к MySQL
dbconfig = {
    "host": "mysql_host",
    "port": 3306,
    "user": "mysql_user",
    "password": "mysql_password",
    "database": "sakila",
}


# Адрес подключения к MongoDB с правами записи
MONGODB_URL_WRITE = (
    "mongodb://username:password@mongodb_host:port/"
)


# База и коллекция для логирования поисковых запросов
MONGO_DATABASE = "ich_edit"

MONGO_COLLECTION = (
    "final_project_060326_ptm_Nataliia_Honchar"
)