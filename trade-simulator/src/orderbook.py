#!/usr/bin/env python
"""
OrderBook Module for Trade Simulator

This module implements an OrderBook class that maintains a sorted list of bids and asks,
and provides methods for calculating market metrics like mid-price and spread.
It also includes a rolling volatility tracker.
"""

import bisect
import json
import numpy as np
from collections import deque
from typing import List, Tuple, Dict, Optional, Union


class OrderBook:
    """
    OrderBook class that maintains sorted lists of bids and asks.
    
    Attributes:
        symbol (str): The trading symbol this orderbook represents
        asks (list): Sorted list of [price, size] ask orders (lowest first)
        bids (list): Sorted list of [price, size] bid orders (highest first)
        mid_prices (deque): Rolling window of mid prices for volatility calculation
        mid_price_window (int): Size of the rolling window for volatility calculation
    """
    
    def __init__(self, symbol: str, mid_price_window: int = 100):
        """
        Initialize an empty orderbook.
        
        Args:
            symbol (str): The trading symbol this orderbook represents
            mid_price_window (int): Size of the rolling window for volatility calculation
        """
        self.symbol = symbol
        self.asks: List[List[float]] = []  # Sorted by price (ascending)
        self.bids: List[List[float]] = []  # Sorted by price (descending)
        self.mid_prices = deque(maxlen=mid_price_window)
        self.mid_price_window = mid_price_window
    
    def update_from_tick(self, tick: Dict) -> None:
        """
        Update the orderbook with a new tick.
        
        Args:
            tick (dict): A dictionary containing the new orderbook state
                         with 'asks' and 'bids' lists of [price, size]
        """
        # Ensure the tick is for the correct symbol
        if 'symbol' in tick and tick['symbol'] != self.symbol:
            raise ValueError(f"Tick symbol {tick['symbol']} does not match orderbook symbol {self.symbol}")
        
        # Update asks
        if 'asks' in tick:
            self._update_side(tick['asks'], self.asks, is_bid=False)
        
        # Update bids
        if 'bids' in tick:
            self._update_side(tick['bids'], self.bids, is_bid=True)
        
        # Update mid price for volatility calculation
        current_mid = self.mid_price()
        if current_mid is not None:
            self.mid_prices.append(current_mid)
    
    def _update_side(self, updates: List[List[Union[str, float]]], 
                    current_levels: List[List[float]], is_bid: bool) -> None:
        """
        Update one side of the orderbook (bids or asks).
        
        Args:
            updates (list): List of [price, size] updates
            current_levels (list): Current list of [price, size] levels
            is_bid (bool): True if updating bids, False if updating asks
        """
        for price_str, size_str in updates:
            # Convert string values to float
            price = float(price_str)
            size = float(size_str)
            
            # Find the index where this price level should be
            idx = self._find_price_index(price, current_levels, is_bid)
            
            # If the price level exists, update it or remove it if size is 0
            if idx < len(current_levels) and abs(current_levels[idx][0] - price) < 1e-10:
                if size > 0:
                    current_levels[idx][1] = size
                else:
                    current_levels.pop(idx)
            # If the price level doesn't exist and size > 0, insert it
            elif size > 0:
                current_levels.insert(idx, [price, size])
    
    def _find_price_index(self, price: float, levels: List[List[float]], is_bid: bool) -> int:
        """
        Find the index where a price should be inserted in the orderbook.
        
        Args:
            price (float): The price to find
            levels (list): Current list of [price, size] levels
            is_bid (bool): True if searching in bids, False if in asks
            
        Returns:
            int: The index where the price should be inserted
        """
        if not levels:
            return 0
        
        if is_bid:
            # For bids, we want descending order (highest first)
            for i, (level_price, _) in enumerate(levels):
                if price >= level_price:
                    return i
            return len(levels)
        else:
            # For asks, we want ascending order (lowest first)
            for i, (level_price, _) in enumerate(levels):
                if price <= level_price:
                    return i
            return len(levels)
    
    def best_bid(self) -> Optional[float]:
        """
        Get the best (highest) bid price.
        
        Returns:
            float or None: The best bid price, or None if there are no bids
        """
        return self.bids[0][0] if self.bids else None
    
    def best_ask(self) -> Optional[float]:
        """
        Get the best (lowest) ask price.
        
        Returns:
            float or None: The best ask price, or None if there are no asks
        """
        return self.asks[0][0] if self.asks else None
    
    def mid_price(self) -> Optional[float]:
        """
        Calculate the mid price between best bid and best ask.
        
        Returns:
            float or None: The mid price, or None if either best bid or best ask is missing
        """
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        
        if best_bid is None or best_ask is None:
            return None
        
        return (best_bid + best_ask) / 2
    
    def spread(self) -> Optional[float]:
        """
        Calculate the spread between best ask and best bid.
        
        Returns:
            float or None: The spread, or None if either best bid or best ask is missing
        """
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        
        if best_bid is None or best_ask is None:
            return None
        
        # Ensure the spread is always positive
        return abs(best_ask - best_bid)
    
    def rolling_volatility(self) -> Optional[float]:
        """
        Calculate the rolling volatility based on the mid price history.
        
        Returns:
            float or None: The standard deviation of mid prices, or None if not enough data
        """
        if len(self.mid_prices) < 2:
            return None
        
        return np.std(list(self.mid_prices))
    
    def depth(self, levels: int = 5) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Get the top N levels of the orderbook.
        
        Args:
            levels (int): Number of price levels to return
            
        Returns:
            tuple: (bids, asks) where each is a list of [price, size] up to 'levels' entries
        """
        return self.bids[:levels], self.asks[:levels]
    
    def __str__(self) -> str:
        """
        String representation of the orderbook.
        
        Returns:
            str: A formatted string showing the top levels of bids and asks
        """
        bid_str = "\n".join([f"{price:.2f} @ {size:.2f}" for price, size in self.bids[:5]])
        ask_str = "\n".join([f"{price:.2f} @ {size:.2f}" for price, size in self.asks[:5]])
        
        mid = self.mid_price()
        spread = self.spread()
        vol = self.rolling_volatility()
        
        mid_str = f"{mid:.2f}" if mid is not None else "N/A"
        spread_str = f"{spread:.2f}" if spread is not None else "N/A"
        vol_str = f"{vol:.6f}" if vol is not None else "N/A"
        
        return (
            f"OrderBook: {self.symbol}\n"
            f"Top 5 Bids:\n{bid_str}\n"
            f"Top 5 Asks:\n{ask_str}\n"
            f"Mid Price: {mid_str}\n"
            f"Spread: {spread_str}\n"
            f"Volatility: {vol_str}"
        )


if __name__ == "__main__":
    # Simple example usage
    book = OrderBook("BTC-USDT-SWAP")
    
    # Sample tick data
    sample_tick = {
        "timestamp": "2023-01-01T00:00:00Z",
        "exchange": "OKX",
        "symbol": "BTC-USDT-SWAP",
        "asks": [["50000.1", "1.5"], ["50001.2", "2.3"], ["50002.3", "3.1"]],
        "bids": [["49999.9", "1.2"], ["49998.8", "2.1"], ["49997.7", "3.0"]]
    }
    
    book.update_from_tick(sample_tick)
    print(book)