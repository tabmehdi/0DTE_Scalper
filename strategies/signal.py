import config
from strategies.indicators import hullMA, emaCross, supertrend, macd, rsi
import pandas as pd

def calculateIndicators(df): 
    # Create your own pandas dataframe using the indicators you want
    return indicators_df


def calculateSignal(indicators_df, lookback_period):
    # Create your own strategy and return a buy signal in this format (1 for call, -1 for a put, 0 for neutral)
    return signal
