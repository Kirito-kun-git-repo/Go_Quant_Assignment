#!/usr/bin/env python
"""
Unit tests for the OrderBook class.
"""

import sys
import os
import unittest
import numpy as np
from collections import deque

# Add the src directory to the path so we can import the orderbook module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.orderbook import OrderBook


class TestOrderBook(unittest.TestCase):
    """Test cases for the OrderBook class."""

    def setUp(self):
        """Set up a fresh OrderBook instance for each test."""
        self.book = OrderBook("BTC-USDT-SWAP")
        
        # Initial orderbook state
        self.initial_tick = {
            "timestamp": "2023-01-01T00:00:00Z",
            "exchange": "OKX",
            "symbol": "BTC-USDT-SWAP",
            "asks": [
                ["50000.1", "1.5"],
                ["50001.2", "2.3"],
                ["50002.3", "3.1"],
                ["50003.4", "4.0"],
                ["50004.5", "5.2"]
            ],
            "bids": [
                ["49999.9", "1.2"],
                ["49998.8", "2.1"],
                ["49997.7", "3.0"],
                ["49996.6", "4.1"],
                ["49995.5", "5.3"]
            ]
        }
        
        self.book.update_from_tick(self.initial_tick)

    def test_initial_state(self):
        """Test that the orderbook is initialized correctly."""
        self.assertEqual(self.book.symbol, "BTC-USDT-SWAP")
        self.assertEqual(len(self.book.asks), 5)
        self.assertEqual(len(self.book.bids), 5)
        self.assertEqual(self.book.asks[0][0], 50000.1)
        self.assertEqual(self.book.bids[0][0], 49999.9)

    def test_update_existing_level(self):
        """Test updating an existing price level."""
        update_tick = {
            "symbol": "BTC-USDT-SWAP",
            "asks": [["50001.2", "3.5"]],  # Update size of existing level
            "bids": [["49998.8", "4.2"]]   # Update size of existing level
        }
        
        self.book.update_from_tick(update_tick)
        
        # Check that the levels were updated
        self.assertEqual(self.book.asks[1][1], 3.5)
        self.assertEqual(self.book.bids[1][1], 4.2)
        
        # Check that the number of levels didn't change
        self.assertEqual(len(self.book.asks), 5)
        self.assertEqual(len(self.book.bids), 5)

    def test_insert_new_level(self):
        """Test inserting a new price level."""
        update_tick = {
            "symbol": "BTC-USDT-SWAP",
            "asks": [["50000.5", "2.5"]],  # New level between existing ones
            "bids": [["49999.5", "3.2"]]   # New level between existing ones
        }
        
        self.book.update_from_tick(update_tick)
        
        # Check that the new levels were inserted at the correct positions
        self.assertEqual(self.book.asks[1][0], 50000.5)
        self.assertEqual(self.book.asks[1][1], 2.5)
        self.assertEqual(self.book.bids[0][0], 49999.9)
        self.assertEqual(self.book.bids[1][0], 49999.5)
        
        # Check that the number of levels increased
        self.assertEqual(len(self.book.asks), 6)
        self.assertEqual(len(self.book.bids), 6)

    def test_remove_level(self):
        """Test removing a price level when size is 0."""
        update_tick = {
            "symbol": "BTC-USDT-SWAP",
            "asks": [["50001.2", "0"]],  # Remove by setting size to 0
            "bids": [["49998.8", "0"]]   # Remove by setting size to 0
        }
        
        self.book.update_from_tick(update_tick)
        
        # Check that the levels were removed
        self.assertEqual(len(self.book.asks), 4)
        self.assertEqual(len(self.book.bids), 4)
        
        # Check that the remaining levels are correct
        self.assertEqual(self.book.asks[0][0], 50000.1)
        self.assertEqual(self.book.asks[1][0], 50002.3)
        self.assertEqual(self.book.bids[0][0], 49999.9)
        self.assertEqual(self.book.bids[1][0], 49997.7)

    def test_best_bid_ask(self):
        """Test the best_bid and best_ask methods."""
        self.assertEqual(self.book.best_bid(), 49999.9)
        self.assertEqual(self.book.best_ask(), 50000.1)
        
        # Update the best levels
        update_tick = {
            "symbol": "BTC-USDT-SWAP",
            "asks": [["49999.95", "1.0"]],  # New best ask
            "bids": [["49999.85", "1.0"]]   # New best bid
        }
        
        self.book.update_from_tick(update_tick)
        
        self.assertEqual(self.book.best_bid(), 49999.9)
        self.assertEqual(self.book.best_ask(), 49999.95)

    def test_mid_price_and_spread(self):
        """Test the mid_price and spread methods."""
        # Initial mid price and spread
        self.assertAlmostEqual(self.book.mid_price(), (49999.9 + 50000.1) / 2)
        self.assertAlmostEqual(self.book.spread(), 50000.1 - 49999.9)
        
        # Update the best levels
        update_tick = {
            "symbol": "BTC-USDT-SWAP",
            "asks": [["50000.0", "1.0"]],  # New best ask
            "bids": [["49999.8", "1.0"]]   # New best bid
        }
        
        self.book.update_from_tick(update_tick)
        
        # Check updated mid price and spread
        self.assertAlmostEqual(self.book.mid_price(), (49999.9 + 50000.0) / 2)
        self.assertAlmostEqual(self.book.spread(), 50000.0 - 49999.9)

    def test_rolling_volatility(self):
        """Test the rolling_volatility method with a known sequence."""
        # Create a new orderbook with a smaller window for testing
        test_book = OrderBook("TEST", mid_price_window=5)
        
        # Manually set mid prices
        mid_prices = [100.0, 101.0, 99.0, 102.0, 98.0]
        test_book.mid_prices = deque(mid_prices, maxlen=5)
        
        # Calculate expected volatility
        expected_volatility = np.std(mid_prices)
        
        # Check that the calculated volatility matches
        self.assertAlmostEqual(test_book.rolling_volatility(), expected_volatility)
        
        # Add a new mid price and check that the window slides
        test_tick = {
            "symbol": "TEST",
            "asks": [["103.0", "1.0"]],
            "bids": [["102.0", "1.0"]]
        }
        
        test_book.update_from_tick(test_tick)
        
        # New mid prices should be [101.0, 99.0, 102.0, 98.0, 102.5]
        expected_new_mid_prices = [101.0, 99.0, 102.0, 98.0, 102.5]
        expected_new_volatility = np.std(expected_new_mid_prices)
        
        self.assertAlmostEqual(test_book.rolling_volatility(), expected_new_volatility)

    def test_empty_orderbook(self):
        """Test behavior with an empty orderbook."""
        empty_book = OrderBook("EMPTY")
        
        self.assertIsNone(empty_book.best_bid())
        self.assertIsNone(empty_book.best_ask())
        self.assertIsNone(empty_book.mid_price())
        self.assertIsNone(empty_book.spread())
        self.assertIsNone(empty_book.rolling_volatility())


if __name__ == "__main__":
    unittest.main()