import websockets
import msgpack
import config
import asyncio
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

class OptionLive:
    def __init__(self):
        self.ws = None
        self.is_connected = False
        self.is_listening = False
        self.connection_lock = asyncio.Lock()
        self.subscribed_symbols = set()
        self.stop_losses = {}
        self.price_callbacks = []
        self.position_states = {}
        
    async def connect(self):
        if self.ws is not None and self.is_connected:
            print("WebSocket already connected and authenticated.")
            return
            
        try:
            self.ws = await websockets.connect(config.OPTIONS_URL)
            print("WebSocket connected. Authenticating...")

            auth_msg = {
                "action": "auth",
                "key": config.ALPACA_KEY,
                "secret": config.ALPACA_SECRET
            }
            await self.ws.send(msgpack.packb(auth_msg))
            
            response = msgpack.unpackb(await self.ws.recv(), raw=False)
            
            if response and response[0].get("T") == "success":
                self.is_connected = True
                print("✓ WebSocket authenticated successfully.")
            else:
                raise ConnectionError("Authentication failed. Check your API credentials.")
        except Exception as e:
            print(f"Connection error: {e}")
            self.is_connected = False
            raise

    async def subscribe(self, symbol):
        if not self.is_connected:
            await self.connect()
            
        if symbol in self.subscribed_symbols:
            print(f"Already subscribed to {symbol}")
            return
            
        sub_msg = {
            "action": "subscribe",
            "quotes": [symbol]
        }
        await self.ws.send(msgpack.packb(sub_msg))
        print(f"→ Subscribing to {symbol}...")
        
        await asyncio.sleep(0.5)
        self.subscribed_symbols.add(symbol)
        print(f"✓ Subscribed to {symbol}")

    async def unsubscribe(self, symbol):
        if not self.is_connected:
            print("WebSocket not connected. Cannot unsubscribe.")
            return
            
        if symbol not in self.subscribed_symbols:
            print(f"Not subscribed to {symbol}")
            return
            
        unsub_msg = {
            "action": "unsubscribe",
            "quotes": [symbol]
        }
        await self.ws.send(msgpack.packb(unsub_msg))
        print(f"→ Unsubscribing from {symbol}...")

        await asyncio.sleep(0.5)
        self.subscribed_symbols.discard(symbol)
        print(f"✓ Unsubscribed from {symbol}")

    async def listen(self):
        if not self.is_connected:
            print("Cannot listen - not connected.")
            return
            
        self.is_listening = True
        
        try:
            while self.is_listening:
                try:
                    raw_msg = await self.ws.recv()
                    msgs = msgpack.unpackb(raw_msg, raw=False)
                    
                    for msg in msgs:
                        msg_type = msg.get("T")
                        
                        if msg_type == "subscription":
                            print(f"Subscription confirmed")
                        elif msg_type == "unsubscription":
                            print(f"Unsubscription confirmed")
                        elif msg_type == "q":
                            symbol = msg.get("S")
                            bp = msg.get("bp")
                            ap = msg.get("ap")
                            
                            if bp is not None and ap is not None:
                                mid_price = (bp + ap) / 2
                                timestamp = msg.get("t")

                                dt = datetime.fromtimestamp(timestamp.seconds + timestamp.nanoseconds / 1e9,tz=timezone.utc)
                                dt_eastern = dt.astimezone(ZoneInfo('America/New_York'))
                                print(f"[{symbol}] {dt_eastern.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ET | MID PRICE: {mid_price:.2f}")
                                
                                await self._check_stop_loss(symbol, mid_price)
                                
                                for callback in self.price_callbacks:
                                    try:
                                        await callback(symbol, mid_price, timestamp)
                                    except Exception as e:
                                        print(f"Callback error: {e}")
                        elif msg_type == "error":
                            print(f"Error received: {msg}")
                            
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"Connection closed: {e}")
                    self.is_connected = False
                    self.is_listening = False
                    break
                except Exception as e:
                    print(f"Error while listening: {e}")
                    
        except Exception as e:
            print(f"Listen error: {e}")
            self.is_listening = False
    
    async def set_trailing_stop_loss(self, symbol, entry_price, tp1_pct=0.15, tp1_size=0.33, tp2_pct=0.25, tp2_size=0.33, trailing_pct=0.20, hard_stop_pct=0.15, max_hold_seconds=300):
        """Set up 2-level TP risk management with trailing stop after TP2.
        
        Args:
            symbol: Option symbol
            entry_price: Entry price
            tp1_pct: Take profit 1 percentage
            tp1_size: Position size to close at TP1 (0-1)
            tp2_pct: Take profit 2 percentage
            tp2_size: Position size to close at TP2 (0-1)
            trailing_pct: Trailing stop percentage (active after TP2)
            hard_stop_pct: Hard stop loss percentage (moves to breakeven after TP1)
            max_hold_seconds: Maximum hold time
        """
        self.stop_losses[symbol] = {
            'entry': entry_price,
            'high': entry_price,
            'tp1_pct': tp1_pct,
            'tp1_size': tp1_size,
            'tp2_pct': tp2_pct,
            'tp2_size': tp2_size,
            'trailing_pct': trailing_pct,
            'hard_stop_pct': hard_stop_pct,
            'entry_time': time.time(),
            'max_hold_seconds': max_hold_seconds,
            'stop_at_breakeven': False 
        }
        
        remaining_size = 1.0 - tp1_size - tp2_size
        
        self.position_states[symbol] = {
            'tp1_active': True,
            'tp2_active': True,
            'trailing_active': True
        }
        
        print(f"2-Level TP risk management set for {symbol}:")
        print(f"   Entry Price: ${entry_price:.2f}")
        print(f"   TP1: +{tp1_pct*100:.1f}% closes {tp1_size*100:.0f}% → moves SL to breakeven")
        print(f"   TP2: +{tp2_pct*100:.1f}% closes {tp2_size*100:.0f}% → activates trailing")
        print(f"   Trailing: {remaining_size*100:.0f}% at -{trailing_pct*100:.1f}% from high (after TP2)")
        print(f"   Initial Hard SL: -{hard_stop_pct*100:.1f}%")
        print(f"   Time limit: {max_hold_seconds}s")
    
    async def _check_stop_loss(self, symbol, current_price):
        if symbol not in self.stop_losses:
            return
        
        stop_data = self.stop_losses[symbol]
        position_state = self.position_states.get(symbol, {})

        if current_price > stop_data['high']:
            stop_data['high'] = current_price
        
        elapsed_time = time.time() - stop_data['entry_time']
        if elapsed_time >= stop_data['max_hold_seconds']:
            profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
            remaining_portions = []
            if position_state.get('tp1_active'):
                remaining_portions.append(f"{stop_data['tp1_size']*100:.0f}% (TP1 portion)")
            if position_state.get('tp2_active'):
                remaining_portions.append(f"{stop_data['tp2_size']*100:.0f}% (TP2 portion)")
            if position_state.get('trailing_active'):
                trailing_size = 1.0 - stop_data['tp1_size'] - stop_data['tp2_size']
                remaining_portions.append(f"{trailing_size*100:.0f}% (trailing portion)")
            
            print(f"\n⏰ TIME LIMIT REACHED for {symbol}")
            print(f"   Held for: {elapsed_time:.0f}s (max: {stop_data['max_hold_seconds']}s)")
            print(f"   Entry: ${stop_data['entry']:.2f}")
            print(f"   Current: ${current_price:.2f}")
            print(f"   Profit/Loss: {profit_pct:+.2f}%")
            print(f"   Closing remaining: {', '.join(remaining_portions)}")
            print(f"   {symbol} FULLY CLOSED\n")
            
            del self.stop_losses[symbol]
            del self.position_states[symbol]
            await self.unsubscribe(symbol)
            return

        if position_state.get('tp1_active'):
            tp1_price = stop_data['entry'] * (1 + stop_data['tp1_pct'])
            if current_price >= tp1_price:
                profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
                print(f"\nTP1 HIT for {symbol}")
                print(f"   Entry: ${stop_data['entry']:.2f}")
                print(f"   TP1 Target: ${tp1_price:.2f}")
                print(f"   Current: ${current_price:.2f}")
                print(f"   Profit: {profit_pct:+.2f}%")
                print(f"   Closing {stop_data['tp1_size']*100:.0f}% of position")
                print(f"   🔒 STOP LOSS MOVED TO BREAKEVEN")
                
                remaining_size = 1.0 - stop_data['tp1_size']
                print(f"   Remaining {remaining_size*100:.0f}%: TP2 @ +{stop_data['tp2_pct']*100:.1f}% and trailing\n")
                
                position_state['tp1_active'] = False
                stop_data['stop_at_breakeven'] = True
                
                if not position_state.get('tp2_active') and not position_state.get('trailing_active'):
                    del self.stop_losses[symbol]
                    del self.position_states[symbol]
                    await self.unsubscribe(symbol)
                return
        
        if position_state.get('tp2_active'):
            tp2_price = stop_data['entry'] * (1 + stop_data['tp2_pct'])
            if current_price >= tp2_price:
                profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
                trailing_size = 1.0 - stop_data['tp1_size'] - stop_data['tp2_size']
                print(f"\nTP2 HIT for {symbol}")
                print(f"   Entry: ${stop_data['entry']:.2f}")
                print(f"   TP2 Target: ${tp2_price:.2f}")
                print(f"   Current: ${current_price:.2f}")
                print(f"   Profit: {profit_pct:+.2f}%")
                print(f"   Closing {stop_data['tp2_size']*100:.0f}% of position")
                print(f"   🚀 TRAILING STOP NOW ACTIVE for remaining {trailing_size*100:.0f}%\n")
                
                position_state['tp2_active'] = False
                
                if not position_state.get('trailing_active'):
                    del self.stop_losses[symbol]
                    del self.position_states[symbol]
                    await self.unsubscribe(symbol)
                return

        if position_state.get('tp1_active') or position_state.get('tp2_active'):
            if stop_data['stop_at_breakeven']:
                stop_price = stop_data['entry']
                if current_price <= stop_price:
                    remaining_portions = []
                    if position_state.get('tp1_active'):
                        remaining_portions.append(f"{stop_data['tp1_size']*100:.0f}% (TP1)")
                    if position_state.get('tp2_active'):
                        remaining_portions.append(f"{stop_data['tp2_size']*100:.0f}% (TP2)")
                    if position_state.get('trailing_active'):
                        trailing_size = 1.0 - stop_data['tp1_size'] - stop_data['tp2_size']
                        remaining_portions.append(f"{trailing_size*100:.0f}% (trailing)")
                    
                    profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
                    print(f"\nBREAKEVEN STOP TRIGGERED for {symbol}")
                    print(f"   Entry/Stop: ${stop_data['entry']:.2f}")
                    print(f"   Current: ${current_price:.2f}")
                    print(f"   Profit/Loss: {profit_pct:+.2f}%")
                    print(f"   Closing remaining: {', '.join(remaining_portions)}")
                    print(f"   {symbol} FULLY CLOSED\n")
                    
                    del self.stop_losses[symbol]
                    del self.position_states[symbol]
                    await self.unsubscribe(symbol)
                    return
            else:
                hard_stop_price = stop_data['entry'] * (1 - stop_data['hard_stop_pct'])
                if current_price <= hard_stop_price:
                    profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
                    print(f"\nHARD STOP LOSS TRIGGERED for {symbol}")
                    print(f"   Entry: ${stop_data['entry']:.2f}")
                    print(f"   Hard Stop: ${hard_stop_price:.2f}")
                    print(f"   Current: ${current_price:.2f}")
                    print(f"   Loss: {profit_pct:+.2f}%")
                    print(f"   {symbol} FULLY CLOSED (before TP1)\n")
                    
                    del self.stop_losses[symbol]
                    del self.position_states[symbol]
                    await self.unsubscribe(symbol)
                    return

        if position_state.get('trailing_active') and not position_state.get('tp2_active'):
            trailing_stop_price = stop_data['high'] * (1 - stop_data['trailing_pct'])
            if current_price <= trailing_stop_price:
                trailing_size = 1.0 - stop_data['tp1_size'] - stop_data['tp2_size']
                profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
                print(f"\nTRAILING STOP TRIGGERED for {symbol}")
                print(f"   Entry: ${stop_data['entry']:.2f}")
                print(f"   High: ${stop_data['high']:.2f}")
                print(f"   Trailing Stop: ${trailing_stop_price:.2f}")
                print(f"   Current: ${current_price:.2f}")
                print(f"   Profit/Loss: {profit_pct:+.2f}%")
                print(f"   Closing final {trailing_size*100:.0f}% trailing portion")
                print(f"   {symbol} FULLY CLOSED\n")
                
                position_state['trailing_active'] = False
                del self.stop_losses[symbol]
                del self.position_states[symbol]
                await self.unsubscribe(symbol)
                return
    
    def stop_listening(self):
        self.is_listening = False
        print("Stopping listener...")
        
    async def disconnect(self):
        self.stop_listening()
        if self.ws:
            await self.ws.close()
            self.ws = None
        self.is_connected = False
        self.subscribed_symbols.clear()
        print("Disconnected.")

    async def run(self):
        await self.connect()
        await self.listen()

