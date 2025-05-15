#!/usr/bin/env python
"""
Data Ingestion Module for Trade Simulator

This module connects to a WebSocket endpoint to receive real-time market data,
specifically L2 orderbook data for BTC-USDT-SWAP from OKX.
It logs the raw JSON messages to a file for further processing.
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path

import websockets

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "data_ingest.log"),
        logging.StreamHandler()
    ]
)

# Configure raw data logging
raw_logger = logging.getLogger("raw_data")
raw_logger.setLevel(logging.INFO)
raw_handler = logging.FileHandler(log_dir / "raw_ticks.log")
raw_handler.setFormatter(logging.Formatter('%(message)s'))
raw_logger.addHandler(raw_handler)
raw_logger.propagate = False  # Don't propagate to root logger

logger = logging.getLogger(__name__)

# WebSocket endpoint
WS_URL = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"

# Maximum reconnection attempts
MAX_RECONNECT_ATTEMPTS = 10


async def connect_websocket():
    """
    Connect to the WebSocket endpoint with exponential backoff on failures.
    """
    reconnect_attempt = 0
    
    while reconnect_attempt < MAX_RECONNECT_ATTEMPTS:
        try:
            if reconnect_attempt > 0:
                # Calculate backoff time with jitter
                backoff_time = min(2 ** reconnect_attempt + random.uniform(0, 1), 60)
                logger.info(f"Reconnecting in {backoff_time:.2f} seconds (attempt {reconnect_attempt}/{MAX_RECONNECT_ATTEMPTS})")
                await asyncio.sleep(backoff_time)
            
            logger.info(f"Connecting to {WS_URL}")
            async with websockets.connect(WS_URL) as websocket:
                logger.info("Connection established")
                reconnect_attempt = 0  # Reset reconnect counter on successful connection
                
                while True:
                    message = await websocket.recv()
                    # Log the raw message
                    raw_logger.info(message)
                    
                    # Optional: Parse and log message details for monitoring
                    try:
                        data = json.loads(message)
                        if reconnect_attempt == 0 and 'type' in data and data['type'] == 'snapshot':
                            logger.info(f"Received initial snapshot with {len(data.get('asks', []))} asks and {len(data.get('bids', []))} bids")
                    except json.JSONDecodeError:
                        logger.warning("Received non-JSON message")
                    
        except websockets.exceptions.ConnectionClosed as e:
            reconnect_attempt += 1
            logger.warning(f"Connection closed: {e}. Attempt {reconnect_attempt}/{MAX_RECONNECT_ATTEMPTS}")
        
        except Exception as e:
            reconnect_attempt += 1
            logger.error(f"Error: {e}. Attempt {reconnect_attempt}/{MAX_RECONNECT_ATTEMPTS}")
    
    logger.error(f"Failed to connect after {MAX_RECONNECT_ATTEMPTS} attempts")


async def main():
    """
    Main entry point for the data ingestion service.
    """
    logger.info("Starting data ingestion service")
    await connect_websocket()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Data ingestion service stopped by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")