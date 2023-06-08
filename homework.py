import logging
import os
import requests
import sys
import time
import telegram
from json import JSONDecodeError
from logging import StreamHandler, FileHandler

from dotenv import load_dotenv

from exceptions import (
    WrongStatusCodeError,
    RequiredVariableEError,
    FailedMessageError
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
            'Сообщение со статусом домашней работы отправлено',
            exc_info=True
        )
    except FailedMessageError:
        raise FailedMessageError(
            'Ошибка отправки сообщения со статусом домашней работы'
        )


def get_api_answer(timestamp):
    """Сделай запрос к API и верни ответ приведенный к данным Python."""
    # timestamp = {'from_date': 0}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
    except requests.RequestException as error:
        raise requests.RequestException(
            f'Ошибка при запросе к API с параметрами:'
            f'{ENDPOINT}, headers={HEADERS}, params={timestamp}: {error}'
        )
    if response.status_code != 200:
        raise WrongStatusCodeError(
            f'Ошибка при запросе к API с параметрами:'
            f'{ENDPOINT}, headers={HEADERS}, params={timestamp}'
        )
    try:
        response.json()
    except JSONDecodeError:
        raise JSONDecodeError(
            f'Неожиданный формат ответа при запросе к API с параметрами:'
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
    if 'homeworks' in response:
        homeworks_info = response['homeworks']
    else:
        raise KeyError('Отсутствует ключ "homeworks"')
    if not isinstance(homeworks_info, list):
        raise TypeError(
            f'Неправильный формат ответа. '
            f'Вместо списка получен {type(homeworks_info)}')
    return homeworks_info


def parse_status(homeworks):
    """Извлеки статус домашней работы, верни сообщение для отправки."""
    if 'homework_name' not in homeworks[0]:
        raise KeyError('Отсутствует ключ "homework_name"')
    name = homeworks[0]['homework_name']
    status = homeworks[0]['status']
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
    timestamp = {'from_date': 0}
    # timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            message = parse_status(homeworks)
            send_message(bot, message)
        except FailedMessageError as error:
            logging.exception(
                f'Ошибка отправки сообщения со статусом домашней работы: '
                f'{error}'
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
        else:
            timestamp = {'from_date': response.get('current_date', 0)}
        finally:
            # print('>>>DONE!')
            # break
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
