#!/usr/bin/env python
"""
Unit tests for the Almgren-Chriss impact module.
"""

import sys
import os
import unittest
import numpy as np
from collections import deque

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.orderbook import OrderBook
from models.impact import (
    permanent_impact, 
    temporary_impact, 
    calculate_market_volume,
    calculate_total_impact
)


class TestImpact(unittest.TestCase):
    """Test cases for the impact module."""

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
        
        # Manually set volatility for testing
        self.book.mid_prices = deque([49995.0, 49996.0, 49994.0, 49997.0, 49993.0], maxlen=5)
        self.test_volatility = np.std(list(self.book.mid_prices))

    def test_market_volume_calculation(self):
        """Test the calculation of market volume from the orderbook."""
        # Expected volume: sum of all sizes in the initial tick
        expected_volume = 1.0 + 2.0 + 3.0 + 4.0 + 5.0 + 1.5 + 2.5 + 3.5 + 4.5 + 5.5
        
        # Calculate volume with all levels
        volume = calculate_market_volume(self.book, levels=10)
        self.assertAlmostEqual(volume, expected_volume, places=2)
        
        # Calculate volume with fewer levels
        volume_3_levels = calculate_market_volume(self.book, levels=3)
        expected_volume_3_levels = 1.0 + 2.0 + 3.0 + 1.5 + 2.5 + 3.5
        self.assertAlmostEqual(volume_3_levels, expected_volume_3_levels, places=2)

    def test_permanent_impact(self):
        """Test the permanent impact calculation with known inputs."""
        # Test parameters
        sigma = 10.0  # Volatility
        Q = 5.0       # Order size
        V = 50.0      # Market volume
        gamma = 0.1   # Impact parameter
        
        # Expected permanent impact: gamma * sigma * sqrt(Q/V)
        expected_impact = gamma * sigma * np.sqrt(Q / V)
        
        # Calculate impact
        impact = permanent_impact(sigma, Q, V, gamma)
        self.assertAlmostEqual(impact, expected_impact, places=6)
        
        # Test with different parameters
        sigma = 5.0
        Q = 10.0
        V = 100.0
        gamma = 0.2
        
        expected_impact = gamma * sigma * np.sqrt(Q / V)
        impact = permanent_impact(sigma, Q, V, gamma)
        self.assertAlmostEqual(impact, expected_impact, places=6)

    def test_temporary_impact(self):
        """Test the temporary impact calculation with known inputs."""
        # Test parameters
        sigma = 10.0  # Volatility
        Q = 5.0       # Order size
        V = 50.0      # Market volume
        epsilon = 0.1 # Impact parameter
        
        # Expected temporary impact: epsilon * sigma * (Q/V)
        expected_impact = epsilon * sigma * (Q / V)
        
        # Calculate impact
        impact = temporary_impact(sigma, Q, V, epsilon)
        self.assertAlmostEqual(impact, expected_impact, places=6)
        
        # Test with different parameters
        sigma = 5.0
        Q = 10.0
        V = 100.0
        epsilon = 0.2
        
        expected_impact = epsilon * sigma * (Q / V)
        impact = temporary_impact(sigma, Q, V, epsilon)
        self.assertAlmostEqual(impact, expected_impact, places=6)

    def test_total_impact_calculation(self):
        """Test the calculation of total impact from the orderbook."""
        # Skip this test if volatility is too small
        if self.test_volatility < 0.1:
            self.skipTest("Volatility too small for meaningful test")
        
        # Order size and impact parameters
        order_size = 2.0
        gamma = 0.1
        epsilon = 0.1
        
        # Calculate market volume
        market_volume = calculate_market_volume(self.book)
        
        # Expected impacts
        expected_perm_impact = gamma * self.test_volatility * np.sqrt(order_size / market_volume)
        expected_temp_impact = epsilon * self.test_volatility * (order_size / market_volume)
        expected_total_impact = expected_perm_impact + expected_temp_impact
        
        # Calculate impacts
        perm_impact, temp_impact, total_impact = calculate_total_impact(
            self.book, order_size, gamma, epsilon
        )
        
        # Check results
        self.assertAlmostEqual(perm_impact, expected_perm_impact, places=6)
        self.assertAlmostEqual(temp_impact, expected_temp_impact, places=6)
        self.assertAlmostEqual(total_impact, expected_total_impact, places=6)

    def test_invalid_inputs(self):
        """Test that appropriate errors are raised for invalid inputs."""
        # Test invalid sigma
        with self.assertRaises(ValueError):
            permanent_impact(0, 5.0, 50.0)
        
        # Test invalid Q
        with self.assertRaises(ValueError):
            permanent_impact(10.0, 0, 50.0)
        
        # Test invalid V
        with self.assertRaises(ValueError):
            permanent_impact(10.0, 5.0, 0)
        
        # Test invalid gamma
        with self.assertRaises(ValueError):
            permanent_impact(10.0, 5.0, 50.0, 0)
        
        # Test invalid epsilon
        with self.assertRaises(ValueError):
            temporary_impact(10.0, 5.0, 50.0, 0)


if __name__ == "__main__":
    unittest.main()