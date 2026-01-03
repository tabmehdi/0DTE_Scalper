from data.optionsLive import OptionLive
import asyncio
import time

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
    
    now = datetime.now()
    seconds_to_next_minute = 60 - now.second - now.microsecond/1_000_000
    await asyncio.sleep(seconds_to_next_minute + 1)

    latest_bar_df = candleNew(config.SYMBOL)
    last_ts = history_df.index[-1]

    if latest_bar_df.index[0] > last_ts:
        history_df = pd.concat([history_df, latest_bar_df])

    indicator_df = calculateIndicators(history_df)
    signal = calculateSignal(indicator_df, config.INDICATOR_LOOKBACK)

    ts_str = str(history_df.index[-1])
    
    if option_live.stop_losses:
        active_symbol = list(option_live.stop_losses.keys())[0]
        stop_data = option_live.stop_losses[active_symbol]
        position_state = option_live.position_states.get(active_symbol, {})
        
        elapsed = time.time() - stop_data['entry_time']
        remaining_portions = []
        if position_state.get('tp1_active'):
            remaining_portions.append(f"TP1: {stop_data['tp1_size']*100:.0f}%")
        if position_state.get('tp2_active'):
            remaining_portions.append(f"TP2: {stop_data['tp2_size']*100:.0f}%")
        if position_state.get('trailing_active'):
            trailing_size = 1.0 - stop_data['tp1_size'] - stop_data['tp2_size']
            remaining_portions.append(f"Trailing: {trailing_size*100:.0f}%")
        
        current_sl_status = "Breakeven" if stop_data.get('stop_at_breakeven') else f"-{stop_data['hard_stop_pct']*100:.0f}%"
        
        print(f"\n{ts_str} ⚠️ TRADE IN PROGRESS - Cannot enter new trade")
        print(f"  Active Position: {active_symbol}")
        print(f"  Entry Price: ${stop_data['entry']:.2f}")
        print(f"  High Reached: ${stop_data['high']:.2f}")
        print(f"  Time Elapsed: {elapsed:.0f}s / {stop_data['max_hold_seconds']}s")
        print(f"  Current Stop: {current_sl_status}")
        print(f"  Remaining: {', '.join(remaining_portions)}")
        if signal == 1:
            skipped_option = optionSymbol(signal, history_df["Close"].iloc[-1])
            print(f"  Skipped Signal: CALL {skipped_option} for {config.SYMBOL} at {history_df['Close'].iloc[-1]}")
        elif signal == -1:
            skipped_option = optionSymbol(signal, history_df["Close"].iloc[-1])
            print(f"  Skipped Signal: PUT {skipped_option} for {config.SYMBOL} at {history_df['Close'].iloc[-1]}")
        print()
        return history_df, True

    if signal == 1:
        option_sym = optionSymbol(signal, history_df["Close"].iloc[-1])
        print(f"{ts_str} Call Signal Detected - {option_sym} @ {optionsNew(option_sym)} for {config.SYMBOL} at {history_df['Close'].iloc[-1]}")
        buy_call()
        try:
            await option_live.subscribe(option_sym)
            entry_price = optionsNew(option_sym)
            if entry_price:
                await option_live.set_trailing_stop_loss(
                    option_sym, 
                    entry_price, 
                    tp1_pct=config.TP1_PCT,
                    tp1_size=config.TP1_POSITION_SIZE,
                    tp2_pct=config.TP2_PCT,
                    tp2_size=config.TP2_POSITION_SIZE,
                    trailing_pct=config.TRAILING_SL,
                    hard_stop_pct=config.HARD_SL,
                    max_hold_seconds=config.TIME_LIMIT
                )
        except Exception as e:
            print(f"Failed to subscribe to {option_sym}: {e}")
            
    elif signal == -1:
        option_sym = optionSymbol(signal, history_df["Close"].iloc[-1])
        print(f"{ts_str} Put Signal Detected - {option_sym} @ {optionsNew(option_sym)} for {config.SYMBOL} at {history_df['Close'].iloc[-1]}")
        buy_put()
        try:
            await option_live.subscribe(option_sym)
            entry_price = optionsNew(option_sym)
            if entry_price:
                await option_live.set_trailing_stop_loss(
                    option_sym, 
                    entry_price, 
                    tp1_pct=config.TP1_PCT,
                    tp1_size=config.TP1_POSITION_SIZE,
                    tp2_pct=config.TP2_PCT,
                    tp2_size=config.TP2_POSITION_SIZE,
                    trailing_pct=config.TRAILING_SL,
                    hard_stop_pct=config.HARD_SL,
                    max_hold_seconds=config.TIME_LIMIT
                )
        except Exception as e:
            print(f"Failed to subscribe to {option_sym}: {e}")
    else:
        print(f"{ts_str} No Signal Detected for {config.SYMBOL} at {history_df['Close'].iloc[-1]}")

    return history_df, True


async def main():
    
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


