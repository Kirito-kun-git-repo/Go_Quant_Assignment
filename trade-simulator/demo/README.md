# Trading Simulator Demo

This directory contains a demonstration of the trading simulator application.

## Live Update Demo

The `live_update.gif` shows the trading simulator in action, demonstrating:

1. Real-time orderbook updates
2. Dynamic calculation of slippage, fees, and market impact
3. Maker/taker classification
4. Performance metrics (latency measurements)

## How to Use the Simulator

1. Select an exchange and trading pair
2. Enter the order quantity in USD
3. Choose your fee tier
4. Click "Start Feed" to begin receiving market data
5. Click "Buy" or "Sell" to simulate a trade and see the impact

## Key Features

- **Real-time Updates**: The simulator updates with each new tick from the market data feed
- **Comprehensive Metrics**: Shows slippage, fees, market impact, and net cost
- **Performance Monitoring**: Tracks latency for each calculation
- **Order Classification**: Automatically determines if an order would be a maker or taker

## Implementation Details

The simulator integrates several models:
- Orderbook management
- Slippage calculation
- Fee computation
- Almgren-Chriss market impact model
- Maker/taker classification

All calculations happen in real-time as market data is received or when user inputs change.