import logging
import os
from pprint import pprint
import requests
import sys
import time
import telegram

from logging import StreamHandler

from dotenv import load_dotenv

load_dotenv()

RETRY_PERIOD = 600
tokens = {
    'practicum_token': os.getenv('PRACTICUM_TOKEN'),
    'telegram_token': os.getenv('TELEGRAM_TOKEN'),
    'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID')
}
practicum_token = os.getenv('PRACTICUM_TOKEN')
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
timestamp = {'from_date': 1682802000}
endpoint = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
headers = {'Authorization': f'OAuth {practicum_token}'}
homework_verdicts = {
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
# logging.debug('123')
# logging.info('Сообщение отправлено')
# logging.warning('Большая нагрузка!')
# logging.error('Бот не смог отправить сообщение')
# logging.critical('Всё упало! Зовите админа!1!111')


def check_tokens():
    """Проверь наличие обязательных токенов."""
    for key, value in tokens.items():
        if not value:
            logging.critical(f'Отсутствует обязательная переменная {key}.')
        continue


def send_message(bot, message):
    ...


def get_api_answer(timestamp):
    """Сделай запрос к API и верни ответ приведенный к данным Python."""
    try:
        response = requests.get(endpoint, headers=headers, params=timestamp)
    except Exception as error:
        return logging.error(f'Ошибка при запросе к API: {error}')
    pprint(response.json())


def check_response(response):
    ...


def parse_status(homework):
    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    get_api_answer(timestamp)

#     bot = telegram.Bot(token=telegram_token)
#     timestamp = int(time.time())

#     ...

#     while True:
#         try:

#             ...

#         except Exception as error:
#             message = f'Сбой в работе программы: {error}'
#             ...
#         ...


if __name__ == '__main__':
    main()
