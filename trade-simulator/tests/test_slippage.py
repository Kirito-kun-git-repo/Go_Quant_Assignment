#!/usr/bin/env python
"""
Unit tests for the slippage module.
"""

import sys
import os
import unittest

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.orderbook import OrderBook
from models.slippage import simulate_slippage, calculate_slippage_percentage


class TestSlippage(unittest.TestCase):
    """Test cases for the slippage module."""

    def setUp(self):
        """Set up a fresh OrderBook instance for each test."""
        self.book = OrderBook("BTC-USDT-SWAP")
        
        # Initial orderbook state with known price levels
        self.initial_tick = {
            "timestamp": "2023-01-01T00:00:00Z",
            "exchange": "OKX",
            "symbol": "BTC-USDT-SWAP",
            "asks": [
                ["50000.0", "1.0"],   # $50,000 per BTC, 1.0 BTC available
                ["50010.0", "2.0"],   # $50,010 per BTC, 2.0 BTC available
                ["50020.0", "3.0"],   # $50,020 per BTC, 3.0 BTC available
                ["50030.0", "4.0"],   # $50,030 per BTC, 4.0 BTC available
                ["50040.0", "5.0"],   # $50,040 per BTC, 5.0 BTC available
            ],
            "bids": [
                ["49990.0", "1.5"],   # $49,990 per BTC, 1.5 BTC available
                ["49980.0", "2.5"],   # $49,980 per BTC, 2.5 BTC available
                ["49970.0", "3.5"],   # $49,970 per BTC, 3.5 BTC available
                ["49960.0", "4.5"],   # $49,960 per BTC, 4.5 BTC available
                ["49950.0", "5.5"],   # $49,950 per BTC, 5.5 BTC available
            ]
        }
        
        self.book.update_from_tick(self.initial_tick)

    def test_small_buy_order(self):
        """Test slippage for a small buy order that fits within the first level."""
        # Order for 0.5 BTC at $50,000 = $25,000
        order_usd = 25000.0
        
        # Expected slippage calculation:
        # Mid price = (49990 + 50000) / 2 = 49995
        # VWAP = 50000
        # Quantity = 0.5 BTC
        # Slippage = (50000 - 49995) * 0.5 = $2.5
        expected_slippage = 2.5
        
        slippage = simulate_slippage(order_usd, self.book, "buy")
        self.assertAlmostEqual(slippage, expected_slippage, places=2)
        
        # Test percentage calculation
        expected_percentage = (expected_slippage / order_usd) * 100
        percentage = calculate_slippage_percentage(order_usd, self.book, "buy")
        self.assertAlmostEqual(percentage, expected_percentage, places=4)

    def test_large_buy_order(self):
        """Test slippage for a large buy order that spans multiple levels."""
        # Order for 3.0 BTC spanning multiple levels
        # 1.0 BTC at $50,000 = $50,000
        # 2.0 BTC at $50,010 = $100,020
        # Total: $150,020
        order_usd = 150020.0
        
        # Expected slippage calculation:
        # Mid price = (49990 + 50000) / 2 = 49995
        # VWAP = (50000*1.0 + 50010*2.0) / 3.0 = 50006.67
        # Quantity = 3.0 BTC
        # Slippage = (50006.67 - 49995) * 3.0 = $35.00
        expected_slippage = 35.00
        
        slippage = simulate_slippage(order_usd, self.book, "buy")
        self.assertAlmostEqual(slippage, expected_slippage, places=2)

    def test_small_sell_order(self):
        """Test slippage for a small sell order that fits within the first level."""
        # Order for 0.5 BTC at $49,990 = $24,995
        order_usd = 24995.0
        
        # Expected slippage calculation:
        # Mid price = (49990 + 50000) / 2 = 49995
        # VWAP = 49990
        # Quantity = 0.5 BTC
        # Slippage = (49995 - 49990) * 0.5 = $2.5
        expected_slippage = 2.5
        
        slippage = simulate_slippage(order_usd, self.book, "sell")
        self.assertAlmostEqual(slippage, expected_slippage, places=2)

    def test_large_sell_order(self):
        """Test slippage for a large sell order that spans multiple levels."""
        # Order for 4.0 BTC spanning multiple levels
        # 1.5 BTC at $49,990 = $74,985
        # 2.5 BTC at $49,980 = $124,950
        # Total: $199,935
        order_usd = 199935.0
        
        # Expected slippage calculation:
        # Mid price = (49990 + 50000) / 2 = 49995
        # VWAP = (49990*1.5 + 49980*2.5) / 4.0 = 49983.75
        # Quantity = 4.0 BTC
        # Slippage = (49995 - 49983.75) * 4.0 = $45.0
        expected_slippage = 45.0
        
        slippage = simulate_slippage(order_usd, self.book, "sell")
        self.assertAlmostEqual(slippage, expected_slippage, places=2)

    def test_insufficient_liquidity(self):
        """Test that an error is raised when there's not enough liquidity."""
        # Order for 20 BTC, which exceeds the available liquidity
        order_usd = 1000000.0
        
        with self.assertRaises(ValueError):
            simulate_slippage(order_usd, self.book, "buy")

    def test_invalid_side(self):
        """Test that an error is raised when an invalid side is provided."""
        order_usd = 25000.0
        
        with self.assertRaises(ValueError):
            simulate_slippage(order_usd, self.book, "invalid")


if __name__ == "__main__":
    unittest.main()