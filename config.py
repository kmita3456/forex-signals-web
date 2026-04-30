# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- MetaTrader 5 ---
MT5_LOGIN = int(os.getenv("MT5_LOGIN", 5049951934))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "-uOj5cId")
MT5_SERVER = os.getenv("MT5_SERVER", "MetaQuotes-Demo")

# --- Firebase ---
FIREBASE_SERVICE_ACCOUNT_KEY = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "./serviceAccountKey.json")

# --- Торговые пары и таймфреймы ---
SYMBOLS = ["EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD"]
TIMEFRAMES = ["M5", "M10", "M15", "M20", "M30"]
TIMEFRAME_MINUTES = {
    "M5": 5,
    "M10": 10,
    "M15": 15,
    "M20": 20,
    "M30": 30
}

# --- Параметры индикаторов ---
EMA_PERIODS = [50, 200]
RSI_PERIOD = 14
MACD_PARAMS = {"fast": 12, "slow": 26, "signal": 9}
ATR_PERIOD = 14
ATR_AVG_PERIOD = 50

# --- Анализ уровней ---
SR_LOOKBACK = 300        # сколько свечей анализировать для поиска уровней
SR_TOLERANCE_FACTOR = 0.002  # 0.2% от цены

# --- Фильтры ---
MIN_CONFIRMATIONS = 2    # минимум подтверждений для конвергенции
ATR_THRESHOLD_FACTOR = 0.5  # ATR_current < 0.5 * средний ATR -> отклонить
RSI_OVERBOUGHT = 80
RSI_OVERSOLD = 20
NEWS_PAUSE_MINUTES = 30  # пауза вокруг важных новостей (±30 минут)

# --- Новостной фильтр ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY", None)
# Резервный XML ForexFactory
NEWS_XML_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

# --- Логирование ---
LOG_FILE = "bot.log"