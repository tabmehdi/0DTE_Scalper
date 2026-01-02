from data.tickerInfo import candleHist, candleNew
from data.optionsInfo import optionsNew, optionSymbol
from strategies.signal import calculateIndicators, calculateSignal
from broker.order import buy_call, buy_put
import config

import pandas as pd
from datetime import datetime
import time


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 1000)

history_df = candleHist(config.SYMBOL, config.START, config.END)

def main_loop(history_df):

    if history_df is None:
        print(f"No data returned for {config.SYMBOL} for {datetime.now().strftime('%Y-%m-%d')}")
        return None, False
    
    now = datetime.now()
    seconds_to_next_minute = 60 - now.second - now.microsecond/1_000_000
    time.sleep(seconds_to_next_minute + 1)

    latest_bar_df = candleNew(config.SYMBOL)
    last_ts = history_df.index[-1]

    if latest_bar_df.index[0] > last_ts:
        history_df = pd.concat([history_df, latest_bar_df])

    indicator_df = calculateIndicators(history_df)
    signal = calculateSignal(indicator_df, config.INDICATOR_LOOKBACK)
    option_symbol = optionSymbol(signal, history_df["Close"].iloc[-1])

    ts_str = str(history_df.index[-1])
    if signal == 1:
        print(f"{ts_str} Buy Signal Detected - {option_symbol} @ {optionsNew(option_symbol)} for {config.SYMBOL} at {history_df["Close"].iloc[-1]}")
        print(buy_call())
    elif signal == -1:
        print(f"{ts_str} Sell Signal Detected - {option_symbol} @ {optionsNew(option_symbol)} for {config.SYMBOL} at {history_df["Close"].iloc[-1]}")
        print(buy_put())
    else:
        print(f"{ts_str} No Signal Detected for {config.SYMBOL} at {history_df["Close"].iloc[-1]}")

    return history_df, True


while True:
    history_df, keep_running = main_loop(history_df)
    if not keep_running:
        break



