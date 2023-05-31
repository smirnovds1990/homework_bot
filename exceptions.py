class WrongStatusCodeException(Exception):
    """Исключение для некорректного статуса при запросе к API."""

    pass


class ParseStatusException(Exception):
    """Исключение при отсутствии ключей 'homework_name' и 'status'."""

    pass


class WrongKeyException(Exception):
    """Исключение при отсутствии ключа 'homeworks'."""

    pass
