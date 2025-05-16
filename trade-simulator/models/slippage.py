#!/usr/bin/env python
"""
Slippage Module for Trade Simulator

This module simulates market impact and calculates slippage by walking through
the orderbook until an order is filled.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Union

# Import the OrderBook class from the src directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.orderbook import OrderBook


def simulate_slippage(order_usd: float, orderbook: OrderBook, side: str) -> float:
    """
    Simulate slippage by walking through the orderbook until the order is filled.
    
    Args:
        order_usd (float): The order size in USD
        orderbook (OrderBook): The current orderbook state
        side (str): The order side, either "buy" or "sell"
        
    Returns:
        float: The slippage amount in USD (positive means worse price)
        
    Raises:
        ValueError: If the side is not "buy" or "sell"
        ValueError: If the orderbook doesn't have enough liquidity to fill the order
    """
    if side not in ["buy", "sell"]:
        raise ValueError('Side must be either "buy" or "sell"')
    
    # Get the mid price as reference
    mid_price = orderbook.mid_price()
    if mid_price is None:
        raise ValueError("Cannot calculate slippage: orderbook has no mid price")
    
    # Get the relevant side of the orderbook
    levels = orderbook.asks if side == "buy" else orderbook.bids
    
    if not levels:
        raise ValueError(f"Cannot calculate slippage: orderbook has no {'asks' if side == 'buy' else 'bids'}")
    
    # Walk through the orderbook until the order is filled
    remaining_usd = order_usd
    executed_value = 0.0  # Total executed value in USD
    executed_quantity = 0.0  # Total executed quantity in base currency
    
    for price, size in levels:
        # Calculate how much we can execute at this level
        level_value = price * size  # Value of this level in USD
        
        if remaining_usd >= level_value:
            # We can consume the entire level
            executed_value += level_value
            executed_quantity += size
            remaining_usd -= level_value
        else:
            # We can only consume part of the level
            partial_size = remaining_usd / price
            executed_value += price * partial_size
            executed_quantity += partial_size
            remaining_usd = 0
            break
    
    # Check if we couldn't fill the entire order
    if remaining_usd > 0:
        raise ValueError(f"Not enough liquidity to fill {order_usd} USD order")
    
    # Calculate VWAP (Volume-Weighted Average Price)
    vwap = executed_value / executed_quantity if executed_quantity > 0 else 0
    
    # Calculate slippage in USD
    # For buys: VWAP - mid_price (positive means we paid more)
    # For sells: mid_price - VWAP (positive means we received less)
    if side == "buy":
        slippage_usd = (vwap - mid_price) * executed_quantity
    else:  # sell
        slippage_usd = (mid_price - vwap) * executed_quantity
    
    return slippage_usd


def calculate_slippage_percentage(order_usd: float, orderbook: OrderBook, side: str) -> float:
    """
    Calculate slippage as a percentage of the order value.
    
    Args:
        order_usd (float): The order size in USD
        orderbook (OrderBook): The current orderbook state
        side (str): The order side, either "buy" or "sell"
        
    Returns:
        float: The slippage as a percentage of the order value
    """
    slippage_usd = simulate_slippage(order_usd, orderbook, side)
    slippage_percentage = (slippage_usd / order_usd) * 100
    
    return slippage_percentage


if __name__ == "__main__":
    # Example usage
    from src.orderbook import OrderBook
    
    # Create a sample orderbook
    book = OrderBook("BTC-USDT-SWAP")
    
    # Sample tick data
    sample_tick = {
        "timestamp": "2023-01-01T00:00:00Z",
        "exchange": "OKX",
        "symbol": "BTC-USDT-SWAP",
        "asks": [
            ["50000.0", "1.0"],   # $50,000 per BTC, 1.0 BTC available
            ["50010.0", "2.0"],   # $50,010 per BTC, 2.0 BTC available
            ["50020.0", "3.0"],   # $50,020 per BTC, 3.0 BTC available
        ],
        "bids": [
            ["49990.0", "1.5"],   # $49,990 per BTC, 1.5 BTC available
            ["49980.0", "2.5"],   # $49,980 per BTC, 2.5 BTC available
            ["49970.0", "3.5"],   # $49,970 per BTC, 3.5 BTC available
        ]
    }
    
    book.update_from_tick(sample_tick)
    
    # Calculate slippage for different order sizes
    small_buy_order = 25000.0  # $25,000 USD (should be filled at first level)
    large_buy_order = 150000.0  # $150,000 USD (should require multiple levels)
    
    small_buy_slippage = simulate_slippage(small_buy_order, book, "buy")
    large_buy_slippage = simulate_slippage(large_buy_order, book, "buy")
    
    print(f"Small buy order ({small_buy_order} USD) slippage: ${small_buy_slippage:.2f} USD")
    print(f"Large buy order ({large_buy_order} USD) slippage: ${large_buy_slippage:.2f} USD")
    
    # Calculate slippage percentage
    small_buy_slippage_pct = calculate_slippage_percentage(small_buy_order, book, "buy")
    large_buy_slippage_pct = calculate_slippage_percentage(large_buy_order, book, "buy")
    
    print(f"Small buy order slippage: {small_buy_slippage_pct:.4f}%")
    print(f"Large buy order slippage: {large_buy_slippage_pct:.4f}%")