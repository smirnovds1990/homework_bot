import logging
import os
import sys
import time
from json import JSONDecodeError
from logging import FileHandler, StreamHandler

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    FailedMessageError,
    RequiredVariableEError,
    WrongStatusCodeError
)


load_dotenv()

RETRY_PERIOD = 600
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
homework_status_message = (
    'Изменился статус проверки работы "{name}". {verdict}'
)


def check_tokens():
    """Проверь наличие обязательных токенов."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    required_variables = []
    for key, value in tokens.items():
        if not value:
            required_variables.append(key)
    if required_variables:
        raise RequiredVariableEError(
            f'Отсутствуют обязательные переменные {required_variables}.'
        )


def send_message(bot, message):
    """Отправть сообщение в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(
            'Сообщение со статусом домашней работы отправлено'
        )
    except Exception:
        raise FailedMessageError(
            'Ошибка отправки сообщения со статусом домашней работы'
        )


def get_api_answer(timestamp):
    """Сделай запрос к API и верни ответ приведенный к данным Python."""
    timestamp = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
    except requests.RequestException as error:
        raise ConnectionError(
            f'Ошибка при запросе к API с параметрами:'
            f'{ENDPOINT}, headers={HEADERS}, params={timestamp}: {error}'
        )
    if response.status_code != 200:
        raise WrongStatusCodeError(
            f'Ошибка при запросе к API с параметрами:'
            f'{ENDPOINT}, headers={HEADERS}, params={timestamp}'
        )
    return response.json()


def check_response(response):
    """Проверь ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            f'Неправильный формат ответа. Нужен словарь. '
            f'Получен {type(response)}'
        )
    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ "homeworks"')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            f'Неправильный формат ответа. '
            f'Вместо списка получен {type(homeworks)}')
    return homeworks


def parse_status(homework):
    """Извлеки статус домашней работы, верни сообщение для отправки."""
    required_keys = ['homework_name', 'status']
    for key in required_keys:
        if key not in homework:
            raise KeyError(f'Отсутствует ключ {key}')
    name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise KeyError(f'Отсутствует статус домашней работы "{status}"')
    verdict = HOMEWORK_VERDICTS[status]
    return homework_status_message.format(name=name, verdict=verdict)


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except RequiredVariableEError as error:
        logging.critical(error)
        sys.exit(error)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.exception('Список домашних работ пуст.')
                raise ValueError('Список домашних работ пуст.')
            homework, *_ = homeworks
            message = parse_status(homework)
            send_message(bot, message)
        except ConnectionError as error:
            logging.exception(
                f'Ошибка отправки сообщения со статусом домашней работы: '
                f'{error}'
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            send_message(bot, message)
        else:
            timestamp = {'from_date': response.get('current_date', 0)}
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format=(
            '%(asctime)s - %(levelname)s - %(name)s - %(filename)s'
            ' - %(funcName)s - %(lineno)s - %(message)s'
        ),
        level=logging.DEBUG,
        handlers=[
            FileHandler(filename=__file__ + '.log', mode='w'),
            StreamHandler(sys.stdout)
        ],
        encoding='UTF-8'
    )
    main()
