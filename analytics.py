# analytics.py
import pandas as pd
import numpy as np
import config

# ---------- Индикаторы ----------
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line

def atr(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

# ---------- Тренд ----------
def detect_trend(df, ema50_col='ema50', ema200_col='ema200', lookback=100):
    """Возвращает 'UP', 'DOWN' или 'SIDEWAYS'"""
    ema50 = df[ema50_col].iloc[-1]
    ema200 = df[ema200_col].iloc[-1]
    price = df['close'].iloc[-1]
    diff_pct = abs(ema50 - ema200) / price

    # Определение локальных экстремумов
    highs = []
    lows = []
    window = 3
    for i in range(window, len(df)-window):
        if all(df['high'].iloc[i] > df['high'].iloc[i-window:i]) and \
           all(df['high'].iloc[i] > df['high'].iloc[i+1:i+1+window]):
            highs.append(df['high'].iloc[i])
        if all(df['low'].iloc[i] < df['low'].iloc[i-window:i]) and \
           all(df['low'].iloc[i] < df['low'].iloc[i+1:i+1+window]):
            lows.append(df['low'].iloc[i])

    # Проверка повышающихся/понижающихся экстремумов
    if len(highs) >= 2 and len(lows) >= 2:
        last_highs = highs[-2:]
        last_lows = lows[-2:]
        higher_highs = last_highs[-1] > last_highs[-2]
        higher_lows = last_lows[-1] > last_lows[-2]
        lower_lows = last_lows[-1] < last_lows[-2]
        lower_highs = last_highs[-1] < last_highs[-2]

        if ema50 > ema200 and higher_highs and higher_lows:
            return 'UP'
        elif ema50 < ema200 and lower_lows and lower_highs:
            return 'DOWN'

    if diff_pct < 0.001:  # 0.1%
        return 'SIDEWAYS'
    return 'SIDEWAYS'

# ---------- Уровни поддержки/сопротивления ----------
def find_sr_levels(df, lookback=300, tolerance_factor=0.002):
    """Возвращает список уровней и список, находится ли цена в зоне"""
    recent = df.tail(lookback).copy()
    price = recent['close'].iloc[-1]
    tolerance = tolerance_factor * price
    half_tol = tolerance / 2

    # Ищем локальные экстремумы
    window = 3
    highs = []
    lows = []
    for i in range(window, len(recent)-window):
        sub = recent.iloc[i-window:i+window+1]
        if recent['high'].iloc[i] == sub['high'].max():
            highs.append(recent['high'].iloc[i])
        if recent['low'].iloc[i] == sub['low'].min():
            lows.append(recent['low'].iloc[i])

    levels = []
    for group in [highs, lows]:
        # Группировка близких цен
        sorted_vals = sorted(group)
        clusters = []
        current_cluster = [sorted_vals[0]]
        for val in sorted_vals[1:]:
            if abs(val - current_cluster[-1]) <= tolerance:
                current_cluster.append(val)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(np.mean(current_cluster))
                current_cluster = [val]
        if len(current_cluster) >= 2:
            clusters.append(np.mean(current_cluster))
        levels.extend(clusters)

    # Проверка, находится ли текущая цена в зоне какого-либо уровня
    in_zone = any(abs(price - lvl) < half_tol for lvl in levels)
    return levels, in_zone

# ---------- Свечные паттерны ----------
def is_bullish_engulfing(df):
    if len(df) < 2: return False
    prev, curr = df.iloc[-2], df.iloc[-1]
    return (curr['close'] > curr['open'] and
            prev['close'] < prev['open'] and
            curr['open'] < prev['close'] and
            curr['close'] > prev['open'])

def is_bearish_engulfing(df):
    if len(df) < 2: return False
    prev, curr = df.iloc[-2], df.iloc[-1]
    return (curr['close'] < curr['open'] and
            prev['close'] > prev['open'] and
            curr['open'] > prev['close'] and
            curr['close'] < prev['open'])

def is_hammer(df):
    if len(df) < 1: return False
    c = df.iloc[-1]
    body = abs(c['close'] - c['open'])
    lower_shadow = min(c['open'], c['close']) - c['low']
    upper_shadow = c['high'] - max(c['open'], c['close'])
    range_ = c['high'] - c['low']
    if range_ == 0: return False
    # Нижняя тень >= 2*тело, верхняя тень маленькая, тело в верхней половине
    return (lower_shadow >= 2 * body and
            upper_shadow < 0.05 * body and
            (c['close'] + c['open']) / 2 > (c['high'] + c['low']) / 2)

def is_hanging_man(df):
    # Те же пропорции, но используется после восходящего движения (проверка вне функции)
    return is_hammer(df)

def is_doji(candle):
    body = abs(candle['close'] - candle['open'])
    range_ = candle['high'] - candle['low']
    return body <= 0.05 * range_ if range_ > 0 else False