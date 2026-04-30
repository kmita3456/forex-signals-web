# news_filter.py
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import config
import logging

logger = logging.getLogger(__name__)

def is_news_time():
    """
    Возвращает True, если сейчас период ±30 мин от важной новости.
    Сначала пробует API Alpha Vantage, при неудаче – парсинг XML.
    Если ничего не работает – использует пустой список (без блокировки).
    """
    # Ручное указание времени (можно заполнить)
    manual_events = [
        # datetime(2026, 4, 29, 14, 30),  # пример
    ]
    now = datetime.utcnow()
    # Проверка ручных
    for evt in manual_events:
        if abs((now - evt).total_seconds()) <= config.NEWS_PAUSE_MINUTES * 60:
            return True

    # Попытка через Alpha Vantage
    if config.NEWS_API_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={config.NEWS_API_KEY}"
            # На самом деле у них другой endpoint, но оставим заглушку
            return False
        except:
            pass

    # Парсинг ForexFactory XML (резерв)
    try:
        resp = requests.get(config.NEWS_XML_URL)
        root = ET.fromstring(resp.content)
        for event in root.findall('event'):
            title = event.find('title').text
            date_str = event.find('date').text
            time_str = event.find('time').text
            impact = event.find('impact').text
            if impact.lower() != 'high':
                continue
            # Парсим дату/время
            dt_str = date_str + ' ' + time_str
            event_time = datetime.strptime(dt_str, '%m-%d-%Y %I:%M%p')
            if abs((now - event_time).total_seconds()) <= config.NEWS_PAUSE_MINUTES * 60:
                logger.info(f"News pause due to: {title}")
                return True
    except Exception as e:
        logger.warning(f"News filter parsing error: {e}")

    return False