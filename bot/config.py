import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///prices.db')

    # Настройки парсера
    OZON_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    # Интервал проверки цен (в секундах)
    CHECK_INTERVAL = 3600  # 1 час

    # Процент изменения для уведомления
    PRICE_CHANGE_THRESHOLD = 5  # 5%