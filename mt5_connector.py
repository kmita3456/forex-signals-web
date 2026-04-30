# mt5_connector.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import config
import logging

logger = logging.getLogger(__5049951934__)

def connect_mt5():
    """Подключение к терминалу MT5, с повторными попытками"""
    if not mt5.initialize():
        logger.error("MT5 initialize failed, retrying in 10 sec...")
        import time
        time.sleep(10)
        if not mt5.initialize():
            raise ConnectionError("Cannot connect to MT5")
    authorized = mt5.login(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER)
    if not authorized:
        logger.error(f"MT5 login failed: {mt5.last_error()}")
        mt5.shutdown()
        raise ConnectionError(f"Login failed: {mt5.last_error()}")
    logger.info("Connected to MT5")
    return True

def fetch_ohlc(symbol: str, timeframe: str, n_candles: int = 2000):
    """
    Загружает последние n_candles свечей для symbol и timeframe.
    Возвращает DataFrame с колонками: time, open, high, low, close, tick_volume
    """
    tf_map = {
        "M5": mt5.TIMEFRAME_M5,
        "M10": mt5.TIMEFRAME_M10,
        "M15": mt5.TIMEFRAME_M15,
        "M20": mt5.TIMEFRAME_M20,
        "M30": mt5.TIMEFRAME_M30,
    }
    if timeframe not in tf_map:
        raise ValueError(f"Unknown timeframe: {timeframe}")

    rates = mt5.copy_rates_from_pos(symbol, tf_map[timeframe], 0, n_candles)
    if rates is None or len(rates) == 0:
        raise ValueError(f"No data for {symbol} {timeframe}")
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    return df[['time', 'open', 'high', 'low', 'close', 'volume']]