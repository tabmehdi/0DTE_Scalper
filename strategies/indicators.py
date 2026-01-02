import pandas as pd
import numpy as np

def hullMA(df, length):

    df = df.copy()
    close = df["Close"]

    length = int(length)
    half = length // 2
    sqrt_len = int(np.sqrt(length))

    def wma(series, l):
        l = int(l)
        weights = np.arange(1, l + 1)
        return series.rolling(l).apply(
            lambda x: np.dot(x, weights) / weights.sum(),
            raw=True
        )

    hma = wma(
        2 * wma(close, half) - wma(close, length),
        sqrt_len
    )

    mhull = hma
    shull = hma.shift(2)

    signal = np.where(
        mhull.isna() | shull.isna(),
        0,
        np.where(mhull > shull, 1, -1)
    )

    df["HMA_SIGNAL"] = signal
    return df[["HMA_SIGNAL"]]

def emaCross(df, short_len, long_len):

    short_ema = df['Close'].ewm(span=short_len, adjust=False).mean()
    long_ema = df['Close'].ewm(span=long_len, adjust=False).mean()

    signal = pd.Series(0, index=df.index)
    signal[(short_ema > long_ema) & (short_ema.shift(1) <= long_ema.shift(1))] = 1
    signal[(short_ema < long_ema) & (short_ema.shift(1) >= long_ema.shift(1))] = -1
    
    return signal


def supertrend(df, atr_period, multiplier):

    df = df.copy()
    high = df['High']
    low = df['Low']
    close = df['Close']

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(atr_period).mean()

    stup = pd.Series(index=df.index, dtype=float)
    dn = pd.Series(index=df.index, dtype=float)
    sttrend = pd.Series(1, index=df.index)
    signal = pd.Series(0, index=df.index)

    for i in range(len(df)):
        if i == 0:
            stup.iloc[i] = close.iloc[i] - multiplier * atr.iloc[i]
            dn.iloc[i] = close.iloc[i] + multiplier * atr.iloc[i]
            signal.iloc[i] = 0
            continue

        stup.iloc[i] = close.iloc[i] - multiplier * atr.iloc[i]
        dn.iloc[i] = close.iloc[i] + multiplier * atr.iloc[i]

        stup.iloc[i] = max(stup.iloc[i], stup.iloc[i-1]) if close.iloc[i-1] > stup.iloc[i-1] else stup.iloc[i]
        dn.iloc[i] = min(dn.iloc[i], dn.iloc[i-1]) if close.iloc[i-1] < dn.iloc[i-1] else dn.iloc[i]

        prev_trend = sttrend.iloc[i-1]
        if prev_trend == -1 and close.iloc[i] > dn.iloc[i-1]:
            sttrend.iloc[i] = 1
        elif prev_trend == 1 and close.iloc[i] < stup.iloc[i-1]:
            sttrend.iloc[i] = -1
        else:
            sttrend.iloc[i] = prev_trend

        signal.iloc[i] = 1 if sttrend.iloc[i] == 1 else -1

    return pd.DataFrame({"SUPER_TREND_SIGNAL": signal})

def macd(df, fast_length, slow_length, signal_length):
    df = df.copy()
    src = df['Close']


    fast_ma = src.ewm(span=fast_length, adjust=False).mean()
    slow_ma = src.ewm(span=slow_length, adjust=False).mean()
    macd_line = fast_ma - slow_ma
    signal_line = macd_line.ewm(span=signal_length, adjust=False).mean()

    signal = pd.Series(0, index=df.index)
    signal[macd_line > signal_line] = 1
    signal[macd_line < signal_line] = -1

    return pd.DataFrame({"MACD_SIGNAL": signal})

def rsi(df, length, long_level, short_level):

    df = df.copy()
    src = df['Close']

    delta = src.diff()

    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)

    alpha = 1 / length
    up_ema = up.ewm(alpha=alpha, adjust=False).mean()
    down_ema = down.ewm(alpha=alpha, adjust=False).mean()

    rs = up_ema / down_ema
    rsi = 100 - (100 / (1 + rs))

    signal = pd.Series(0, index=df.index)
    signal[rsi <= long_level] = 1
    signal[rsi >= short_level] = -1

    return pd.DataFrame({"RSI_SIGNAL": signal})


