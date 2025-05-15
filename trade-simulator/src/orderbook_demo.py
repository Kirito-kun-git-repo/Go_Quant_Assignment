#!/usr/bin/env python
"""
OrderBook Demo Script

This script demonstrates the OrderBook class by processing real market data
from the logs/raw_ticks.log file and displaying orderbook metrics.
"""

import json
import time
import sys
from pathlib import Path
from orderbook import OrderBook


def process_log_file(log_file_path, max_ticks=100):
    """
    Process ticks from a log file and update an orderbook.
    
    Args:
        log_file_path (str): Path to the log file
        max_ticks (int): Maximum number of ticks to process
    """
    book = OrderBook("BTC-USDT-SWAP")
    
    print(f"Processing up to {max_ticks} ticks from {log_file_path}")
    print("-" * 50)
    
    tick_count = 0
    start_time = time.perf_counter()
    
    with open(log_file_path, 'r') as f:
        for line in f:
            try:
                tick = json.loads(line.strip())
                book.update_from_tick(tick)
                tick_count += 1
                
                if tick_count % 10 == 0:
                    print(f"Processed {tick_count} ticks")
                    print(f"Mid Price: {book.mid_price():.2f}")
                    print(f"Spread: {book.spread():.2f}")
                    print(f"Volatility: {book.rolling_volatility() or 'N/A'}")
                    print("-" * 30)
                
                if tick_count >= max_ticks:
                    break
                    
            except json.JSONDecodeError:
                print(f"Error parsing JSON: {line[:50]}...")
                continue
            except Exception as e:
                print(f"Error processing tick: {e}")
                continue
    
    end_time = time.perf_counter()
    processing_time = end_time - start_time
    
    print("-" * 50)
    print(f"Processed {tick_count} ticks in {processing_time:.2f} seconds")
    print(f"Average processing time: {(processing_time / tick_count) * 1000:.2f} ms per tick")
    
    # Print final orderbook state
    print("\nFinal OrderBook State:")
    print(book)


def main():
    """Main entry point for the demo script."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_file = log_dir / "raw_ticks.log"
    
    if not log_file.exists():
        print(f"Error: Log file {log_file} does not exist.")
        print("Please run data_ingest.py first to collect market data.")
        sys.exit(1)
    
    max_ticks = 100
    if len(sys.argv) > 1:
        try:
            max_ticks = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number of ticks: {sys.argv[1]}. Using default: {max_ticks}")
    
    process_log_file(log_file, max_ticks)


if __name__ == "__main__":
    main()