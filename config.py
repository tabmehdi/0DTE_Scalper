import os

# ========= API & DATA CONFIGURATION ========= #

# API CREDENTIALS
ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")

# API URLS
OPTIONS_URL = "wss://stream.data.alpaca.markets/v1beta1/indicative"

# Bot webhook URL
CALL_WEBHOOK = os.getenv("CALL_WEBHOOK")
PUT_WEBHOOK = os.getenv("PUT_WEBHOOK")
# ========= PARAMETERS ========= #

# DATA PARAMETERS
SYMBOL = "SPY"
START = "T09:30:00-05:00"
END = "T15:59:00-05:00"
INDICATOR_LOOKBACK = 3

# EMA PARAMETERS
EMA_SHORT_PERIOD = 5
EMA_LONG_PERIOD = 14

# HULL MA PARAMETERS
HMA_PERIOD = 9

#SUPERTREND PARAMETERS
SUPERTREND_ATR_PERIOD = 2
SUPERTREND_MULTIPLIER = 2.2

#MACD PARAMETERS
MACD_FAST_LENGTH = 12
MACD_SLOW_LENGTH = 26
MACD_SIGNAL_LENGTH = 9

# RSI PARAMETERS
RSI_PERIOD = 14
RSI_LONG = 40
RSI_SHORT = 60

#SELLING PARAMETERS
# Take Profit Levels (TP1 hits first, TP2 second, then trailing for remainder)
TP1_PCT = 0.20           # % take profit level 1
TP1_POSITION_SIZE = 0.50 # Close % of position at TP1

TP2_PCT = 0.40           # % take profit level 2
TP2_POSITION_SIZE = 0.25 # Close % of position at TP2

# Remaining % uses trailing stop AFTER TP2 is hit
TRAILING_SL = 0.10       # % trailing stop loss (active after TP2)

# Initial hard stop loss (moves to breakeven when TP1 hits)
HARD_SL = 0.20           # % hard stop loss before TP1

# Time parameters
TIME_LIMIT = 420         # Seconds to hold position before exiting
