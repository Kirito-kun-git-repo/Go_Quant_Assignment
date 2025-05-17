#!/usr/bin/env python
"""
Trading Simulator UI

This module provides a graphical user interface for the trading simulator
using PySimpleGUI. It allows users to select trading parameters and view
real-time market impact and cost estimates.
"""

import os
import sys
import json
import time
import asyncio
import threading
import logging
import PySimpleGUI as sg
from typing import Dict, List, Any, Optional, Tuple

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.orderbook import OrderBook
from models.fee import compute_fee
from models.slippage import simulate_slippage
from models.impact import calculate_total_impact
from models.maker_taker import classify_order_heuristic

# Define constants
EXCHANGES = ['OKX']
SYMBOLS = ['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP']
FEE_TIERS = ['VIP0', 'VIP1', 'VIP2', 'VIP3', 'VIP4', 'VIP5']
DEFAULT_QTY = '100'
DEFAULT_VOL = 'auto'
DEFAULT_TIER = 'VIP0'
DEFAULT_EXCHANGE = 'OKX'
DEFAULT_SYMBOL = 'BTC-USDT-SWAP'

# Global variables
orderbook = OrderBook(DEFAULT_SYMBOL)
stop_event = threading.Event()


def create_layout() -> List[List[Any]]:
    """
    Create the layout for the PySimpleGUI window.
    
    Returns:
        list: The layout configuration
    """
    # Left column - Input parameters
    left_column = [
        [sg.Text('Exchange:'), sg.DropDown(EXCHANGES, default_value=DEFAULT_EXCHANGE, key='-EXCHANGE-', size=(15, 1))],
        [sg.Text('Symbol:'), sg.InputCombo(SYMBOLS, default_value=DEFAULT_SYMBOL, key='-SYMBOL-', size=(15, 1))],
        [sg.Text('Quantity (USD):'), sg.Input(DEFAULT_QTY, key='-QTY-', size=(15, 1))],
        [sg.Text('Volume (BTC):'), sg.Input(DEFAULT_VOL, key='-VOL-', size=(15, 1))],
        [sg.Text('Fee Tier:'), sg.InputCombo(FEE_TIERS, default_value=DEFAULT_TIER, key='-TIER-', size=(15, 1))],
        [sg.Button('Buy', key='-BUY-', button_color=('white', 'green')), 
         sg.Button('Sell', key='-SELL-', button_color=('white', 'red'))],
    ]
    
    # Right column - Output metrics
    right_column = [
        [sg.Text('Market Data', font=('Helvetica', 12, 'bold'))],
        [sg.Text('Mid Price: $0.00', key='-MID-')],
        [sg.Text('Spread: $0.00', key='-SPREAD-')],
        [sg.Text('Volatility: 0.00%', key='-VOL-DISPLAY-')],
        [sg.Text('Last Update: N/A', key='-LAST-UPDATE-')],
        [sg.HorizontalSeparator()],
        [sg.Text('Trade Impact', font=('Helvetica', 12, 'bold'))],
        [sg.Text('Slippage: $0.00', key='-SLIP-')],
        [sg.Text('Fees: $0.00', key='-FEE-')],
        [sg.Text('Market Impact: $0.00', key='-IMPACT-')],
        [sg.Text('Net Cost: $0.00', key='-NET-')],
        [sg.Text('Classification: N/A', key='-CLASS-')],
        [sg.Text('Estimated Latency: 0ms', key='-LATENCY-')],
    ]
    
    # Combine columns
    layout = [
        [sg.Text('Trading Simulator', font=('Helvetica', 16, 'bold'), justification='center', expand_x=True)],
        [sg.Column(left_column), sg.VerticalSeparator(), sg.Column(right_column)],
        [sg.Button('Start Feed', key='-START-'), sg.Button('Stop Feed', key='-STOP-'), sg.Button('Exit')]
    ]
    
    return layout


