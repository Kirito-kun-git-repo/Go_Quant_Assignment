# Trade Simulator

A Python-based trading simulator for algorithmic trading strategy development and testing.

## Project Structure

```
trade-simulator/
├── src/             # Source code
│   ├── data_ingest.py       # WebSocket client for market data
│   ├── orderbook.py         # OrderBook implementation with volatility tracking
│   ├── benchmark_orderbook.py # Performance benchmarking
│   └── orderbook_demo.py    # Demo script for OrderBook
├── logs/            # Log files
│   ├── data_ingest.log      # Application logs
│   └── raw_ticks.log        # Raw market data
├── models/          # Trained models
├── tests/           # Test files
│   └── test_orderbook.py    # Unit tests for OrderBook
├── docs/            # Documentation
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

## Testing

To run the unit tests:

```
pytest tests/
```

Or to run a specific test file with verbose output:

```
pytest tests/test_orderbook.py -v
```