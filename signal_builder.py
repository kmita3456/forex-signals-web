# signal_builder.py
import numpy as np
import config
from dataclasses import dataclass
from typing import Optional

@dataclass
class Signal:
    symbol: str
    timeframe: str
    direction: str          # UP или DOWN
    confidence: float
    hold_time_minutes: int
    entry_price: float
    atr_value: float
    explanation: str
    weak: bool = False      # помечаем, если уверенность < 70

def calculate_confidence(trend_m30_dir, trend_m15_dir, signal_dir,
                         has_pattern, atr_current, atr_avg50,
                         volume_current, volume_avg20, near_sr):
    score = 0
    reasons = []

    if trend_m30_dir == signal_dir:
        score += 30
        reasons.append("M30 trend agrees")
    if trend_m15_dir == signal_dir:
        score += 20
        reasons.append("M15 trend agrees")
    if has_pattern:
        score += 20
        reasons.append("Candlestick pattern detected")
    if atr_current >= 0.5 * atr_avg50:
        score += 10
        reasons.append("ATR active")
    if volume_current > volume_avg20:
        score += 10
        reasons.append("Volume above average")
    if near_sr:
        score += 10
        reasons.append("Price near S/R level")

    return min(score, 100), ", ".join(reasons)

def calculate_hold_time(timeframe_min, atr_current, atr_avg50):
    # Фиксированные диапазоны
    ranges_minutes = {
        5: (5, 25),
        10: (10, 35),
        15: (15, 45),
        20: (20, 60),
        30: (30, 90)
    }
    low, high = ranges_minutes[timeframe_min]
    mid = (low + high) / 2
    vol_coef = atr_current / atr_avg50 if atr_avg50 != 0 else 1.0
    hold = mid * vol_coef
    return max(low, min(high, round(hold)))