async def fetch_market_data(window: sg.Window) -> None:
    """
    Simulate fetching market data and updating the orderbook.
    
    In a real implementation, this would connect to the WebSocket API
    and receive real market data.
    
    Args:
        window (sg.Window): The PySimpleGUI window to update
    """
    import logging
    import random
    import numpy as np
    
    logger = logging.getLogger('trade_simulator')
    logger.info("Market data feed started")
    
    # Initialize market parameters
    tick_count = 0
    symbol = orderbook.symbol
    
    # Set base prices for different symbols
    base_prices = {
        "BTC-USDT-SWAP": 50000.0,
        "ETH-USDT-SWAP": 3000.0,
        "SOL-USDT-SWAP": 100.0
    }
    
    # Set volatility parameters for different symbols
    volatility = {
        "BTC-USDT-SWAP": 50.0,  # $50 standard deviation
        "ETH-USDT-SWAP": 20.0,  # $20 standard deviation
        "SOL-USDT-SWAP": 2.0    # $2 standard deviation
    }
    
    # Initialize price with random walk
    current_price = base_prices.get(symbol, 50000.0)
    
    # Create a more realistic order book with multiple levels
    def generate_orderbook_levels(center_price, symbol, num_levels=10):
        vol = volatility.get(symbol, 50.0)
        
        # Generate spreads that increase as we move away from mid price
        # This simulates real orderbooks where liquidity is concentrated near the mid price
        spread_base = vol * 0.01  # Base spread is 1% of volatility
        
        asks = []
        bids = []
        
        for i in range(num_levels):
            # Spread increases quadratically as we move away from mid price
            level_spread = spread_base * (1 + 0.5 * i * i)
            
            # Price levels
            ask_price = center_price + level_spread * (i + 1)
            bid_price = center_price - level_spread * (i + 1)
            
            # Size decreases as we move away from mid price
            base_size = 1.0 / (symbol.startswith("BTC") and 1 or (symbol.startswith("ETH") and 10 or 100))
            size_factor = 1.0 / (1 + 0.2 * i)
            
            ask_size = base_size * size_factor * (1 + 0.1 * random.random())
            bid_size = base_size * size_factor * (1 + 0.1 * random.random())
            
            asks.append([str(ask_price), str(ask_size)])
            bids.append([str(bid_price), str(bid_size)])
        
        return asks, bids
    
    while not stop_event.is_set():
        try:
            # Get current symbol from orderbook
            symbol = orderbook.symbol
            
            # Update tick count
            tick_count += 1
            
            # Simulate price movement with random walk
            vol = volatility.get(symbol, 50.0)
            price_change = np.random.normal(0, vol * 0.05)  # Random walk with 5% of volatility (increased from 1%)
            current_price += price_change
            
            # Ensure price doesn't go too far from base price (mean reversion)
            base_price = base_prices.get(symbol, 50000.0)
            mean_reversion = 0.01 * (base_price - current_price)  # 1% reversion to mean
            current_price += mean_reversion
            
            # Ensure price is positive
            current_price = max(current_price, 0.01 * base_price)
            
            # Generate orderbook levels
            asks, bids = generate_orderbook_levels(current_price, symbol)
            
            # Create a synthetic tick
            tick = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
                "exchange": "OKX",
                "symbol": symbol,
                "asks": asks,
                "bids": bids
            }
            
            # Measure latency of orderbook update
            start_time = time.time()
            
            # Update the orderbook
            orderbook.update_from_tick(tick)
            
            # Calculate update latency
            update_latency = (time.time() - start_time) * 1000  # in milliseconds
            
            # Create a snapshot of the current state
            snapshot = {
                "mid_price": orderbook.mid_price(),
                "spread": orderbook.spread(),
                "volatility": orderbook.rolling_volatility(),
                "timestamp": tick["timestamp"],
                "update_latency": update_latency
            }
            
            logger.debug(f"Generated tick for {symbol}: mid={snapshot['mid_price']:.2f}, spread={snapshot['spread']:.2f}")
            
            # Send the snapshot to the main thread
            window.write_event_value('-TICK-', snapshot)
            
            # Wait a bit before the next update (randomize slightly for realism)
            await asyncio.sleep(0.5 + 0.5 * random.random())
            
        except Exception as e:
            logger.error(f"Error in market data thread: {e}", exc_info=True)
            await asyncio.sleep(5.0)  # Wait longer on error


def start_market_data_thread(window: sg.Window) -> threading.Thread:
    """
    Start a background thread to fetch market data.
    
    Args:
        window (sg.Window): The PySimpleGUI window to update
        
    Returns:
        threading.Thread: The started thread
    """
    stop_event.clear()
    
    def run_async_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(fetch_market_data(window))
    
    thread = threading.Thread(target=run_async_loop, daemon=True)
    thread.start()
    return thread


