#!/usr/bin/env python
"""
Benchmarking Script for Trading Simulator

This script measures the end-to-end latency of the trading simulator
under different load conditions and generates performance charts.
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Tuple

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.orderbook import OrderBook
from models.slippage import simulate_slippage
from models.fee import compute_fee
from models.impact import calculate_total_impact
from models.maker_taker import classify_order_heuristic


def generate_synthetic_tick(base_price: float, volatility: float, symbol: str) -> Dict[str, Any]:
    """
    Generate a synthetic market data tick.
    
    Args:
        base_price (float): The base price for the symbol
        volatility (float): The price volatility
        symbol (str): The trading symbol
        
    Returns:
        dict: A synthetic market data tick
    """
    # Generate a random price movement
    price_change = np.random.normal(0, volatility)
    current_price = base_price + price_change
    
    # Generate orderbook levels with increasing spread
    asks = []
    bids = []
    
    for i in range(10):
        # Spread increases as we move away from mid price
        level_spread = volatility * 0.01 * (1 + 0.5 * i * i)
        
        # Price levels
        ask_price = current_price + level_spread * (i + 1)
        bid_price = current_price - level_spread * (i + 1)
        
        # Size decreases as we move away from mid price
        base_size = 1.0
        size_factor = 1.0 / (1 + 0.2 * i)
        
        ask_size = base_size * size_factor * (1 + 0.1 * np.random.random())
        bid_size = base_size * size_factor * (1 + 0.1 * np.random.random())
        
        asks.append([str(ask_price), str(ask_size)])
        bids.append([str(bid_price), str(bid_size)])
    
    # Create the tick
    tick = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        "exchange": "OKX",
        "symbol": symbol,
        "asks": asks,
        "bids": bids
    }
    
    return tick


def benchmark_orderbook_updates(num_updates: int, symbol: str = "BTC-USDT-SWAP") -> Dict[str, float]:
    """
    Benchmark orderbook updates.
    
    Args:
        num_updates (int): Number of updates to perform
        symbol (str): The trading symbol
        
    Returns:
        dict: Benchmark results
    """
    # Create an orderbook
    book = OrderBook(symbol)
    
    # Initialize parameters
    base_price = 50000.0
    volatility = 50.0
    
    # Warm up the orderbook with some initial data
    for _ in range(20):
        tick = generate_synthetic_tick(base_price, volatility, symbol)
        book.update_from_tick(tick)
    
    # Measure update time
    start_time = time.time()
    
    for _ in range(num_updates):
        tick = generate_synthetic_tick(base_price, volatility, symbol)
        book.update_from_tick(tick)
    
    end_time = time.time()
    
    # Calculate results
    total_time = end_time - start_time
    avg_time = total_time / num_updates * 1000  # in milliseconds
    
    return {
        "num_updates": num_updates,
        "total_time_ms": total_time * 1000,
        "avg_time_ms": avg_time
    }


def benchmark_trade_impact(num_calculations: int, orderbook: OrderBook) -> Dict[str, float]:
    """
    Benchmark trade impact calculations.
    
    Args:
        num_calculations (int): Number of calculations to perform
        orderbook (OrderBook): The orderbook to use
        
    Returns:
        dict: Benchmark results
    """
    # Generate order sizes
    order_sizes = np.linspace(100, 10000, num_calculations)
    
    # Measure calculation time
    start_time = time.time()
    
    for i in range(num_calculations):
        # Calculate slippage
        slippage_start = time.time()
        slippage = simulate_slippage(order_sizes[i], orderbook, "buy")
        slippage_time = (time.time() - slippage_start) * 1000  # in milliseconds
        
        # Calculate fee
        fee_start = time.time()
        fee = compute_fee(order_sizes[i], orderbook.mid_price(), "VIP0", is_taker=True)
        fee_time = (time.time() - fee_start) * 1000  # in milliseconds
        
        # Calculate market impact
        impact_start = time.time()
        try:
            base_qty = order_sizes[i] / orderbook.mid_price()
            perm_impact, temp_impact, total_impact = calculate_total_impact(orderbook, base_qty)
        except (ValueError, TypeError):
            perm_impact, temp_impact, total_impact = 0, 0, 0
        impact_time = (time.time() - impact_start) * 1000  # in milliseconds
        
        # Classify order
        class_start = time.time()
        classification = classify_order_heuristic(order_sizes[i], orderbook, "buy")
        class_time = (time.time() - class_start) * 1000  # in milliseconds
    
    end_time = time.time()
    
    # Calculate results
    total_time = end_time - start_time
    avg_time = total_time / num_calculations * 1000  # in milliseconds
    
    return {
        "num_calculations": num_calculations,
        "total_time_ms": total_time * 1000,
        "avg_time_ms": avg_time
    }


def benchmark_end_to_end(num_iterations: int, symbol: str = "BTC-USDT-SWAP") -> Dict[str, Any]:
    """
    Benchmark end-to-end processing from market data to trade impact.
    
    Args:
        num_iterations (int): Number of iterations to perform
        symbol (str): The trading symbol
        
    Returns:
        dict: Benchmark results
    """
    # Create an orderbook
    book = OrderBook(symbol)
    
    # Initialize parameters
    base_price = 50000.0
    volatility = 50.0
    order_size = 1000.0
    
    # Warm up the orderbook with some initial data
    for _ in range(20):
        tick = generate_synthetic_tick(base_price, volatility, symbol)
        book.update_from_tick(tick)
    
    # Measure end-to-end latency
    latencies = []
    
    for _ in range(num_iterations):
        # Generate a tick
        tick = generate_synthetic_tick(base_price, volatility, symbol)
        
        # Measure end-to-end processing time
        start_time = time.time()
        
        # Update the orderbook
        book.update_from_tick(tick)
        
        # Calculate slippage
        slippage = simulate_slippage(order_size, book, "buy")
        
        # Calculate fee
        fee = compute_fee(order_size, book.mid_price(), "VIP0", is_taker=True)
        
        # Calculate market impact
        try:
            base_qty = order_size / book.mid_price()
            perm_impact, temp_impact, total_impact = calculate_total_impact(book, base_qty)
        except (ValueError, TypeError):
            perm_impact, temp_impact, total_impact = 0, 0, 0
        
        # Classify order
        classification = classify_order_heuristic(order_size, book, "buy")
        
        # Calculate net cost
        net_cost = slippage + fee + temp_impact
        
        # Record latency
        latency = (time.time() - start_time) * 1000  # in milliseconds
        latencies.append(latency)
    
    # Calculate results
    latencies = np.array(latencies)
    
    return {
        "num_iterations": num_iterations,
        "min_latency_ms": np.min(latencies),
        "max_latency_ms": np.max(latencies),
        "avg_latency_ms": np.mean(latencies),
        "median_latency_ms": np.median(latencies),
        "p95_latency_ms": np.percentile(latencies, 95),
        "p99_latency_ms": np.percentile(latencies, 99),
        "latencies_ms": latencies.tolist()
    }


def run_benchmarks() -> Dict[str, Any]:
    """
    Run all benchmarks and return the results.
    
    Returns:
        dict: All benchmark results
    """
    print("Running benchmarks...")
    
    # Benchmark orderbook updates with different loads
    print("Benchmarking orderbook updates...")
    update_loads = [10, 50, 100, 500, 1000]
    update_results = []
    
    for load in update_loads:
        print(f"  Running with {load} updates...")
        result = benchmark_orderbook_updates(load)
        update_results.append(result)
        print(f"  Average time: {result['avg_time_ms']:.2f}ms")
    
    # Create an orderbook for trade impact benchmarks
    book = OrderBook("BTC-USDT-SWAP")
    base_price = 50000.0
    volatility = 50.0
    
    # Warm up the orderbook with some initial data
    for _ in range(20):
        tick = generate_synthetic_tick(base_price, volatility, "BTC-USDT-SWAP")
        book.update_from_tick(tick)
    
    # Benchmark trade impact calculations with different loads
    print("Benchmarking trade impact calculations...")
    impact_loads = [10, 50, 100, 500, 1000]
    impact_results = []
    
    for load in impact_loads:
        print(f"  Running with {load} calculations...")
        result = benchmark_trade_impact(load, book)
        impact_results.append(result)
        print(f"  Average time: {result['avg_time_ms']:.2f}ms")
    
    # Benchmark end-to-end processing with different loads
    print("Benchmarking end-to-end processing...")
    e2e_loads = [10, 50, 100, 500, 1000]
    e2e_results = []
    
    for load in e2e_loads:
        print(f"  Running with {load} iterations...")
        result = benchmark_end_to_end(load)
        e2e_results.append(result)
        print(f"  Average latency: {result['avg_latency_ms']:.2f}ms")
    
    # Combine all results
    all_results = {
        "orderbook_updates": update_results,
        "trade_impact": impact_results,
        "end_to_end": e2e_results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    return all_results


def save_results(results: Dict[str, Any], filename: str = "benchmark_results.json") -> None:
    """
    Save benchmark results to a file.
    
    Args:
        results (dict): Benchmark results
        filename (str): Output filename
    """
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    
    # Save the results
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {filename}")


def generate_charts(results: Dict[str, Any], output_dir: str = "benchmark_charts") -> None:
    """
    Generate charts from benchmark results.
    
    Args:
        results (dict): Benchmark results
        output_dir (str): Output directory for charts
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data for plotting
    update_loads = [r["num_updates"] for r in results["orderbook_updates"]]
    update_times = [r["avg_time_ms"] for r in results["orderbook_updates"]]
    
    impact_loads = [r["num_calculations"] for r in results["trade_impact"]]
    impact_times = [r["avg_time_ms"] for r in results["trade_impact"]]
    
    e2e_loads = [r["num_iterations"] for r in results["end_to_end"]]
    e2e_avg_latencies = [r["avg_latency_ms"] for r in results["end_to_end"]]
    e2e_p95_latencies = [r["p95_latency_ms"] for r in results["end_to_end"]]
    e2e_p99_latencies = [r["p99_latency_ms"] for r in results["end_to_end"]]
    
    # Set up the figure style
    plt.style.use('ggplot')
    
    # Plot orderbook update latency
    plt.figure(figsize=(10, 6))
    plt.plot(update_loads, update_times, 'o-', linewidth=2, markersize=8)
    plt.xlabel('Number of Updates')
    plt.ylabel('Average Time (ms)')
    plt.title('Orderbook Update Latency vs. Load')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'orderbook_update_latency.png'), dpi=300)
    
    # Plot trade impact calculation latency
    plt.figure(figsize=(10, 6))
    plt.plot(impact_loads, impact_times, 'o-', linewidth=2, markersize=8)
    plt.xlabel('Number of Calculations')
    plt.ylabel('Average Time (ms)')
    plt.title('Trade Impact Calculation Latency vs. Load')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'trade_impact_latency.png'), dpi=300)
    
    # Plot end-to-end latency
    plt.figure(figsize=(10, 6))
    plt.plot(e2e_loads, e2e_avg_latencies, 'o-', linewidth=2, markersize=8, label='Average')
    plt.plot(e2e_loads, e2e_p95_latencies, 's--', linewidth=2, markersize=8, label='95th Percentile')
    plt.plot(e2e_loads, e2e_p99_latencies, '^:', linewidth=2, markersize=8, label='99th Percentile')
    plt.xlabel('Number of Iterations')
    plt.ylabel('Latency (ms)')
    plt.title('End-to-End Latency vs. Load')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'end_to_end_latency.png'), dpi=300)
    
    # Plot latency distribution for the highest load
    highest_load_idx = e2e_loads.index(max(e2e_loads))
    latencies = results["end_to_end"][highest_load_idx]["latencies_ms"]
    
    plt.figure(figsize=(10, 6))
    plt.hist(latencies, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(np.mean(latencies), color='red', linestyle='dashed', linewidth=2, label=f'Mean: {np.mean(latencies):.2f}ms')
    plt.axvline(np.percentile(latencies, 95), color='green', linestyle='dashed', linewidth=2, label=f'95th: {np.percentile(latencies, 95):.2f}ms')
    plt.axvline(np.percentile(latencies, 99), color='orange', linestyle='dashed', linewidth=2, label=f'99th: {np.percentile(latencies, 99):.2f}ms')
    plt.xlabel('Latency (ms)')
    plt.ylabel('Frequency')
    plt.title(f'End-to-End Latency Distribution (Load: {max(e2e_loads)} iterations)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'latency_distribution.png'), dpi=300)
    
    print(f"Charts saved to {output_dir}")


def main() -> None:
    """Main function to run benchmarks and generate charts."""
    # Run benchmarks
    results = run_benchmarks()
    
    # Save results
    save_results(results, "benchmark_results.json")
    
    # Generate charts
    generate_charts(results, "benchmark_charts")
    
    print("Benchmarking complete!")


if __name__ == "__main__":
    main()