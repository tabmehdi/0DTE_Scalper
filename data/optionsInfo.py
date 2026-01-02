import math
from datetime import datetime

from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest

import config

def optionSymbol(signal, current_price): 

    if signal == -1:
        option_type = "P"
        strike = math.ceil(current_price)
    else:
        option_type = "C"
        strike = math.floor(current_price)
    
    date_part = datetime.now().strftime("%y%m%d")
    strike_part = f"{int(strike * 1000):08d}"

    return f"{config.SYMBOL}{date_part}{option_type}{strike_part}"


client = OptionHistoricalDataClient(config.ALPACA_KEY, config.ALPACA_SECRET)

def optionsNew(symbol):
    
    request = OptionLatestQuoteRequest(symbol_or_symbols=[symbol])
    
    latest = client.get_option_latest_quote(request)
    
    quote = latest.get(symbol)
    if not quote:
        return None
    
    bp = quote.bid_price
    ap = quote.ask_price
    
    if bp is None or ap is None:
        return None
    
    mid_price = (bp + ap) / 2
    return mid_price
