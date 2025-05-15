#!/usr/bin/env python
"""
Benchmark script for OrderBook update performance.

This script generates synthetic orderbook updates and measures the time
it takes to process them.
"""

import time
import random
import json
import numpy as np
from typing import List, Dict, Any
from orderbook import OrderBook


def generate_synthetic_tick(symbol: str, 
                           base_price: float, 
                           price_volatility: float = 0.01,
                           num_levels: int = 10) -> Dict[str, Any]:
    """
    Generate a synthetic orderbook tick.
    
    Args:
        symbol (str): The trading symbol
        base_price (float): The base price around which to generate levels
        price_volatility (float): The volatility of price changes
        num_levels (int): Number of price levels to generate
        
    Returns:
        dict: A synthetic orderbook tick
    """
    # Generate random price movement
    price_change = random.normalvariate(0, price_volatility)
    new_base_price = base_price * (1 + price_change)
    
    # Generate ask levels (ascending prices)
    asks = []
    for i in range(num_levels):
        price = new_base_price + (i + 1) * random.uniform(0.1, 0.5)
        size = random.uniform(0.1, 10.0)
        asks.append([str(price), str(size)])
    
    # Generate bid levels (descending prices)
    bids = []
    for i in range(num_levels):
        price = new_base_price - (i + 1) * random.uniform(0.1, 0.5)
        size = random.uniform(0.1, 10.0)
        bids.append([str(price), str(size)])
    
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "exchange": "SYNTHETIC",
        "symbol": symbol,
        "asks": asks,
        "bids": bids
    }


def benchmark_updates(num_updates: int = 10000, symbol: str = "BTC-USDT-SWAP") -> float:
    """
    Benchmark the performance of orderbook updates.
    
    Args:
        num_updates (int): Number of updates to process
        symbol (str): Symbol to use for the orderbook
        
    Returns:
        float: Average update time in microseconds
    """
    book = OrderBook(symbol)
    base_price = 50000.0  # Starting price
    
    # Generate initial orderbook state
    initial_tick = generate_synthetic_tick(symbol, base_price)
    book.update_from_tick(initial_tick)
    
    # Measure update time
    start_time = time.perf_counter()
    
    for i in range(num_updates):
        # Update base price based on previous mid price
        if book.mid_price() is not None:
            base_price = book.mid_price()
        
        # Generate and apply update
        tick = generate_synthetic_tick(symbol, base_price)
        book.update_from_tick(tick)
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    avg_update_time = (total_time / num_updates) * 1_000_000  # Convert to microseconds
    
    return avg_update_time


def main():
    """Run the benchmark and print results."""
    print("Starting OrderBook update benchmark...")
    
    # Run benchmark with different numbers of updates
    for num_updates in [100, 500, 1000]:
        avg_time = benchmark_updates(num_updates)
        print(f"Average update time for {num_updates} updates: {avg_time:.2f} microseconds")
    
    print("Benchmark complete.")


if __name__ == "__main__":
    main()