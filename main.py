# main.py
import logging
import numpy as np
import pandas as pd
from datetime import datetime
import time
import sys

import config
from mt5_connector import connect_mt5, fetch_ohlc
from analytics import (ema, rsi, macd, atr, detect_trend,
                       find_sr_levels, is_bullish_engulfing, is_bearish_engulfing,
                       is_hammer, is_hanging_man, is_morning_star, is_evening_star)
from filters import (filter_convergence, filter_atr, filter_sr, filter_rsi)
from signal_builder import Signal, calculate_confidence, calculate_hold_time
from news_filter import is_news_time
from firestore_writer import init_firestore, save_signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(config.LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def analyze_symbol(symbol: str, tf: str):
    """
    Полный анализ одного символа и таймфрейма.
    Возвращает Signal или None.
    """
    tf_min = config.TIMEFRAME_MINUTES[tf]
    try:
        df = fetch_ohlc(symbol, tf, 2000)
    except Exception as e:
        logger.error(f"Data fetch error {symbol} {tf}: {e}")
        return None

    # Вычисление индикаторов
    df['ema50'] = ema(df['close'], 50)
    df['ema200'] = ema(df['close'], 200)
    df['rsi'] = rsi(df['close'], 14)
    df['macd_line'], df['macd_signal'] = macd(df['close'])
    df['atr'] = atr(df, 14)
    atr_avg50 = df['atr'].rolling(50).mean().iloc[-1]
    atr_current = df['atr'].iloc[-1]
    volume_avg20 = df['volume'].rolling(20).mean().iloc[-1]
    volume_current = df['volume'].iloc[-1]

    # Определение направления сигнала на основе младшего таймфрейма
    # Сначала ищем свечной паттерн
    pattern = None
    if is_bullish_engulfing(df) or is_morning_star(df) or (is_hammer(df) and df['close'].iloc[-1] > df['open'].iloc[-1]):
        pattern = 'UP'
    elif is_bearish_engulfing(df) or is_evening_star(df) or (is_hanging_man(df) and df['close'].iloc[-1] < df['open'].iloc[-1]):
        pattern = 'DOWN'

    # Если паттерна нет, можно использовать пересечение MACD
    macd_cross = None
    if df['macd_line'].iloc[-2] < df['macd_signal'].iloc[-2] and df['macd_line'].iloc[-1] > df['macd_signal'].iloc[-1]:
        macd_cross = 'UP'
    elif df['macd_line'].iloc[-2] > df['macd_signal'].iloc[-2] and df['macd_line'].iloc[-1] < df['macd_signal'].iloc[-1]:
        macd_cross = 'DOWN'

    signal_dir = pattern or macd_cross
    if not signal_dir:
        logger.debug(f"No pattern or MACD cross for {symbol} {tf}")
        return None

    # Мультитаймфреймовый анализ: подгружаем M30 и M15
    try:
        df_m30 = fetch_ohlc(symbol, "M30", 200)
        df_m15 = fetch_ohlc(symbol, "M15", 200)
    except:
        logger.warning(f"Could not fetch higher TFs for {symbol}")
        return None

    df_m30['ema50'] = ema(df_m30['close'], 50)
    df_m30['ema200'] = ema(df_m30['close'], 200)
    trend_m30 = detect_trend(df_m30, 'ema50', 'ema200')

    df_m15['ema50'] = ema(df_m15['close'], 50)
    df_m15['ema200'] = ema(df_m15['close'], 200)
    trend_m15 = detect_trend(df_m15, 'ema50', 'ema200')

    if trend_m30 == 'SIDEWAYS':
        logger.info(f"{symbol} M30 is sideways, no signal")
        return None
    if trend_m30 != trend_m15:
        logger.info(f"{symbol} M30 and M15 trends differ, no signal")
        return None

    # Проверка зоны S/R
    levels, in_zone = find_sr_levels(df, config.SR_LOOKBACK, config.SR_TOLERANCE_FACTOR)
    # Определяем, закрылась ли последняя свеча внутри зоны
    last_close = df['close'].iloc[-1]
    if levels:
        closest_level = min(levels, key=lambda x: abs(x - last_close))
        in_zone_tolerance = config.SR_TOLERANCE_FACTOR * last_close / 2
        last_candle_closed_inside = abs(last_close - closest_level) < in_zone_tolerance
    else:
        last_candle_closed_inside = False

    # Фильтры
    rsi_val = df['rsi'].iloc[-1]
    macd_signal_dir = 'UP' if df['macd_line'].iloc[-1] > df['macd_signal'].iloc[-1] else 'DOWN'
    # Подсчёт подтверждений для конвергенции (передаём позже)

    # Фильтр новостей
    if is_news_time():
        logger.info(f"News pause, {symbol} {tf} skipped")
        return None

    # Конвергенция
    has_pattern = pattern is not None
    confirmations_count = (
        int(trend_m30 == signal_dir and trend_m15 == signal_dir) +
        int(has_pattern) +
        int(macd_signal_dir == signal_dir) +
        (0.5 if (signal_dir == 'UP' and rsi_val < 70) or (signal_dir == 'DOWN' and rsi_val > 30) else 0)
    )
    if not filter_convergence(macd_signal_dir, rsi_val, trend_m30, trend_m15, has_pattern, signal_dir):
        return None

    # ATR
    if not filter_atr(atr_current, atr_avg50):
        return None

    # S/R
    if not filter_sr(in_zone, last_candle_closed_inside):
        return None

    # RSI
    engulfing = (pattern == 'UP' and is_bullish_engulfing(df)) or (pattern == 'DOWN' and is_bearish_engulfing(df))
    if not filter_rsi(rsi_val, signal_dir, engulfing, confirmations_count):
        return None

    # Расчёт уверенности и времени удержания
    confidence, reason_str = calculate_confidence(
        trend_m30, trend_m15, signal_dir,
        has_pattern, atr_current, atr_avg50,
        volume_current, volume_avg20, in_zone
    )
    hold_time = calculate_hold_time(tf_min, atr_current, atr_avg50)

    entry_price = df['close'].iloc[-1]
    explanation = f"{reason_str}. Signal {signal_dir} on {tf}."
    if confidence < 70:
        explanation += " WEAK signal confidence."

    signal = Signal(
        symbol=symbol,
        timeframe=tf,
        direction=signal_dir,
        confidence=confidence,
        hold_time_minutes=hold_time,
        entry_price=entry_price,
        atr_value=atr_current,
        explanation=explanation,
        weak=(confidence < 70)
    )
    return signal

def main_loop():
    # Инициализация Firestore
    db = init_firestore()
    connect_mt5()

    while True:
        try:
            for symbol in config.SYMBOLS:
                for tf in config.TIMEFRAMES:
                    signal = analyze_symbol(symbol, tf)
                    if signal:
                        signal_dict = {
                            'symbol': signal.symbol,
                            'timeframe': signal.timeframe,
                            'direction': signal.direction,
                            'confidence': signal.confidence,
                            'hold_time_minutes': signal.hold_time_minutes,
                            'entry_price': signal.entry_price,
                            'atr_value': signal.atr_value,
                            'explanation': signal.explanation,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        save_signal(db, signal_dict)
                        logger.info(f"Signal saved: {signal.symbol} {signal.direction}")
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
        time.sleep(60)

if __name__ == "__main__":
    main_loop()