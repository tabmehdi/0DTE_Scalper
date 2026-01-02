# 0DTE Options Trading Signal Bot

A Python-based automated trading bot that analyzes market data using technical indicators, generates buy/sell signals for 0DTE (zero days to expiration) options

## Features

- **Latest Options Integration**: Latest options price via Alpaca API
- **Technical Indicators**: Hull MA, EMA Cross, Supertrend, MACD, RSI
- **Automated Signal Generation**: Analyzes market data every minute to detect trading opportunities
- **Webhook Integration**: Sends buy/sell signals to RelayDesk

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

## Future Implementation Goal

- **Support for Canadian Broker** : Adding support for a Broker instead of relying on RelayDesk
- **Indicators** : Adding support for more indicators to have better strategies
- **Websocket Implementation** : Adding support for live options quotes for better price tracking
- **Risk Management** : Each position will be protected by three exit mechanisms : Trailing Stop Loss, Hard Stop Loss, Time Constraint

## Disclaimer

**This software is for educational purposes only. Trading options involves substantial risk of loss. Use at your own risk. The authors are not responsible for any financial losses incurred.**
