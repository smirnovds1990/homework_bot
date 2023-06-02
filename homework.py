import logging
import os
import requests
import sys
import time
import telegram

from logging import StreamHandler

from dotenv import load_dotenv

from exceptions import (
    NoKeyException, ParseStatusException, WrongStatusCodeException,
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

logging.basicConfig(
    filename='main.log',
    filemode='w',
    format=(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s - %(filename)s'
        '- %(funcName)s - %(lineno)s'
    ),
    level=logging.DEBUG,
    encoding='UTF-8'
)
handler = StreamHandler(stream=sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s - %(message)s - %(filename)s'
    '- %(funcName)s - %(lineno)s'
)
handler.setFormatter(formatter)
logging.getLogger('').addHandler(handler)


def check_tokens():
    """Проверь наличие обязательных токенов."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if not token:
            logging.critical(f'Отсутствует обязательная переменная {token}.')
            break


def send_message(bot, message):
    """Отправть сообщение в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено')
    except Exception:
        logging.error('Ошибка отправки сообщения')


def get_api_answer(timestamp):
    """Сделай запрос к API и верни ответ приведенный к данным Python."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
    except requests.RequestException as error:
        print(f'Ошибка при запросе к API: {error}')
    if response.status_code != 200:
        raise WrongStatusCodeException('Ошибка при запросе к API')
    return response.json()


def check_response(response):
    """Проверь ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Неправильный формат ответа. Нужен словарь.')
    if 'homeworks' in response.keys():
        homework_info = response['homeworks']
    else:
        raise NoKeyException('Отсутствует ключ "homeworks"')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Неправильный формат ответа.')
    EXPECTED_HOMEWORK_STATUSES = ['reviewing', 'approved', 'rejected']
    for item in homework_info:
        if item['status'] not in EXPECTED_HOMEWORK_STATUSES:
            logging.error('Неизвестный статус')
    return response['homeworks'][0]


def parse_status(homework):
    """Извлеки статус домашней работы, верни сообщение для отправки."""
    if 'homework_name' not in homework.keys():
        raise ParseStatusException('Отсутствует ключ "homework_name"')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ParseStatusException('Отсутствует статус домашней работы')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{verdict}'
    )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = {'from_date': 1672520400}
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            timestamp = {'from_date': response['current_date']}
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