def update_market_data_display(window: sg.Window, snapshot: Dict[str, Any]) -> None:
    """
    Update the market data display with the latest snapshot.
    
    Args:
        window (sg.Window): The PySimpleGUI window to update
        snapshot (dict): The market data snapshot
    """
    import logging
    logger = logging.getLogger('trade_simulator')
    
    mid_price = snapshot.get("mid_price", 0)
    spread = snapshot.get("spread", 0)
    volatility = snapshot.get("volatility", 0)
    timestamp = snapshot.get("timestamp", "N/A")
    update_latency = snapshot.get("update_latency", 0)
    
    # Format timestamp for display (remove milliseconds and 'Z')
    if 'T' in timestamp:
        display_time = timestamp.split('.')[0].replace('T', ' ').replace('Z', '')
    else:
        display_time = timestamp
    
    # Update the display with formatted values
    window['-MID-'].update(f'Mid Price: ${mid_price:.2f}')
    window['-SPREAD-'].update(f'Spread: ${spread:.2f}')
    
    # Format volatility as percentage if available
    if volatility is not None:
        # Volatility is already in percentage form (as a decimal) from our updated calculation
        # Multiply by 100 to display as percentage
        vol_pct = volatility * 100
        window['-VOL-DISPLAY-'].update(f'Volatility: {vol_pct:.2f}%')
    else:
        window['-VOL-DISPLAY-'].update('Volatility: N/A')
    
    # Update timestamp and add update latency if available
    latency_info = f" (update: {update_latency:.1f}ms)" if update_latency else ""
    window['-LAST-UPDATE-'].update(f'Last Update: {display_time}{latency_info}')
    
    # Log detailed information at debug level
    vol_str = f"{volatility:.6f}" if volatility is not None else "N/A"
    logger.debug(f"Updated market display - Mid: ${mid_price:.2f}, Spread: ${spread:.2f}, " +
                f"Volatility: {vol_str}, Update Latency: {update_latency:.2f}ms")


def update_trade_impact(window: sg.Window, side: str) -> None:
    """
    Update the trade impact display based on the current orderbook and inputs.
    
    Args:
        window (sg.Window): The PySimpleGUI window to update
        side (str): The trade side ('buy' or 'sell')
    """
    import logging
    logger = logging.getLogger('trade_simulator')
    
    try:
        # Get input values
        qty_usd = float(window['-QTY-'].get())
        tier = window['-TIER-'].get()
        
        # Calculate metrics
        start_time = time.time()
        
        # Fetch latest OrderBook snapshot
        logger.debug(f"Processing {side} order for {qty_usd} USD with tier {tier}")
        logger.debug(f"Current OrderBook state: mid_price={orderbook.mid_price()}, spread={orderbook.spread()}")
        
        # Slippage calculation
        slippage_start = time.time()
        slippage = simulate_slippage(qty_usd, orderbook, side)
        slippage_time = (time.time() - slippage_start) * 1000
        logger.debug(f"Slippage calculation took {slippage_time:.2f}ms, result: ${slippage:.2f}")
        
        # Fee calculation
        fee_start = time.time()
        mid_price = orderbook.mid_price() or 0
        fee = compute_fee(qty_usd, mid_price, tier, is_taker=True)  # Default to taker for initial calculation
        fee_time = (time.time() - fee_start) * 1000
        logger.debug(f"Fee calculation took {fee_time:.2f}ms, result: ${fee:.2f}")
        
        # Market impact calculation
        impact_start = time.time()
        try:
            # Convert USD to base currency quantity using mid price
            base_qty = qty_usd / orderbook.mid_price() if orderbook.mid_price() else 0
            perm_impact, temp_impact, total_impact = calculate_total_impact(orderbook, base_qty)
            logger.debug(f"Impact breakdown - Permanent: ${perm_impact:.2f}, Temporary: ${temp_impact:.2f}")
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to calculate market impact: {e}")
            perm_impact, temp_impact, total_impact = 0, 0, 0
        impact_time = (time.time() - impact_start) * 1000
        logger.debug(f"Market impact calculation took {impact_time:.2f}ms, result: ${total_impact:.2f}")
        
        # Order classification
        class_start = time.time()
        classification = classify_order_heuristic(qty_usd, orderbook, side)
        class_time = (time.time() - class_start) * 1000
        logger.debug(f"Classification took {class_time:.2f}ms, result: {classification}")
        
        # Recalculate fee based on maker/taker classification
        is_taker = classification == "taker"
        fee = compute_fee(qty_usd, mid_price, tier, is_taker=is_taker)
        
        # Net cost calculation (sum of slippage, fees, and temporary impact)
        # Note: We only include temporary impact in net cost as permanent impact is a market effect
        net_cost = slippage + fee + temp_impact
        
        # Total latency
        latency = (time.time() - start_time) * 1000  # in milliseconds
        logger.debug(f"Total processing time: {latency:.2f}ms")
        
        # Update the UI in real-time
        window['-SLIP-'].update(f'Slippage: ${slippage:.2f}')
        window['-FEE-'].update(f'Fees: ${fee:.2f}')
        window['-IMPACT-'].update(f'Market Impact: ${total_impact:.2f}')
        window['-NET-'].update(f'Net Cost: ${net_cost:.2f}')
        window['-CLASS-'].update(f'Classification: {classification}')
        window['-LATENCY-'].update(f'Estimated Latency: {latency:.2f}ms')
        
    except Exception as e:
        logger.error(f"Error updating trade impact: {e}", exc_info=True)
        # Show error in the UI
        window['-SLIP-'].update('Slippage: Error')
        window['-FEE-'].update('Fees: Error')
        window['-IMPACT-'].update('Market Impact: Error')
        window['-NET-'].update('Net Cost: Error')
        window['-CLASS-'].update('Classification: Error')
        window['-LATENCY-'].update('Estimated Latency: Error')


