class CaseValidationError(ValueError):
    """Ошибка проверки полей случая или выбранного оборудования"""

    def __init__(
        self, field: str, message: str = "Дата изготовления не должна содержать буквы"
    ):
        """Сохраняет поле и сообщение об ошибке"""
        self.field = field
        super().__init__(message)
