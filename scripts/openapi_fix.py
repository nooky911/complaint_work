from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.openapi.utils import get_openapi
from typing import Any
import json


def openapi_encoding_fix(app: FastAPI):
    # Мутируем список роутов, чтобы удалить стандартный роут
    app.router.routes[:] = [
        route
        for route in app.router.routes
        if not (hasattr(route, "path") and route.path == "/openapi.json")
    ]

    # Регистрируем кастомный роут
    @app.get("/openapi.json", include_in_schema=False, response_class=Response)
    async def get_custom_openapi() -> Response:

        openapi_schema: dict[str, Any] | None = app.openapi_schema

        if not openapi_schema:
            # При генерации схемы используем app.routes (читаем полный список)
            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
            )
            app.openapi_schema = openapi_schema

        json_output_string = json.dumps(openapi_schema, ensure_ascii=False, indent=2)

        return Response(
            content=json_output_string.encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
