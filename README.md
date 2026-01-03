# 0DTE Options Trading Signal Bot

A Python-based automated trading bot that analyzes market data using technical indicators, generates buy/sell signals for 0DTE (zero days to expiration) options, locally tracks orders and manages exits

## Features

- **Live Options Price Tracking** : Live options data via Alpaca WebSocket
- **Technical Indicators**: Hull MA, EMA Cross, Supertrend, MACD, RSI
- **Automated Signal Generation**: Analyzes market data every minute to detect trading opportunities
- **Webhook Integration**: Sends buy/sell signals to RelayDesk
- **Local Order Tracking and Risk Management**: Keeps track of the prices of a bought options and manages risk and exits locally

## Project Structure

```
0DTE_Scalper/
├── broker/
│   └── order.py             # Webhook order execution
├── data/
│   ├── optionsInfo.py       # Options data fetching
│   ├── optionsLive.py       # Live options price for tracking order
│   └── tickerInfo.py        # Stock bar data fetching
├── strategies/
│   ├── indicators.py        # Technical indicators
│   └── signal.py            # Generates Signal (Create this file)
├── config.py                # Configuration
├── main.py                  # Production entry point
└── requirements.txt         # Python dependencies
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/0DTE_Scalper.git
cd 0DTE_Scalper
```

### 2. Install Dependencies

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## API Requirements

- **Alpaca Markets API/WebSocket**: For live and historical market data
  - Sign up at [alpaca.markets](https://alpaca.markets)
  - Get API key and secret
- **Webhook Service**: For RelayDesk integration, requires 2 webhooks, one for calls and one for puts

## Usage

### Configuration

Edit `config.py` to customize:

- **Trading Symbol**: `SYMBOL = "SPY"`
- **Trading Hours**: `START` and `END` times
- **Indicator Parameters**: EMA, HMA, Supertrend, MACD, RSI settings
- **Risk Management Parameters**: `TRAILING_SL`, `HARD_SL` and `TIMELIMIT`

Create `calculateSignal()` in `strategies/signal.py`

- You can use the available indicators in `indicators.py` or use your own strategy
- Return -1 to buy a put, 1 for a call or 0 for nothing

### Run the Trading Bot

```bash
python main.py
```

The bot will:
1. Connect to Alpaca API and WebSocket
2. Load historical data
3. Analyze the market every minute
4. Generate buy/sell signals based on implemented strategy
5. Send webhook orders when signals trigger
6. Track order price 
7. Exits according to risk management strategy

Create `calculateSignal()` in `strategies/signal.py`

- You can use the available indicators in `indicators.py` or use your own strategy
- Return -1 to buy a put, 1 for a call or 0 for nothing
  
## Technical Indicators

The bot provdes multiple indicators to generate signals:

1. **Hull Moving Average (HMA)**: Trend direction
2. **EMA Cross**: Short/long crossover signals
3. **Supertrend**: Trend-following indicator
4. **MACD**: Momentum and trend strength
5. **RSI**: Overbought/oversold conditions

Signals are aggregated using `calculateSignal()`.

## Exit Strategy & Risk Management

Each position is managed using four exit mechanisms designed specifically for 0DTE options trading:

1. **Two Take-Profit Targets**: Exits the position with a certain percentage of contracts the moments it reaches desired profits
2. **Hard Stop Loss**: Immediately exits a trade when a fixed loss threshold is hit to prevent outsized losses.
3. **Trailing Stop Loss (Post-Profit Activation)**: Activates after the Take-Profits. Tracks the highest price reached after entry and closes the remaining position if price retraces by a configurable percentage.
4. **Time-Based Exit**: Forces exit at configured end-of-day time to avoid overnight exposure for 0DTE trades.


## Future Implementation Goal

- **Support for Canadian Broker**: The framework for the buy and exits signals exists already so adding support for a Broker instead of relying on RelayDesk would make this bot fully autonomous.
- **More Indicators**: Adding support for more indicators to have better strategies

## Disclaimer

**This software is for educational purposes only. Trading options involves substantial risk of loss. Use at your own risk. The authors are not responsible for any financial losses incurred.**
