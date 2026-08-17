"""
Веб-интерфейс приложения для поиска фильмов.
"""

from typing import Annotated

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from log_stats import get_popular_searches, get_recent_searches
from log_writer import save_search
from mysql_connector import (
    count_movies_by_genre_and_year,
    count_movies_by_keyword,
    count_movies_by_year_range,
    get_categories,
    get_film_by_id,
    get_year_range,
    search_by_genre_and_year,
    search_by_keyword,
    search_by_year_range,

)


app = FastAPI(
    title="Movie Search",
    description="Поиск фильмов в базе Sakila",
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

templates = Jinja2Templates(directory="templates")


def describe_search(search_type, params):
    """Создаёт понятное описание поискового запроса."""

    if search_type == "keyword":
        return f"Ключевое слово: {params.get('keyword', '')}"

    if search_type in ("genre_year", "genre__years_range"):
        genre = params.get("genre") or params.get("genre_name", "")

        if "years_range" in params:
            years = params.get("years_range", "")
        else:
            start_year = params.get("start_year", "")
            end_year = params.get("end_year", "")
            years = f"{start_year}–{end_year}"

        return f"Жанр: {genre}, годы: {years}"

    return "Неизвестный тип поиска"


def format_timestamp(timestamp):
    """Форматирует дату и время для HTML-страницы."""

    if timestamp is None:
        return "—"

    return timestamp.astimezone().strftime("%d.%m.%Y %H:%M")

def add_statistics_to_context(context):
    """Добавляет актуальную статистику запросов в context."""

    recent_searches = get_recent_searches()
    popular_searches = get_popular_searches()

    recent_rows = []

    for search in recent_searches:
        recent_rows.append(
            {
                "description": describe_search(
                    search.get("search_type"),
                    search.get("params", {}),
                ),
                "results_count": search.get("results_count", 0),
                "timestamp": format_timestamp(
                    search.get("timestamp")
                ),
            }
        )

    popular_rows = []

    for search in popular_searches:
        search_data = search.get("_id", {})

        popular_rows.append(
            {
                "description": describe_search(
                    search_data.get("search_type"),
                    search_data.get("params", {}),
                ),
                "count": search.get("search_count", 0),
                "results_count": search.get("results_count", 0),
                "timestamp": format_timestamp(
                    search.get("last_used")
                ),
            }
        )

    context["recent_searches"] = recent_rows
    context["popular_searches"] = popular_rows

def get_page_context():
    """Возвращает общие данные для главной страницы."""

    categories = get_categories()
    min_year, max_year = get_year_range()
    recent_searches = get_recent_searches()
    popular_searches = get_popular_searches()

    recent_rows = []

    for search in recent_searches:
        recent_rows.append(
            {
                "description": describe_search(
                    search.get("search_type"),
                    search.get("params", {}),
                ),
                "results_count": search.get("results_count", 0),
                "timestamp": format_timestamp(
                    search.get("timestamp")
                ),
            }
        )

    popular_rows = []

    for search in popular_searches:
        search_data = search.get("_id", {})

        popular_rows.append(
            {
                "description": describe_search(
                    search_data.get("search_type"),
                    search_data.get("params", {}),
                ),
                "count": search.get("search_count", 0),
            }
        )

    return {
        "page_title": "Поиск фильмов",
        "categories": categories,
        "min_year": min_year,
        "max_year": max_year,
        "movies": None,
        "message": None,
        "keyword": "",
        "selected_genre_id": "",
        "start_year": min_year,
        "end_year": max_year,
        "offset": 0,
        "has_previous": False,
        "has_next": False,
        "previous_offset": 0,
        "next_offset": 10,
        "pagination_type": None,
        "recent_searches": recent_rows,
        "popular_searches": popular_rows,
    }


@app.get("/", response_class=HTMLResponse)
def show_home_page(request: Request):
    """Показывает главную страницу сайта."""

    context = get_page_context()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )


@app.post("/search/keyword", response_class=HTMLResponse)
def search_keyword(
    request: Request,
    keyword: Annotated[str, Form()],
    offset: Annotated[int, Form()] = 0,
    log_search: Annotated[str, Form()] = "",
):
    """Ищет фильмы по ключевому слову."""

    context = get_page_context()
    keyword = keyword.strip().lower()

    if offset < 0:
        offset = 0

    context["keyword"] = keyword

    if not keyword:
        context["message"] = "Введите ключевое слово."

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=context,
        )

    limit = 10

    movies_with_extra = search_by_keyword(
        keyword,
        limit=limit + 1,
        offset=offset,
    )

    movies = movies_with_extra[:limit]
    has_next = len(movies_with_extra) > limit

    total_results = count_movies_by_keyword(keyword)

    if log_search == "1":
        save_search(
            search_type="keyword",
            params={"keyword": keyword},
            results_count=total_results,
        )

    add_statistics_to_context(context)

    context["movies"] = movies
    context["offset"] = offset
    context["has_previous"] = offset > 0
    context["has_next"] = has_next
    context["previous_offset"] = max(0, offset - limit)
    context["next_offset"] = offset + limit
    context["pagination_type"] = "keyword"

    if movies:
        page_number = offset // limit + 1

        context["message"] = (
            f"Страница {page_number}. "
            f"Показано результатов: {len(movies)}"
        )
    elif offset == 0:
        context["message"] = "Фильмы не найдены."
    else:
        context["message"] = "Больше фильмов нет."

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )

