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
    tick_count = 0
    base_price = 50000.0  # Starting price for BTC
    
    while not stop_event.is_set():
        try:
            # Simulate market data with some random price movement
            tick_count += 1
            price_change = (tick_count % 5 - 2) * 10.0  # Oscillate between -20 and +20
            current_price = base_price + price_change
            
            # Create a synthetic tick
            tick = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
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
            
            # Update the orderbook
            orderbook.update_from_tick(tick)
            
            # Create a snapshot of the current state
            snapshot = {
                "mid_price": orderbook.mid_price(),
                "spread": orderbook.spread(),
                "volatility": orderbook.rolling_volatility(),
                "timestamp": tick["timestamp"]
            }
            
            # Send the snapshot to the main thread
            window.write_event_value('-TICK-', snapshot)
            
            # Wait a bit before the next update
            await asyncio.sleep(1.0)
            
        except Exception as e:
            print(f"Error in market data thread: {e}")
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
    mid_price = snapshot.get("mid_price", 0)
    spread = snapshot.get("spread", 0)
    volatility = snapshot.get("volatility", 0)
    timestamp = snapshot.get("timestamp", "N/A")
    
    # Update the display
    window['-MID-'].update(f'Mid Price: ${mid_price:.2f}')
    window['-SPREAD-'].update(f'Spread: ${spread:.2f}')
    
    # Format volatility as percentage if available
    if volatility is not None:
        vol_pct = volatility / mid_price * 100 if mid_price else 0
        window['-VOL-DISPLAY-'].update(f'Volatility: {vol_pct:.2f}%')
    else:
        window['-VOL-DISPLAY-'].update('Volatility: N/A')
    
    window['-LAST-UPDATE-'].update(f'Last Update: {timestamp}')


def update_trade_impact(window: sg.Window, side: str) -> None:
    """
    Update the trade impact display based on the current orderbook and inputs.
    
    Args:
        window (sg.Window): The PySimpleGUI window to update
        side (str): The trade side ('buy' or 'sell')
    """
    try:
        # Get input values
        qty_usd = float(window['-QTY-'].get())
        tier = window['-TIER-'].get()
        
        # Calculate metrics
        start_time = time.time()
        
        # Slippage
        slippage = simulate_slippage(qty_usd, orderbook, side)
        
        # Fee
        monthly_volume = 1000000.0  # Placeholder for monthly volume
        is_taker = True  # Assume taker for now
        fee = compute_fee(qty_usd, monthly_volume, tier, is_taker)
        
        # Market impact
        try:
            perm_impact, temp_impact, total_impact = calculate_total_impact(orderbook, qty_usd / orderbook.mid_price())
        except (ValueError, TypeError):
            perm_impact, temp_impact, total_impact = 0, 0, 0
        
        # Classification
        classification = classify_order_heuristic(qty_usd, orderbook, side)
        
        # Net cost
        net_cost = slippage + fee + total_impact
        
        # Latency
        latency = (time.time() - start_time) * 1000  # in milliseconds
        
        # Update the display
        window['-SLIP-'].update(f'Slippage: ${slippage:.2f}')
        window['-FEE-'].update(f'Fees: ${fee:.2f}')
        window['-IMPACT-'].update(f'Market Impact: ${total_impact:.2f}')
        window['-NET-'].update(f'Net Cost: ${net_cost:.2f}')
        window['-CLASS-'].update(f'Classification: {classification}')
        window['-LATENCY-'].update(f'Estimated Latency: {latency:.2f}ms')
        
    except Exception as e:
        print(f"Error updating trade impact: {e}")
        # Show error in the UI
        window['-SLIP-'].update('Slippage: Error')
        window['-FEE-'].update('Fees: Error')
        window['-IMPACT-'].update('Market Impact: Error')
        window['-NET-'].update('Net Cost: Error')
        window['-CLASS-'].update('Classification: Error')
        window['-LATENCY-'].update('Estimated Latency: Error')


def main() -> None:
    """
    Main function to run the trading simulator UI.
    """
    # Set the theme
    sg.theme('DarkBlue')
    
    # Create the window
    layout = create_layout()
    window = sg.Window('Trading Simulator', layout, finalize=True)
    
    # Initialize variables
    market_data_thread = None
    
    # Event loop
    while True:
        event, values = window.read(timeout=100)
        
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
            
        elif event == '-START-':
            if market_data_thread is None or not market_data_thread.is_alive():
                market_data_thread = start_market_data_thread(window)
                window['-START-'].update(disabled=True)
                window['-STOP-'].update(disabled=False)
        
        elif event == '-STOP-':
            if market_data_thread and market_data_thread.is_alive():
                stop_event.set()
                market_data_thread.join(timeout=1.0)
                window['-START-'].update(disabled=False)
                window['-STOP-'].update(disabled=True)
        
        elif event == '-TICK-':
            snapshot = values['-TICK-']
            update_market_data_display(window, snapshot)
            
            # Also update trade impact if we have valid inputs
            try:
                qty = float(values['-QTY-'])
                if qty > 0:
                    update_trade_impact(window, 'buy')  # Default to buy side for updates
            except (ValueError, TypeError):
                pass
        
        elif event == '-BUY-':
            update_trade_impact(window, 'buy')
            
        elif event == '-SELL-':
            update_trade_impact(window, 'sell')
    
    # Clean up
    stop_event.set()
    if market_data_thread and market_data_thread.is_alive():
        market_data_thread.join(timeout=1.0)
    
    window.close()


if __name__ == "__main__":
    main()