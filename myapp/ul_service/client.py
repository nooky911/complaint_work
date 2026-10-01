from datetime import date, datetime
from html.parser import HTMLParser

import httpx

from myapp.config import settings


UL_MODEL_TYPES = {
    145: "2эс6",
    116: "3эс6",
    997: "2эс8",
    165: "3эс8",
}


class _TokenParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.token: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "input":
            return
        fields = dict(attrs)
        if fields.get("name") == "__RequestVerificationToken":
            self.token = fields.get("value")


class ULServiceClient:
    """Получает подтверждённые даты ввода локомотивов из UL-сервиса"""

    @staticmethod
    def get_commissioning_dates() -> dict[tuple[str, int], date]:
        """Возвращает даты по модели и номеру локомотива"""
        base_url = settings.UL_SERVICE_URL.rstrip("/")
        login_url = f"{base_url}/ulservice/Account/Login"
        report_url = f"{base_url}/ulservice/DislocationReportElectricLoco/Get"
        with httpx.Client(
            timeout=30,
            verify=settings.UL_SERVICE_VERIFY_SSL,
            follow_redirects=False,
        ) as client:
            login_page = client.get(login_url)
            login_page.raise_for_status()
            parser = _TokenParser()
            parser.feed(login_page.text)
            if not parser.token:
                raise ValueError("UL-сервис не вернул токен формы входа")

            login = client.post(
                login_url,
                data={
                    "UserName": settings.UL_SERVICE_USER,
                    "Password": settings.UL_SERVICE_PASSWORD,
                    "__RequestVerificationToken": parser.token,
                },
            )
            if login.status_code not in (200, 302, 303):
                login.raise_for_status()
                raise ValueError("UL-сервис вернул неожиданный ответ при входе")
            if not any(
                cookie.name.startswith(".AspNetCore.Identity.Application")
                for cookie in client.cookies.jar
            ):
                raise ValueError("UL-сервис не подтвердил вход")

            report = client.get(
                report_url,
                params={
                    "reportDate": date.today().isoformat(),
                    "reportTime": 1,
                    "reportType": 0,
                },
                headers={
                    "Accept": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            report.raise_for_status()
            if "application/json" not in report.headers.get("content-type", ""):
                raise ValueError("UL-сервис вернул ответ не в формате JSON")
            rows = report.json()
            if not isinstance(rows, list):
                raise ValueError("UL-сервис вернул неверный формат отчёта")

        result: dict[tuple[str, int], date] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                model_name = UL_MODEL_TYPES.get(int(row.get("locType")))
                number = int(row.get("locNum"))
            except (TypeError, ValueError):
                continue
            value = row.get("issueDateField")
            if model_name is None or not value:
                continue
            commissioned_at = datetime.strptime(str(value).strip(), "%d.%m.%Y").date()
            key = model_name, number
            if key in result and result[key] != commissioned_at:
                raise ValueError(f"Разные даты ввода для {model_name} №{number}")
            result[key] = commissioned_at
        return result
