# 0DTE Options Trading Signal Bot

A Python-based automated trading bot that analyzes market data using technical indicators, generates buy/sell signals for 0DTE (zero days to expiration) options

## Features

- **Live Options Data** : Live options data via Alpaca WebSocket
- **Technical Indicators**: Hull MA, EMA Cross, Supertrend, MACD, RSI
- **Automated Signal Generation**: Analyzes market data every minute to detect trading opportunities
- **Webhook Integration**: Sends buy/sell signals to RelayDesk
- **Order Tracking and Risk Management**: Keeps track of the prices of a bought options and manages risk and exits

## Project Structure

```
0DTE_Scalper/
├── broker/
│   └── order.py             # Webhook order execution
├── data/
│   ├── optionsInfo.py       # Options data fetching
│   └── tickerInfo.py        # Stock bar data fetching
├── strategies/
│   ├── indicators.py        # Technical indicators
│   └── signal.py            # Generates Signal
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

## Usage

### Run the Trading Bot

```bash
python main.py
```

The bot will:
1. Connect to Alpaca WebSocket
2. Load historical data
3. Analyze the market every minute
4. Generate buy/sell signals based on indicators
5. Send webhook orders when signals trigger

### Configuration

Edit `config.py` to customize:

- **Trading Symbol**: `SYMBOL = "SPY"`
- **Trading Hours**: `START` and `END` times
- **Indicator Parameters**: EMA, HMA, Supertrend, MACD, RSI settings

Create `calculateSignal()` in `strategies/signal.py`

- You can use the available indicators in `indicators.py` or use your own strategy
- Return -1 to buy a put, 1 for a call or 0 for nothing

## Technical Indicators

The bot combines multiple indicators to generate signals:

1. **Hull Moving Average (HMA)**: Trend direction
2. **EMA Cross**: Short/long crossover signals
3. **Supertrend**: Trend-following indicator
4. **MACD**: Momentum and trend strength
5. **RSI**: Overbought/oversold conditions

Signals are aggregated using `calculateSignal()` with a lookback period.

## API Requirements

- **Alpaca Markets API**: For live and historical market data
  - Sign up at [alpaca.markets](https://alpaca.markets)
  - Get API key and secret
- **Webhook Service**: For RelayDesk integration

## Risk Management

Each position will be protected by three exit mechanisms 

1. **Trailing Stop Loss**: Automatically closes the position if the price drops by a percentage below the highest price reached
2. **Hard Stop Loss**: Sets a fixed maximum loss limit to prevent catastrophic losses on a single trade
3. **Time Constraint**: Automatically exits the position at the end of trading hours to avoid overnight risk exposure


## Future Implementation Goal

- **Support for Canadian Broker**: Adding support for a Broker instead of relying on RelayDesk
- **Indicators**: Adding support for more indicators to have better strategies

## Disclaimer

**This software is for educational purposes only. Trading options involves substantial risk of loss. Use at your own risk. The authors are not responsible for any financial losses incurred.**
