#!/usr/bin/env python
"""
Walkthrough Video Recording Script

This script provides instructions for recording a walkthrough video
of the trading simulator.
"""

import os
import sys
import time
import subprocess

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def print_walkthrough_script():
    """Print the walkthrough script for the video."""
    script = """
TRADING SIMULATOR WALKTHROUGH SCRIPT
====================================

Introduction (30 seconds)
-------------------------
- Hello and welcome to this walkthrough of our Trading Simulator
- This simulator helps traders understand market impact and trading costs
- It provides real-time metrics and visualization of orderbook data

Project Structure (30 seconds)
-----------------------------
- The simulator is built with Python 3.10
- It uses PySimpleGUI for the user interface
- The core components include:
  * OrderBook management
  * Fee calculation
  * Slippage simulation
  * Market impact modeling
  * Maker/taker classification

Running the Simulator (1 minute)
------------------------------
- Let's start the simulator with: python src/app.py
- The UI shows two main sections:
  * Left: Input parameters (exchange, symbol, quantity, etc.)
  * Right: Output metrics (market data and trade impact)
- We can start the market data feed by clicking "Start Feed"

Market Data Visualization (1 minute)
----------------------------------
- The simulator now shows real-time market data:
  * Mid price: The average of best bid and ask
  * Spread: The difference between best bid and ask
  * Volatility: The standard deviation of mid prices
- Notice how the values update in real-time
- We can change the symbol to see different market data

Trade Impact Calculation (1 minute)
---------------------------------
- Let's enter a quantity and click "Buy"
- The simulator calculates:
  * Slippage: The difference between execution price and mid price
  * Fees: Based on the selected fee tier
  * Market Impact: Using the Almgren-Chriss model
  * Net Cost: The total trading cost
- We can also see if the order is classified as "maker" or "taker"

Performance Metrics (30 seconds)
-----------------------------
- The simulator measures and displays latency for all operations
- This helps traders understand the performance characteristics
- We can see how latency changes with different order sizes

Conclusion (30 seconds)
---------------------
- This simulator provides valuable insights for algorithmic traders
- It helps understand and optimize trading costs
- Future improvements include:
  * WebSocket connection to real exchange APIs
  * Historical data replay
  * Enhanced visualization with charts
  * Support for different order types

Thank you for watching this walkthrough!
"""
    print(script)


def start_simulator():
    """Start the trading simulator application."""
    simulator_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')
    
    # Start the simulator in a separate process
    process = subprocess.Popen([sys.executable, simulator_path])
    
    return process


def main():
    """Main function to guide the walkthrough recording."""
    print("=== TRADING SIMULATOR WALKTHROUGH RECORDING GUIDE ===")
    print("\nThis script will help you record a 5-minute walkthrough video of the trading simulator.")
    print("\nInstructions:")
    print("1. Start your screen recording software")
    print("2. Press Enter to start the simulator")
    input("Press Enter to continue...")
    
    # Start the simulator
    simulator = start_simulator()
    
    # Print the walkthrough script
    print_walkthrough_script()
    
    print("\nFollow the script above for your walkthrough.")
    print("When you're done, press Enter to close the simulator.")
    input("Press Enter to close the simulator...")
    
    # Terminate the simulator
    simulator.terminate()
    print("Simulator terminated.")
    print("Don't forget to stop your screen recording software!")


if __name__ == "__main__":
    main()