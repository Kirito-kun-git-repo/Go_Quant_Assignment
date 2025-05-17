# Trade Simulator

A Python-based trading simulator for algorithmic trading strategy development and testing. This simulator provides real-time market data visualization, trade impact calculation, and performance metrics.

## Architecture

```
                                 +----------------+
                                 |                |
                                 |  User Interface|
                                 |  (PySimpleGUI) |
                                 |                |
                                 +--------+-------+
                                          |
                                          | User Input & Display
                                          v
+----------------+    Market Data    +----+-------+    Trade Parameters    +----------------+
|                |----------------->|            |<---------------------|                |
| Market Data    |                  | Application|                       | Configuration  |
| Feed           |                  | Controller |                       | Manager        |
| (WebSocket)    |                  |            |                       |                |
+----------------+                  +----+-------+                       +----------------+
                                          |
                                          | Processing
                                          v
                      +------------------------------------------+
                      |                                          |
                      |              Models                      |
                      |                                          |
          +-----------+-----------+                  +-----------+-----------+
          |                       |                  |                       |
          |    OrderBook          |                  |    Impact Models      |
          |    Management         |                  |                       |
          |                       |                  |                       |
          +-----------+-----------+                  +-----------+-----------+
                      |                                          |
                      |                                          |
          +-----------+-----------+                  +-----------+-----------+
          |                       |                  |                       |
          |    Fee Calculation    |                  |    Maker/Taker        |
          |                       |                  |    Classification     |
          |                       |                  |                       |
          +-----------------------+                  +-----------------------+
```

## Project Structure

```
trade-simulator/
├── src/                    # Source code
│   ├── app.py              # Trading simulator UI
│   ├── benchmark.py        # End-to-end benchmarking
│   ├── data_ingest.py      # WebSocket client for market data
│   ├── generate_report.py  # Benchmark report generator
│   ├── orderbook.py        # OrderBook implementation with volatility tracking
│   ├── benchmark_orderbook.py # OrderBook performance benchmarking
│   └── orderbook_demo.py   # Demo script for OrderBook
├── logs/                   # Log files
│   ├── data_ingest.log     # Application logs
│   └── raw_ticks.log       # Raw market data
├── models/                 # Trained models and model implementations
│   ├── fee.py              # Trading fee calculation
│   ├── slippage.py         # Slippage simulation
│   ├── impact.py           # Almgren-Chriss market impact model
│   └── maker_taker.py      # Maker/taker order classification
├── tests/                  # Test files
│   ├── test_orderbook.py   # Unit tests for OrderBook
│   ├── test_fee.py         # Unit tests for fee module
│   ├── test_slippage.py    # Unit tests for slippage module
│   ├── test_impact.py      # Unit tests for impact module
│   ├── test_maker_taker.py # Unit tests for maker/taker module
│   └── test_integration.py # Integration tests
├── docs/                   # Documentation
│   ├── benchmark_analysis.ipynb # Benchmark analysis notebook
│   ├── slippage_demo.ipynb     # Slippage model demonstration
│   ├── impact_demo.ipynb       # Impact model demonstration
│   └── maker_taker_demo.ipynb  # Maker/taker classification demonstration
├── demo/                   # Demo files
│   ├── live_update.gif     # Demo GIF of the simulator in action
│   └── record_demo.py      # Script to record demo
├── benchmark_charts/       # Benchmark charts
├── venv/                   # Virtual environment
├── requirements.txt        # Dependencies
├── benchmark_results.json  # Benchmark results
├── benchmark_report.pdf    # Benchmark report
└── README.md               # This file
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

3. Run the simulator:
   ```
   python src/app.py
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
- `depth(levels)`: Get the top N levels of the orderbook

### Running the OrderBook Demo

To see the OrderBook in action with real market data:

```
python src/orderbook_demo.py [num_ticks]
```

Where `num_ticks` is the number of ticks to process (default: 100).

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

Fee calculation is based on the following formula:
```
fee_amount = order_value * fee_rate
```

Where `fee_rate` depends on the fee tier and whether the order is a maker or taker.

### Slippage Module

The slippage module simulates market impact by walking through the orderbook:

```python
from models.slippage import simulate_slippage

# Calculate slippage for a $50,000 buy order
slippage = simulate_slippage(50000.0, orderbook, "buy")
print(f"Slippage: ${slippage:.2f}")
```

