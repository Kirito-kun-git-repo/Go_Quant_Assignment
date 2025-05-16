# Trade Simulator

A Python-based trading simulator for algorithmic trading strategy development and testing.

## Project Structure

```
trade-simulator/
├── src/             # Source code
│   ├── app.py               # Trading simulator UI
│   ├── data_ingest.py       # WebSocket client for market data
│   ├── orderbook.py         # OrderBook implementation with volatility tracking
│   ├── benchmark_orderbook.py # Performance benchmarking
│   └── orderbook_demo.py    # Demo script for OrderBook
├── logs/            # Log files
│   ├── data_ingest.log      # Application logs
│   └── raw_ticks.log        # Raw market data
├── models/          # Trained models and model implementations
│   ├── fee.py              # Trading fee calculation
│   ├── slippage.py         # Slippage simulation
│   ├── impact.py           # Almgren-Chriss market impact model
│   └── maker_taker.py      # Maker/taker order classification
├── tests/           # Test files
│   ├── test_orderbook.py    # Unit tests for OrderBook
│   ├── test_fee.py          # Unit tests for fee module
│   ├── test_slippage.py     # Unit tests for slippage module
│   ├── test_impact.py       # Unit tests for impact module
│   └── test_maker_taker.py  # Unit tests for maker/taker module
├── docs/            # Documentation
│   ├── slippage_demo.ipynb  # Slippage model demonstration
│   ├── impact_demo.ipynb    # Impact model demonstration
│   └── maker_taker_demo.ipynb # Maker/taker classification demonstration
├── venv/            # Virtual environment
├── requirements.txt # Dependencies
└── README.md        # This file
```

## Setup

1. Create a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Data Ingestion

The data ingestion module connects to a WebSocket endpoint to receive real-time market data for BTC-USDT-SWAP from OKX.

To run the data ingestion:
```
python src/data_ingest.py
```

This will start collecting L2 orderbook data and save it to `logs/raw_ticks.log`.

## OrderBook Management

The OrderBook class maintains a sorted list of bids and asks, and provides methods for calculating market metrics:

- `update_from_tick(tick)`: Update the orderbook with a new tick
- `best_bid()`, `best_ask()`: Get the best bid and ask prices
- `mid_price()`: Calculate the mid price
- `spread()`: Calculate the spread between best ask and best bid
- `rolling_volatility()`: Calculate the rolling volatility based on mid price history

### Running the OrderBook Demo

To see the OrderBook in action with real market data:

```
python src/orderbook_demo.py [num_ticks]
```

Where `num_ticks` is the number of ticks to process (default: 100).

### Running the Benchmark

To benchmark the performance of the OrderBook implementation:

```
python src/benchmark_orderbook.py
```

This will measure the average update time for different numbers of synthetic updates.

## Market Impact and Trading Costs

The simulator includes several modules for modeling market impact and trading costs:

### Fee Module

The fee module calculates trading fees based on OKX fee tiers:

```python
from models.fee import compute_fee

# Calculate fee for a $10,000 order at VIP0 tier
fee = compute_fee(10000.0, 50000.0, "VIP0", is_taker=True)
print(f"Fee: ${fee:.2f}")
```

### Slippage Module

The slippage module simulates market impact by walking through the orderbook:

```python
from models.slippage import simulate_slippage

# Calculate slippage for a $50,000 buy order
slippage = simulate_slippage(50000.0, orderbook, "buy")
print(f"Slippage: ${slippage:.2f}")
```

### Almgren-Chriss Impact Model

The impact module implements the Almgren-Chriss market impact model:

```python
from models.impact import calculate_total_impact

# Calculate impact for a 1.0 BTC order
perm, temp, total = calculate_total_impact(orderbook, 1.0)
print(f"Permanent impact: ${perm:.2f}")
print(f"Temporary impact: ${temp:.2f}")
print(f"Total impact: ${total:.2f}")
```

### Maker/Taker Classification

The maker_taker module classifies orders as "maker" or "taker" based on orderbook liquidity:

```python
from models.maker_taker import classify_order_heuristic

# Classify a $25,000 buy order
classification = classify_order_heuristic(25000.0, orderbook, "buy")
print(f"Classification: {classification}")
```

## Trading Simulator UI

The trading simulator includes a graphical user interface built with PySimpleGUI. The UI allows users to:

- Select trading parameters (exchange, symbol, quantity, etc.)
- View real-time market data (mid price, spread, volatility)
- Calculate and display trade impact metrics (slippage, fees, market impact)
- Classify orders as maker or taker

To run the UI:

```
python src/app.py
```

The UI includes the following features:

- Real-time market data updates via an asyncio background thread
- Interactive controls for trading parameters
- Live calculation of trading costs and market impact
- Buy and sell order simulation

## Jupyter Notebooks

The `docs/` directory contains Jupyter notebooks demonstrating the use of the different modules:

- `slippage_demo.ipynb`: Demonstrates slippage simulation and model fitting
- `impact_demo.ipynb`: Demonstrates the Almgren-Chriss impact model
- `maker_taker_demo.ipynb`: Demonstrates maker/taker classification

To run the notebooks:

```
cd docs/
jupyter notebook
```

## Testing

To run the unit tests:

```
pytest tests/
```

Or to run a specific test file with verbose output:

```
pytest tests/test_orderbook.py -v
```