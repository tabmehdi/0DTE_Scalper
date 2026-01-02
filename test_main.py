from data.optionsLive import OptionLive
import asyncio

from data.tickerInfo import candleHist, candleNew
from data.optionsInfo import optionsNew, optionSymbol
from strategies.signal import calculateIndicators, calculateSignal
from broker.order import buy_call, buy_put
import config

import pandas as pd
from datetime import datetime

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 1000)


async def main_loop_async(option_live, history_df):
    """Async version of main loop that runs every minute and subscribes to options."""
    
    if history_df is None:
        print(f"No data returned for {config.SYMBOL} for {datetime.now().strftime('%Y-%m-%d')}")
        return None, False
    
    # Wait for the next minute
    now = datetime.now()
    seconds_to_next_minute = 60 - now.second - now.microsecond/1_000_000
    await asyncio.sleep(seconds_to_next_minute + 1)

    # Fetch latest bar
    latest_bar_df = candleNew(config.SYMBOL)
    last_ts = history_df.index[-1]

    if latest_bar_df.index[0] > last_ts:
        history_df = pd.concat([history_df, latest_bar_df])

    # Calculate indicators and signal
    indicator_df = calculateIndicators(history_df)
    signal = calculateSignal(indicator_df, config.INDICATOR_LOOKBACK)
    option_sym = optionSymbol(signal, history_df["Close"].iloc[-1])

    ts_str = str(history_df.index[-1])
    
    if signal == 1:
        print(f"{ts_str} Buy Signal Detected - {option_sym} @ {optionsNew(option_sym)} for {config.SYMBOL} at {history_df['Close'].iloc[-1]}")
        print(buy_call())
        # Subscribe to the option for live price monitoring
        try:
            await option_live.subscribe(option_sym)
            entry_price = optionsNew(option_sym)
            if entry_price:
                await option_live.set_trailing_stop_loss(
                    option_sym, 
                    entry_price, 
                    stop_pct=config.TRAILING_SL,
                    hard_stop_pct=config.HARD_SL,
                    max_hold_seconds=config.TIME_LIMIT
                )
        except Exception as e:
            print(f"Failed to subscribe to {option_sym}: {e}")
            
    elif signal == -1:
        print(f"{ts_str} Sell Signal Detected - {option_sym} @ {optionsNew(option_sym)} for {config.SYMBOL} at {history_df['Close'].iloc[-1]}")
        print(buy_put())
        # Subscribe to the option for live price monitoring
        try:
            await option_live.subscribe(option_sym)
            entry_price = optionsNew(option_sym)
            if entry_price:
                await option_live.set_trailing_stop_loss(
                    option_sym, 
                    entry_price, 
                    stop_pct=config.TRAILING_SL,
                    hard_stop_pct=config.HARD_SL,
                    max_hold_seconds=config.TIME_LIMIT
                )
        except Exception as e:
            print(f"Failed to subscribe to {option_sym}: {e}")
    else:
        print(f"{ts_str} No Signal Detected for {config.SYMBOL} at {history_df['Close'].iloc[-1]}")

    return history_df, True


async def main():
    """Main entry point that integrates indicator signals with WebSocket subscription."""
    
    history_df = candleHist(config.SYMBOL, config.START, config.END)
    
    if history_df is None:
        print(f"Failed to load historical data for {config.SYMBOL}")
        return
    
    option_live = OptionLive()
    await option_live.connect()
    
    listener = asyncio.create_task(option_live.listen())
    
    print(f"Started trading bot for {config.SYMBOL}")
    print(f"Will check for signals every minute using real indicators")
    print("=" * 60)
    
    try:
        while True:
            history_df, keep_running = await main_loop_async(option_live, history_df)
            if not keep_running:
                break
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Clean up
        await option_live.disconnect()
        listener.cancel()
        print("Disconnected from WebSocket")


if __name__ == "__main__":
    asyncio.run(main())