@app.post("/search/genre", response_class=HTMLResponse)
def search_genre(
    request: Request,
    genre_id: Annotated[int, Form()],
    start_year: Annotated[int, Form()],
    end_year: Annotated[int, Form()],
    offset: Annotated[int, Form()] = 0,
    log_search: Annotated[str, Form()] = "",
):
    """Ищет фильмы по жанру и диапазону годов."""

    context = get_page_context()

    if offset < 0:
        offset = 0

    context["selected_genre_id"] = genre_id
    context["start_year"] = start_year
    context["end_year"] = end_year

    categories = {
        category_id: category_name
        for category_id, category_name in context["categories"]
    }

    # 0 означает "Все жанры"
    if genre_id != 0 and genre_id not in categories:
        context["message"] = "Выберите существующий жанр."

    elif start_year > end_year:
        context["message"] = (
            "Начальный год не может быть больше конечного."
        )

    elif (
        start_year < context["min_year"]
        or end_year > context["max_year"]
    ):
        context["message"] = (
            f"Введите годы от {context['min_year']} "
            f"до {context['max_year']}."
        )

    else:
        limit = 10

        # Поиск без ограничения по жанру
        if genre_id == 0:
            genre_name = "Все жанры"

            movies_with_extra = search_by_year_range(
                start_year,
                end_year,
                limit=limit + 1,
                offset=offset,
            )

            total_results = count_movies_by_year_range(
                start_year,
                end_year,
            )

        # Обычный поиск по конкретному жанру
        else:
            genre_name = categories[genre_id]

            movies_with_extra = search_by_genre_and_year(
                genre_id,
                start_year,
                end_year,
                limit=limit + 1,
                offset=offset,
            )

            total_results = count_movies_by_genre_and_year(
                genre_id,
                start_year,
                end_year,
            )

        movies = movies_with_extra[:limit]
        has_next = len(movies_with_extra) > limit

        if log_search == "1":
            save_search(
                search_type="genre__years_range",
                params={
                    "genre": genre_name,
                    "years_range": f"{start_year}-{end_year}",
                },
                results_count=total_results,
            )

        add_statistics_to_context(context)

        context["movies"] = movies
        context["offset"] = offset
        context["has_previous"] = offset > 0
        context["has_next"] = has_next
        context["previous_offset"] = max(
            0,
            offset - limit,
        )
        context["next_offset"] = offset + limit
        context["pagination_type"] = "genre"

        if movies:
            page_number = offset // limit + 1

            context["message"] = (
                f"Страница {page_number}. "
                f"Показано результатов: {len(movies)}"
            )

        elif offset == 0:
            context["message"] = "Фильмы не найдены."

        else:
            context["message"] = "Больше фильмов нет."

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )

@app.get("/statistics", response_class=HTMLResponse)
def show_statistics(request: Request):
    """Показывает статистику поисковых запросов."""

    recent_searches = get_recent_searches()
    popular_searches = get_popular_searches()

    recent_rows = []

    for search in recent_searches:
        recent_rows.append(
            {
                "description": describe_search(
                    search.get("search_type"),
                    search.get("params", {}),
                ),
                "results_count": search.get("results_count", 0),
                "timestamp": format_timestamp(
                    search.get("timestamp")
                ),
            }
        )

    popular_rows = []

    for search in popular_searches:
        search_data = search.get("_id", {})

        popular_rows.append(
            {
                "description": describe_search(
                    search_data.get("search_type"),
                    search_data.get("params", {}),
                ),
                "count": search.get("search_count", 0),
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="statistics.html",
        context={
            "page_title": "Статистика",
            "recent_searches": recent_rows,
            "popular_searches": popular_rows,
        },
    )


@app.get("/film/{film_id}")
def film_detail(request: Request, film_id: int):
    """Показывает подробную информацию о фильме."""

    film = get_film_by_id(film_id)

    if film is None:
        return templates.TemplateResponse(
            request=request,
            name="film_detail.html",
            context={
                "film": None,
                "page_title": "Фильм не найден",
            },
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="film_detail.html",
        context={
            "film": film,
            "page_title": film[1],
        },
    )