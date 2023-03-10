import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from exceptions import (
    APICallError,
    MissingDataInResponse,
    ParseStatusError,
    TelegramBotError
)

load_dotenv()
# Задана глобальная конфигурация для всех логгеров
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s, %(levelname)s, %(message)s",
)
# Настройки логгера для текущего файла
logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

RETRY_PERIOD = 600

ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
PAYLOAD = {"from_date": 0}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens():
    """Check the availability of environment variables."""
    required_env_vars = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for env_var in required_env_vars:
        if env_var is None:
            logger.critical((f"Enter a variable {env_var}"))
            exit()


def get_api_answer(timestamp):
    """Make a request to endpoint of the API service."""
    # Сonverting API response from JSON format to Python data types.
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            raise APICallError(
                f"Error {response.status_code}: {response.content}",
            )
        return response.json()
    except requests.RequestException as error:
        raise APICallError(
            f"Error while sending request to Telegram API: {error}"
        )


def check_response(response):
    """Check the API response for compliance with the documentation."""
    if not isinstance(response, dict):
        raise TypeError("Response is not a dictionary")
    if not response.get("homeworks"):
        raise MissingDataInResponse("Missing new homeworks")
    if not isinstance(response.get("homeworks"), list):
        raise TypeError("Not list")
    if "current_date" not in response:
        raise KeyError("No current date in response")
    return response["homeworks"]


def parse_status(homework):
    """
    Extract the status from the information about a particular homework.
    The function returns the line prepared for sending to Telegram,
    containing one of the verdicts of the HOMEWORK_VERDICTS dictionary.
    """
    # Сheck that there is `homework_name` key in the homework API response
    if "homework_name" not in homework:
        raise KeyError("Homework name is not found")
    homework_name = homework.get("homework_name")
    status = homework["status"]
    if status not in HOMEWORK_VERDICTS:
        raise ParseStatusError("Homework status is not found")
    verdict = HOMEWORK_VERDICTS[homework.get("status")]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Send a message to Telegram chat, defined by the TELEGRAM_CHAT_ID."""
    try:
        logging.info("Sending message to Telegram")
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f"Сообщение отправлено: {message}")
    except Exception as error:
        logging.error(f"Ошибка при отправке сообщения:{error}")


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    status = ""
    LIST_ERRORS = []
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            timestamp = response.get("current_date", timestamp)
            if homework:
                new_status = parse_status(homework[0])
                if status != new_status:
                    status = new_status
                    send_message(bot, status)
        except MissingDataInResponse as info:
            logger.info(info)
        except (TelegramBotError, KeyError, TypeError) as error:
            message = f"Сбой в работе программы: {error}"
            if message not in LIST_ERRORS:
                send_message(bot, message)
                LIST_ERRORS.append(message)
                logger.critical(message)
        except Exception as error:
            logger.critical(f'Unknown error {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
