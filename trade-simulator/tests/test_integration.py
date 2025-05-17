#!/usr/bin/env python
"""
Integration Tests for Trading Simulator

This module contains integration tests for the trading simulator,
focusing on end-to-end functionality and performance.
"""

import os
import sys
import time
import pytest
import threading
import asyncio
import numpy as np
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.orderbook import OrderBook
from src.app import update_trade_impact, update_market_data_display
from models.slippage import simulate_slippage
from models.fee import compute_fee
from models.impact import calculate_total_impact
from models.maker_taker import classify_order_heuristic


class TestIntegration:
    """Integration tests for the trading simulator."""

    @pytest.fixture
    def orderbook(self):
        """Create a test orderbook with sample data."""
        book = OrderBook("BTC-USDT-SWAP")
        
        # Add some initial data to the orderbook
        for i in range(20):  # Add enough data for volatility calculation
            price_offset = i * 5
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
        
        return book

    @pytest.fixture
    def mock_window(self):
        """Create a mock PySimpleGUI window for testing."""
        mock_window = MagicMock()
        
        # Mock the window elements
        elements = {
            '-QTY-': MagicMock(get=lambda: "100"),
            '-TIER-': MagicMock(get=lambda: "VIP0"),
            '-SLIP-': MagicMock(update=MagicMock()),
            '-FEE-': MagicMock(update=MagicMock()),
            '-IMPACT-': MagicMock(update=MagicMock()),
            '-NET-': MagicMock(update=MagicMock()),
            '-CLASS-': MagicMock(update=MagicMock()),
            '-LATENCY-': MagicMock(update=MagicMock()),
            '-MID-': MagicMock(update=MagicMock()),
            '-SPREAD-': MagicMock(update=MagicMock()),
            '-VOL-DISPLAY-': MagicMock(update=MagicMock()),
            '-LAST-UPDATE-': MagicMock(update=MagicMock()),
        }
        
        # Allow dictionary-style access to elements
        mock_window.__getitem__ = lambda self, key: elements.get(key, MagicMock())
        
        return mock_window

    def test_rapid_tick_ingestion(self, orderbook, mock_window):
        """Test that the system can handle rapid tick ingestion."""
        # Number of ticks to generate
        num_ticks = 100
        
        # Generate a series of ticks with random price movements
        ticks = []
        base_price = 50000.0
        
        for i in range(num_ticks):
            # Random price movement
            price_change = np.random.normal(0, 10.0)
            current_price = base_price + price_change
            
            tick = {
                "timestamp": f"2023-01-01T00:00:{i:02d}Z",
                "exchange": "OKX",
                "symbol": "BTC-USDT-SWAP",
                "asks": [
                    [str(current_price + 5.0), "1.0"],
                    [str(current_price + 15.0), "2.0"],
                    [str(current_price + 25.0), "3.0"],
                ],
                "bids": [
                    [str(current_price - 5.0), "1.5"],
                    [str(current_price - 15.0), "2.5"],
                    [str(current_price - 25.0), "3.5"],
                ]
            }
            ticks.append(tick)
        
        # Measure the time to process all ticks
        start_time = time.time()
        
        for tick in ticks:
            # Update the orderbook
            orderbook.update_from_tick(tick)
            
            # Create a snapshot
            snapshot = {
                "mid_price": orderbook.mid_price(),
                "spread": orderbook.spread(),
                "volatility": orderbook.rolling_volatility(),
                "timestamp": tick["timestamp"],
                "update_latency": 0.5  # Mock latency
            }
            
            # Update the UI
            update_market_data_display(mock_window, snapshot)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calculate average time per tick
        avg_time_per_tick = processing_time / num_ticks * 1000  # in milliseconds
        
        # Assert that the average processing time is below the target latency
        target_latency = 10.0  # 10ms per tick
        assert avg_time_per_tick < target_latency, f"Average processing time ({avg_time_per_tick:.2f}ms) exceeds target latency ({target_latency}ms)"
        
        # Verify that the UI was updated the correct number of times
        assert mock_window['-MID-'].update.call_count == num_ticks
        assert mock_window['-SPREAD-'].update.call_count == num_ticks
        assert mock_window['-VOL-DISPLAY-'].update.call_count == num_ticks
        assert mock_window['-LAST-UPDATE-'].update.call_count == num_ticks

    def test_trade_impact_calculation_latency(self, orderbook, mock_window):
        """Test that trade impact calculations complete within target latency."""
        # Number of calculations to perform
        num_calculations = 50
        
        # Order sizes to test
        order_sizes = np.linspace(100, 10000, num_calculations)
        
        # Sides to test
        sides = ['buy', 'sell'] * (num_calculations // 2)
        if len(sides) < num_calculations:
            sides.append('buy')
        
        # Measure the time to perform all calculations
        latencies = []
        
        for i in range(num_calculations):
            # Set up the mock window to return the current order size
            mock_window['-QTY-'].get = lambda size=order_sizes[i]: str(size)
            
            # Measure the time to calculate trade impact
            start_time = time.time()
            update_trade_impact(mock_window, sides[i])
            end_time = time.time()
            
            # Record the latency
            latency = (end_time - start_time) * 1000  # in milliseconds
            latencies.append(latency)
        
        # Calculate average and maximum latency
        avg_latency = np.mean(latencies)
        max_latency = np.max(latencies)
        
        # Define target latencies
        target_avg_latency = 20.0  # 20ms average
        target_max_latency = 50.0  # 50ms maximum
        
        # Assert that latencies are within targets
        assert avg_latency < target_avg_latency, f"Average latency ({avg_latency:.2f}ms) exceeds target ({target_avg_latency}ms)"
        assert max_latency < target_max_latency, f"Maximum latency ({max_latency:.2f}ms) exceeds target ({target_max_latency}ms)"
        
        # Verify that the UI was updated the correct number of times
        assert mock_window['-SLIP-'].update.call_count == num_calculations
        assert mock_window['-FEE-'].update.call_count == num_calculations
        assert mock_window['-IMPACT-'].update.call_count == num_calculations
        assert mock_window['-NET-'].update.call_count == num_calculations
        assert mock_window['-CLASS-'].update.call_count == num_calculations
        assert mock_window['-LATENCY-'].update.call_count == num_calculations

    def test_end_to_end_workflow(self, orderbook, mock_window):
        """Test the end-to-end workflow from market data to UI update."""
        # Generate a market data tick
        tick = {
            "timestamp": "2023-01-01T00:00:00Z",
            "exchange": "OKX",
            "symbol": "BTC-USDT-SWAP",
            "asks": [
                ["50005.0", "1.0"],
                ["50015.0", "2.0"],
                ["50025.0", "3.0"],
            ],
            "bids": [
                ["49995.0", "1.5"],
                ["49985.0", "2.5"],
                ["49975.0", "3.5"],
            ]
        }
        
        # Update the orderbook
        start_time = time.time()
        orderbook.update_from_tick(tick)
        
        # Create a snapshot
        snapshot = {
            "mid_price": orderbook.mid_price(),
            "spread": orderbook.spread(),
            "volatility": orderbook.rolling_volatility(),
            "timestamp": tick["timestamp"],
            "update_latency": (time.time() - start_time) * 1000  # in milliseconds
        }
        
        # Update the market data display
        update_market_data_display(mock_window, snapshot)
        
        # Calculate trade impact
        update_trade_impact(mock_window, 'buy')
        
        # Verify that all UI elements were updated
        assert mock_window['-MID-'].update.call_count == 1
        assert mock_window['-SPREAD-'].update.call_count == 1
        assert mock_window['-VOL-DISPLAY-'].update.call_count == 1
        assert mock_window['-LAST-UPDATE-'].update.call_count == 1
        assert mock_window['-SLIP-'].update.call_count == 1
        assert mock_window['-FEE-'].update.call_count == 1
        assert mock_window['-IMPACT-'].update.call_count == 1
        assert mock_window['-NET-'].update.call_count == 1
        assert mock_window['-CLASS-'].update.call_count == 1
        assert mock_window['-LATENCY-'].update.call_count == 1


if __name__ == "__main__":
    pytest.main(["-v", __file__])