#!/usr/bin/env python
"""
Unit tests for the maker/taker classification module.
"""

import sys
import os
import unittest
import numpy as np
import tempfile
import joblib

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.orderbook import OrderBook
from models.maker_taker import (
    classify_order_heuristic,
    extract_orderbook_features,
    train_maker_taker_model,
    classify_order_ml
)


class TestMakerTaker(unittest.TestCase):
    """Test cases for the maker/taker classification module."""

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

    def test_small_buy_order_classification(self):
        """Test classification of a small buy order that should be a maker."""
        # Order smaller than the best ask level
        # Best ask: 1.0 BTC at $50,000 = $50,000
        # Order: $25,000 (0.5 BTC)
        order_usd = 25000.0
        
        classification = classify_order_heuristic(order_usd, self.book, "buy")
        self.assertEqual(classification, "maker")

    def test_large_buy_order_classification(self):
        """Test classification of a large buy order that should be a taker."""
        # Order larger than the best ask level
        # Best ask: 1.0 BTC at $50,000 = $50,000
        # Order: $75,000 (1.5 BTC)
        order_usd = 75000.0
        
        classification = classify_order_heuristic(order_usd, self.book, "buy")
        self.assertEqual(classification, "taker")

    def test_small_sell_order_classification(self):
        """Test classification of a small sell order that should be a maker."""
        # Order smaller than the best bid level
        # Best bid: 1.5 BTC at $49,990 = $74,985
        # Order: $25,000 (0.5 BTC)
        order_usd = 25000.0
        
        classification = classify_order_heuristic(order_usd, self.book, "sell")
        self.assertEqual(classification, "maker")

    def test_large_sell_order_classification(self):
        """Test classification of a large sell order that should be a taker."""
        # Order larger than the best bid level
        # Best bid: 1.5 BTC at $49,990 = $74,985
        # Order: $100,000 (2.0 BTC)
        order_usd = 100000.0
        
        classification = classify_order_heuristic(order_usd, self.book, "sell")
        self.assertEqual(classification, "taker")

    def test_edge_case_equal_to_best_level(self):
        """Test classification when order size equals the best level."""
        # Best ask: 1.0 BTC at $50,000 = $50,000
        # Order: $50,000 (1.0 BTC)
        order_usd = 50000.0
        
        classification = classify_order_heuristic(order_usd, self.book, "buy")
        self.assertEqual(classification, "maker")
        
        # Best bid: 1.5 BTC at $49,990 = $74,985
        # Order: $74,985 (1.5 BTC)
        order_usd = 74985.0
        
        classification = classify_order_heuristic(order_usd, self.book, "sell")
        self.assertEqual(classification, "maker")

    def test_invalid_side(self):
        """Test that an error is raised for an invalid side."""
        order_usd = 25000.0
        
        with self.assertRaises(ValueError):
            classify_order_heuristic(order_usd, self.book, "invalid")

    def test_feature_extraction(self):
        """Test the extraction of features from the orderbook."""
        features = extract_orderbook_features(self.book)
        
        # Check that we have the expected number of features
        # 1 (mid_price) + 1 (spread) + 1 (spread_pct) + 1 (volume_imbalance) + 
        # 5 (bid_volumes) + 5 (ask_volumes) + 5 (bid_distances) + 5 (ask_distances)
        expected_feature_count = 1 + 1 + 1 + 1 + 5 + 5 + 5 + 5
        self.assertEqual(len(features), expected_feature_count)
        
        # Check that the first feature is the mid price
        mid_price = (49990.0 + 50000.0) / 2
        self.assertAlmostEqual(features[0], mid_price, places=2)
        
        # Check that the second feature is the spread
        spread = 50000.0 - 49990.0
        self.assertAlmostEqual(features[1], spread, places=2)

    def test_model_training_and_prediction(self):
        """Test training a model and using it for prediction."""
        # Create synthetic training data
        orderbooks = [self.book] * 10
        
        # Create synthetic orders with known labels
        orders = [
            {"size_usd": 25000.0, "side": "buy", "is_maker": True},
            {"size_usd": 75000.0, "side": "buy", "is_maker": False},
            {"size_usd": 25000.0, "side": "sell", "is_maker": True},
            {"size_usd": 100000.0, "side": "sell", "is_maker": False},
            {"size_usd": 50000.0, "side": "buy", "is_maker": True},
            {"size_usd": 80000.0, "side": "buy", "is_maker": False},
            {"size_usd": 30000.0, "side": "sell", "is_maker": True},
            {"size_usd": 90000.0, "side": "sell", "is_maker": False},
            {"size_usd": 40000.0, "side": "buy", "is_maker": True},
            {"size_usd": 95000.0, "side": "buy", "is_maker": False},
        ]
        
        # Create a temporary file for the model
        with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as temp_file:
            model_path = temp_file.name
        
        try:
            # Train the model
            model, scaler = train_maker_taker_model(orderbooks, orders, model_path)
            
            # Test prediction with the trained model
            small_order = 25000.0
            large_order = 75000.0
            
            # Test ML classification
            small_classification = classify_order_ml(small_order, self.book, "buy", model_path)
            large_classification = classify_order_ml(large_order, self.book, "buy", model_path)
            
            # Check that the predictions match the expected labels
            self.assertEqual(small_classification, "maker")
            self.assertEqual(large_classification, "taker")
            
        finally:
            # Clean up the temporary file
            if os.path.exists(model_path):
                os.remove(model_path)


if __name__ == "__main__":
    unittest.main()