Slippage is calculated by simulating the execution of an order through the orderbook levels:
1. Start with the best price level
2. Fill as much as possible at that level
3. Move to the next price level
4. Repeat until the order is fully filled
5. Calculate the difference between the executed price and the mid price

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

The Almgren-Chriss model separates market impact into two components:

1. **Permanent Impact**: The lasting effect on the market price after the order is executed.
   ```
   permanent_impact = gamma * sigma * sqrt(Q / V)
   ```

2. **Temporary Impact**: The transient effect during execution that disappears afterward.
   ```
   temporary_impact = epsilon * sigma * (Q / V)
   ```

Where:
- `gamma` and `epsilon` are market impact parameters
- `sigma` is market volatility
- `Q` is order size
- `V` is market volume

### Maker/Taker Classification

The maker_taker module classifies orders as "maker" or "taker" based on orderbook liquidity:

```python
from models.maker_taker import classify_order_heuristic

# Classify a $25,000 buy order
classification = classify_order_heuristic(25000.0, orderbook, "buy")
print(f"Classification: {classification}")
```

The classification uses a heuristic approach:
- If the order size is less than or equal to the best level's size, it's classified as a "maker"
- Otherwise, it's classified as a "taker"

The module also includes an optional machine learning approach using logistic regression.

## Trading Simulator UI

The trading simulator includes a graphical user interface built with PySimpleGUI. The UI allows users to:

- Select trading parameters (exchange, symbol, quantity, etc.)
- View real-time market data (mid price, spread, volatility)
- Calculate and display trade impact metrics (slippage, fees, market impact)
- Classify orders as maker or taker
- Measure and display latency for all operations

To run the UI:

```
python src/app.py
```

The UI includes the following features:

- Real-time market data updates via an asyncio background thread
- Interactive controls for trading parameters
- Live calculation of trading costs and market impact
- Buy and sell order simulation
- Latency measurement and display

## Benchmarking

The simulator includes comprehensive benchmarking tools to measure performance:

### Running the Benchmarks

To run the end-to-end benchmarks:

```
python src/benchmark.py
```

This will:
1. Measure orderbook update latency under different loads
2. Measure trade impact calculation latency
3. Measure end-to-end latency from market data to UI update
4. Generate charts in the `benchmark_charts/` directory
5. Save results to `benchmark_results.json`

### Generating a Benchmark Report

To generate a PDF report from the benchmark results:

```
python src/generate_report.py
```

This will create `benchmark_report.pdf` with charts and analysis.

### Analyzing Benchmarks in Jupyter

To analyze the benchmark results in a Jupyter notebook:

```
jupyter notebook docs/benchmark_analysis.ipynb
```

## Testing

The simulator includes comprehensive unit and integration tests:

### Running Unit Tests

To run the unit tests:

```
pytest tests/test_orderbook.py tests/test_fee.py tests/test_slippage.py tests/test_impact.py tests/test_maker_taker.py -v
```

### Running Integration Tests

To run the integration tests:

```
pytest tests/test_integration.py -v
```

The integration tests verify:
1. Rapid tick ingestion performance
2. Trade impact calculation latency
3. End-to-end workflow from market data to UI update

## Demo

To record a demo of the simulator in action:

```
python demo/record_demo.py
```

This will create a GIF in the `demo/` directory showing the simulator processing real-time market data and calculating trade impact.

## Jupyter Notebooks

The `docs/` directory contains Jupyter notebooks demonstrating the use of the different modules:

- `benchmark_analysis.ipynb`: Analyzes benchmark results
- `slippage_demo.ipynb`: Demonstrates slippage simulation and model fitting
- `impact_demo.ipynb`: Demonstrates the Almgren-Chriss impact model
- `maker_taker_demo.ipynb`: Demonstrates maker/taker classification

To run the notebooks:

```
cd docs/
jupyter notebook
```

## Environment Support

The simulator is designed to work in different environments:

- **Development**: Uses simulated market data with configurable parameters
- **Testing**: Uses predefined test data for reproducible results
- **Production**: Can connect to real exchange APIs via WebSocket

## Future Improvements

Planned improvements for future versions:

1. WebSocket connection to real exchange APIs
2. Historical data replay functionality
3. Enhanced visualization with charts and graphs
4. More sophisticated market impact models
5. Support for different order types (limit, market, etc.)
6. Multi-exchange support
7. Portfolio-level analysis