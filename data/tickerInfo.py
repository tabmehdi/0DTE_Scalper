from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockLatestBarRequest

import pandas as pd
from datetime import datetime
from pytz import timezone, utc

import config

client = StockHistoricalDataClient(config.ALPACA_KEY, config.ALPACA_SECRET)

def candleHist(symbol, start_time, end_time):
    today = datetime.now().strftime("%Y-%m-%d")

    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Minute,
        start=today + start_time,
        end=today + end_time,
        feed="iex"
    )
    bars = client.get_stock_bars(request)
    df = bars.df.reset_index()

    if df.empty:
        return None

    df['timestamp'] = df['timestamp'].dt.tz_convert("America/New_York")

    df.rename(columns={
        'timestamp': 'Datetime',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    df.set_index('Datetime', inplace=True)

    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

    df[['Open','High','Low','Close','Volume']] = df[['Open','High','Low','Close','Volume']].ffill()

    return df

def candleNew(symbol):

    request = StockLatestBarRequest(
        symbol_or_symbols=[symbol],
        feed="iex"
    )

    latest = client.get_stock_latest_bar(request)
    bar = list(latest.values())[0] if isinstance(latest, dict) else latest

    ny_tz = timezone("America/New_York")
    ts = bar.timestamp.replace(tzinfo=utc).astimezone(ny_tz)

    df = pd.DataFrame({
        'Open': [bar.open],
        'High': [bar.high],
        'Low': [bar.low],
        'Close': [bar.close],
        'Volume': [bar.volume]
    }, index=[ts])
    df.index.name = 'Datetime'

    return df

 
