class WrongStatusCodeError(Exception):
    """Исключение для некорректного статуса при запросе к API."""

    pass


class RequiredVariableEError(Exception):
    """Исключение при отсутствии обязательных токенов."""

    pass


class FailedMessageError(Exception):
    """Исключение при ошибке в отправке сообщения в телеграм."""

    pass
