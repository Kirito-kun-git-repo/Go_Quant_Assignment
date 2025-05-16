#!/usr/bin/env python
"""
Almgren-Chriss Market Impact Model

This module implements the Almgren-Chriss market impact model, which separates
price impact into permanent and temporary components.

References:
    Almgren, R., & Chriss, N. (2001). Optimal execution of portfolio transactions.
    Journal of Risk, 3, 5-40.
"""

import numpy as np
from typing import List, Optional, Tuple

# Import the OrderBook class from the src directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.orderbook import OrderBook


def calculate_market_volume(orderbook: OrderBook, levels: int = 10) -> float:
    """
    Calculate the total market volume from the top N levels of the orderbook.
    
    Args:
        orderbook (OrderBook): The current orderbook state
        levels (int): Number of price levels to consider
        
    Returns:
        float: The total volume in base currency units
    """
    bids, asks = orderbook.depth(levels)
    
    # Sum the volumes from both sides
    total_volume = sum(size for _, size in bids) + sum(size for _, size in asks)
    
    return total_volume


def permanent_impact(sigma: float, Q: float, V: float, gamma: float = 0.1) -> float:
    """
    Calculate the permanent price impact according to the Almgren-Chriss model.
    
    The permanent impact represents the lasting effect on the market price
    after the order is executed.
    
    Args:
        sigma (float): Market volatility (standard deviation of returns)
        Q (float): Order size in base currency units
        V (float): Market volume in base currency units
        gamma (float): Market impact parameter (default: 0.1)
        
    Returns:
        float: Permanent price impact in currency units
        
    Notes:
        The formula used is: permanent_impact = gamma * sigma * (Q / V)^(1/2)
    """
    if sigma <= 0:
        raise ValueError("Volatility (sigma) must be positive")
    if Q <= 0:
        raise ValueError("Order size (Q) must be positive")
    if V <= 0:
        raise ValueError("Market volume (V) must be positive")
    if gamma <= 0:
        raise ValueError("Impact parameter (gamma) must be positive")
    
    # Calculate the permanent impact using the Almgren-Chriss formula
    impact = gamma * sigma * np.sqrt(Q / V)
    
    return impact


def temporary_impact(sigma: float, Q: float, V: float, epsilon: float = 0.1) -> float:
    """
    Calculate the temporary price impact according to the Almgren-Chriss model.
    
    The temporary impact represents the transient effect on the price during
    the execution of the order, which disappears after the order is completed.
    
    Args:
        sigma (float): Market volatility (standard deviation of returns)
        Q (float): Order size in base currency units
        V (float): Market volume in base currency units
        epsilon (float): Market impact parameter (default: 0.1)
        
    Returns:
        float: Temporary price impact in currency units
        
    Notes:
        The formula used is: temporary_impact = epsilon * sigma * (Q / V)
    """
    if sigma <= 0:
        raise ValueError("Volatility (sigma) must be positive")
    if Q <= 0:
        raise ValueError("Order size (Q) must be positive")
    if V <= 0:
        raise ValueError("Market volume (V) must be positive")
    if epsilon <= 0:
        raise ValueError("Impact parameter (epsilon) must be positive")
    
    # Calculate the temporary impact using the Almgren-Chriss formula
    impact = epsilon * sigma * (Q / V)
    
    return impact


def calculate_total_impact(orderbook: OrderBook, order_size: float, 
                          gamma: float = 0.1, epsilon: float = 0.1) -> Tuple[float, float, float]:
    """
    Calculate both permanent and temporary impact for an order.
    
    Args:
        orderbook (OrderBook): The current orderbook state
        order_size (float): Order size in base currency units
        gamma (float): Permanent impact parameter (default: 0.1)
        epsilon (float): Temporary impact parameter (default: 0.1)
        
    Returns:
        tuple: (permanent_impact, temporary_impact, total_impact) in currency units
        
    Raises:
        ValueError: If volatility is None or market volume is zero
    """
    # Get volatility from the orderbook
    sigma = orderbook.rolling_volatility()
    if sigma is None:
        raise ValueError("Cannot calculate impact: orderbook has no volatility data")
    
    # Calculate market volume from top 10 levels
    market_volume = calculate_market_volume(orderbook, levels=10)
    if market_volume <= 0:
        raise ValueError("Cannot calculate impact: orderbook has no volume")
    
    # Calculate impacts
    perm_impact = permanent_impact(sigma, order_size, market_volume, gamma)
    temp_impact = temporary_impact(sigma, order_size, market_volume, epsilon)
    total_impact = perm_impact + temp_impact
    
    return perm_impact, temp_impact, total_impact


if __name__ == "__main__":
    # Example usage
    from src.orderbook import OrderBook
    
    # Create a sample orderbook
    book = OrderBook("BTC-USDT-SWAP")
    
    # Sample tick data with volatility history
    for i in range(20):  # Add some history for volatility calculation
        price_offset = i * 10
        sample_tick = {
            "timestamp": f"2023-01-01T00:00:{i:02d}Z",
            "exchange": "OKX",
            "symbol": "BTC-USDT-SWAP",
            "asks": [
                [f"{50000.0 + price_offset}", "1.0"],
                [f"{50010.0 + price_offset}", "2.0"],
                [f"{50020.0 + price_offset}", "3.0"],
            ],
            "bids": [
                [f"{49990.0 - price_offset}", "1.5"],
                [f"{49980.0 - price_offset}", "2.5"],
                [f"{49970.0 - price_offset}", "3.5"],
            ]
        }
        book.update_from_tick(sample_tick)
    
    # Calculate market impact for different order sizes
    order_sizes = [1.0, 5.0, 10.0]
    
    for size in order_sizes:
        try:
            perm, temp, total = calculate_total_impact(book, size)
            print(f"Order size: {size} BTC")
            print(f"  Permanent impact: ${perm:.2f}")
            print(f"  Temporary impact: ${temp:.2f}")
            print(f"  Total impact: ${total:.2f}")
        except ValueError as e:
            print(f"Error for order size {size}: {e}")