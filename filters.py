# filters.py
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)

def filter_convergence(macd_signal, rsi_val, trend_m30, trend_m15, pattern_detected, signal_dir):
    confirmations = 0
    if trend_m30 == signal_dir and trend_m15 == signal_dir:
        confirmations += 1
    if pattern_detected:
        confirmations += 1
    if macd_signal == signal_dir:  # ожидается 'UP' или 'DOWN'
        confirmations += 1
    # RSI не противоречит: для BUY RSI < 70, для SELL RSI > 30
    if signal_dir == 'UP' and rsi_val < 70:
        confirmations += 0.5  # полуподтверждение
    elif signal_dir == 'DOWN' and rsi_val > 30:
        confirmations += 0.5

    passed = confirmations >= config.MIN_CONFIRMATIONS
    if not passed:
        logger.info(f"Convergence filter failed: confirmations={confirmations}")
    return passed

def filter_atr(atr_current, atr_avg50):
    if atr_current < config.ATR_THRESHOLD_FACTOR * atr_avg50:
        logger.info(f"ATR filter: market too slow (ATR={atr_current:.5f} < 0.5*avg={atr_avg50:.5f})")
        return False
    return True

def filter_sr(in_zone, last_candle_closed_inside_zone):
    """
    Если цена внутри зоны уровня и текущая закрывшаяся свеча не пробила её – отклоняем.
    last_candle_closed_inside_zone: булево значение, которое мы вычислим в основном коде.
    """
    if in_zone and last_candle_closed_inside_zone:
        logger.info("S/R filter: price inside zone and no breakout candle")
        return False
    return True

def filter_rsi(rsi_val, signal_dir, pattern_engulfing, confirmations):
    if signal_dir == 'UP' and rsi_val > config.RSI_OVERBOUGHT:
        if not (pattern_engulfing and confirmations >= 3):
            logger.info(f"RSI filter: RSI={rsi_val:.1f} > {config.RSI_OVERBOUGHT}, buy rejected")
            return False
    if signal_dir == 'DOWN' and rsi_val < config.RSI_OVERSOLD:
        if not (pattern_engulfing and confirmations >= 3):
            logger.info(f"RSI filter: RSI={rsi_val:.1f} < {config.RSI_OVERSOLD}, sell rejected")
            return False
    return True