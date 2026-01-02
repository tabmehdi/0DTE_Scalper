import websockets
import msgpack
import config
import asyncio
import time

class OptionLive:
    def __init__(self):
        self.ws = None
        self.is_connected = False
        self.is_listening = False
        self.connection_lock = asyncio.Lock()
        self.subscribed_symbols = set()
        self.stop_losses = {}
        self.price_callbacks = []
        
    async def connect(self):
        """Establish a WebSocket connection and authenticate."""
        if self.ws is not None and self.is_connected:
            print("WebSocket already connected and authenticated.")
            return
            
        try:
            self.ws = await websockets.connect(config.OPTIONS_URL)
            print("WebSocket connected. Authenticating...")
            
            # Authenticate
            auth_msg = {
                "action": "auth",
                "key": config.ALPACA_KEY,
                "secret": config.ALPACA_SECRET
            }
            await self.ws.send(msgpack.packb(auth_msg))
            
            # Wait for auth response
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
        """Subscribe to a specific option quote."""
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
        
        # Wait a moment for the subscription confirmation
        await asyncio.sleep(0.5)
        self.subscribed_symbols.add(symbol)
        print(f"✓ Subscribed to {symbol}")

    async def unsubscribe(self, symbol):
        """Unsubscribe from a specific option quote."""
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
        
        # Wait a moment for the unsubscription confirmation
        await asyncio.sleep(0.5)
        self.subscribed_symbols.discard(symbol)
        print(f"✓ Unsubscribed from {symbol}")

    async def listen(self):
        """Continuously listen for incoming messages."""
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
                            print(f"Subscription confirmed: {msg}")
                        elif msg_type == "unsubscription":
                            print(f"Unsubscription confirmed: {msg}")
                        elif msg_type == "q":
                            symbol = msg.get("S")
                            bp = msg.get("bp")
                            ap = msg.get("ap")
                            
                            if bp is not None and ap is not None:
                                mid_price = (bp + ap) / 2
                                timestamp = msg.get("t")
                                print(f"[{symbol}] {timestamp} | MID PRICE: {mid_price:.2f}")
                                
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
    
    async def set_trailing_stop_loss(self, symbol, entry_price, stop_pct=0.10, hard_stop_pct=0.15, max_hold_seconds=300):

        self.stop_losses[symbol] = {
            'entry': entry_price,
            'high': entry_price,
            'stop_pct': stop_pct,
            'hard_stop_pct': hard_stop_pct,
            'entry_time': time.time(),
            'max_hold_seconds': max_hold_seconds
        }
        print(f"✓ Stop loss set for {symbol}:")
        print(f"  - Trailing: {stop_pct*100:.1f}% from high")
        print(f"  - Hard stop: {hard_stop_pct*100:.1f}% from entry")
        print(f"  - Time limit: {max_hold_seconds}s")
    
    async def _check_stop_loss(self, symbol, current_price):

        if symbol not in self.stop_losses:
            return
        
        stop_data = self.stop_losses[symbol]

        if current_price > stop_data['high']:
            stop_data['high'] = current_price
        
        # Check time constraint
        elapsed_time = time.time() - stop_data['entry_time']
        if elapsed_time >= stop_data['max_hold_seconds']:
            profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
            print(f"\n TIME LIMIT REACHED for {symbol}")
            print(f"   Held for: {elapsed_time:.0f}s (max: {stop_data['max_hold_seconds']}s)")
            print(f"   Entry: ${stop_data['entry']:.2f}")
            print(f"   Current: ${current_price:.2f}")
            print(f"   Profit/Loss: {profit_pct:+.2f}%")
            print(f"   {symbol} SOLD\n")
            
            del self.stop_losses[symbol]
            await self.unsubscribe(symbol)
            return
        
        # Check hard stop loss (from entry)
        hard_stop_price = stop_data['entry'] * (1 - stop_data['hard_stop_pct'])
        if current_price <= hard_stop_price:
            profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
            print(f"\n HARD STOP LOSS TRIGGERED for {symbol}")
            print(f"   Entry: ${stop_data['entry']:.2f}")
            print(f"   Hard Stop: ${hard_stop_price:.2f}")
            print(f"   Current: ${current_price:.2f}")
            print(f"   Loss: {profit_pct:+.2f}%")
            print(f"   {symbol} SOLD\n")
            
            del self.stop_losses[symbol]
            await self.unsubscribe(symbol)
            return
        
        # Check trailing stop loss (from high)
        trailing_stop_price = stop_data['high'] * (1 - stop_data['stop_pct'])
        if current_price <= trailing_stop_price:
            profit_pct = ((current_price - stop_data['entry']) / stop_data['entry']) * 100
            print(f"\n TRAILING STOP TRIGGERED for {symbol}")
            print(f"   Entry: ${stop_data['entry']:.2f}")
            print(f"   High: ${stop_data['high']:.2f}")
            print(f"   Current: ${current_price:.2f}")
            print(f"   Profit/Loss: {profit_pct:+.2f}%")
            print(f"   {symbol} SOLD\n")
            
            del self.stop_losses[symbol]
            await self.unsubscribe(symbol)
            return
    
    def stop_listening(self):
        """Stop the listening loop."""
        self.is_listening = False
        print("Stopping listener...")
        
    async def disconnect(self):
        """Close the WebSocket connection."""
        self.stop_listening()
        if self.ws:
            await self.ws.close()
            self.ws = None
        self.is_connected = False
        self.subscribed_symbols.clear()
        print("Disconnected.")

    async def run(self):
        """Run the WebSocket connection and listener."""
        await self.connect()
        await self.listen()

