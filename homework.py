import logging
import os
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
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PAYLOAD = {'from_date': 1682802000}
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
    for key, value in tokens.items():
        if not value:
            logging.critical(f'Отсутствует обязательная переменная {key}.')
        continue


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
    except Exception as error:
        return logging.error(f'Ошибка при запросе к API: {error}')
    return response.json()


def check_response(response):
    """Проверь ответ API на соответствие документации."""
    EXPECTED_KEYS = ['homeworks', 'current_date']
    EXPECTED_HOMEWORK_STATUSES = ['reviewing', 'approved', 'rejected']
    homework_info = response['homeworks']
    for key in response.keys():
        if key not in EXPECTED_KEYS:
            logging.error(f'Нет обязательного ключа {key}')
    for item in homework_info:
        if item['status'] not in EXPECTED_HOMEWORK_STATUSES:
            logging.error('Неизвестный статус')
    return response['homeworks'][0]


def parse_status(homework):
    """Извлеки статус домашней работы, верни сообщение для отправки."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_VERDICTS[homework_status]
    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{verdict}'
    )


def main():
    """Основная логика работы бота."""
    check_tokens()
    response = get_api_answer(PAYLOAD)
    homework = check_response(response)
    message = parse_status(homework)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    send_message(bot, message)
    while True:
        try:
            time.sleep(RETRY_PERIOD)
            main()
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        break


if __name__ == '__main__':
    main()
