import httpx
from datetime import date, datetime
from html.parser import HTMLParser

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
        report_url = f"{base_url}/ulservice/DislocationReportElectricLoco/Get"
        with httpx.Client(
            timeout=30,
            verify=settings.UL_SERVICE_VERIFY_SSL,
            follow_redirects=False,
        ) as client:
            ULServiceClient._login(client, base_url)

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

    @staticmethod
    def _login(client, base_url):
        """Авторизует общий HTTP-клиент для отчётов локомотивов и поездов"""
        login_url = f"{base_url}/ulservice/Account/Login"
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

    @staticmethod
    def parse_train_report(html):
        """Извлекает согласованные модели и номера из HTML-отчёта UL"""
        parser = _TrainReportParser()
        parser.feed(html)
        header = next(
            (row for row in parser.rows if "Серия" in row and "Номер" in row), None
        )
        if header is None:
            raise ValueError("UL не вернул таблицу поездов с серией и номером")
        model_index, number_index = header.index("Серия"), header.index("Номер")
        result = set()
        for row in parser.rows:
            if len(row) <= max(model_index, number_index):
                continue
            model = {"ЭС104": "ЭС104", "ЭС105С": "ЭС105"}.get(
                row[model_index].upper().strip()
            )
            number_text = row[number_index].strip()
            if model is None or not number_text.isdecimal():
                continue
            number = int(number_text)
            if number >= (30 if model == "ЭС104" else 1):
                result.add((model, f"{number:03d}"))
        return result

    @staticmethod
    def get_train_identities():
        """Читает появившиеся поезда без проверки даты запуска"""
        base_url = settings.UL_SERVICE_URL.rstrip("/")
        with httpx.Client(
            timeout=30, verify=settings.UL_SERVICE_VERIFY_SSL, follow_redirects=False
        ) as client:
            ULServiceClient._login(client, base_url)
            report = client.post(
                f"{base_url}/ulservice/Api/DislocationReportElectricTrain/GetReport",
                json={
                    "ReportDate": date.today().isoformat() + "T00:00:00+03:00",
                    "ReportHour": "Morning",
                },
                headers={
                    "Accept": "text/html, */*",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            report.raise_for_status()
            return ULServiceClient.parse_train_report(report.text)


class _TrainReportParser(HTMLParser):
    """Читает текст ячеек отчёта, включая HTML-сущности"""

    def __init__(self):
        """Подготавливает накопители строк и ячеек"""
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        """Начинает строку или ячейку таблицы"""
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []

    def handle_data(self, data):
        """Сохраняет текст вложенных элементов ячейки"""
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        """Завершает накопление ячейки или строки"""
        if tag in ("td", "th") and self.cell is not None:
            if self.row is not None:
                self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