def setup_logging() -> None:
    """
    Set up logging configuration for the application.
    """
    import logging
    
    # Create logger
    logger = logging.getLogger('trade_simulator')
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler('trade_simulator.log')
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatters
    console_format = logging.Formatter('%(levelname)s - %(message)s')
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add formatters to handlers
    console_handler.setFormatter(console_format)
    file_handler.setFormatter(file_format)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info("Logging initialized")


def main() -> None:
    """
    Main function to run the trading simulator UI.
    """
    # Set up logging
    setup_logging()
    logger = logging.getLogger('trade_simulator')
    
    # Set the theme
    sg.theme('DarkBlue')
    
    # Create the window
    layout = create_layout()
    window = sg.Window('Trading Simulator', layout, finalize=True)
    
    # Initialize variables
    market_data_thread = None
    last_update_time = time.time()
    update_interval = 0.5  # Update trade impact every 0.5 seconds when market data changes
    
    logger.info("Trading Simulator started")
    
    # Event loop
    while True:
        event, values = window.read(timeout=100)
        
        if event == sg.WIN_CLOSED or event == 'Exit':
            logger.info("Application exit requested")
            break
            
        elif event == '-START-':
            if market_data_thread is None or not market_data_thread.is_alive():
                logger.info("Starting market data feed")
                market_data_thread = start_market_data_thread(window)
                window['-START-'].update(disabled=True)
                window['-STOP-'].update(disabled=False)
        
        elif event == '-STOP-':
            if market_data_thread and market_data_thread.is_alive():
                logger.info("Stopping market data feed")
                stop_event.set()
                market_data_thread.join(timeout=1.0)
                window['-START-'].update(disabled=False)
                window['-STOP-'].update(disabled=True)
        
        elif event == '-TICK-':
            # Get the snapshot from the event
            snapshot = values['-TICK-']
            logger.debug(f"Received tick: mid_price={snapshot.get('mid_price')}, spread={snapshot.get('spread')}")
            
            # Update the market data display
            update_market_data_display(window, snapshot)
            
            # Update trade impact if we have valid inputs and enough time has passed
            current_time = time.time()
            if current_time - last_update_time >= update_interval:
                try:
                    # Get the current quantity from the UI
                    qty = float(values['-QTY-'])
                    if qty > 0:
                        # Get the current side (default to buy for auto-updates)
                        side = 'buy'  # Default side for auto-updates
                        logger.debug(f"Auto-updating trade impact for {side} order of {qty} USD")
                        update_trade_impact(window, side)
                        last_update_time = current_time
                except (ValueError, TypeError) as e:
                    logger.debug(f"Skipping auto-update due to invalid input: {e}")
        
        elif event == '-BUY-':
            logger.info("Buy button clicked")
            update_trade_impact(window, 'buy')
            
        elif event == '-SELL-':
            logger.info("Sell button clicked")
            update_trade_impact(window, 'sell')
            
        # Handle symbol change
        elif event == '-SYMBOL-':
            symbol = values['-SYMBOL-']
            logger.info(f"Symbol changed to {symbol}")
            # Update the orderbook with the new symbol
            global orderbook
            orderbook = OrderBook(symbol)
            # Clear the display until we get new data
            window['-MID-'].update('Mid Price: $0.00')
            window['-SPREAD-'].update('Spread: $0.00')
            window['-VOL-DISPLAY-'].update('Volatility: 0.00%')
            window['-LAST-UPDATE-'].update('Last Update: N/A')
    
    # Clean up
    logger.info("Cleaning up resources")
    stop_event.set()
    if market_data_thread and market_data_thread.is_alive():
        market_data_thread.join(timeout=1.0)
    
    window.close()
    logger.info("Application terminated")


if __name__ == "__main__":
    main()