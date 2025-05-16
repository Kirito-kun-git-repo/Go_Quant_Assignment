#!/usr/bin/env python
"""
Maker/Taker Classification Module

This module provides functions to classify orders as "maker" or "taker" based on
orderbook liquidity and order size. It also includes an optional machine learning
approach using logistic regression.
"""

import numpy as np
import os
import sys
from typing import List, Dict, Tuple, Optional, Union
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Import the OrderBook class from the src directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.orderbook import OrderBook


def classify_order_heuristic(order_usd: float, orderbook: OrderBook, side: str) -> str:
    """
    Classify an order as "maker" or "taker" using a simple heuristic.
    
    Heuristic: If order_usd < best_level_size * mid_price, label as "maker", else "taker".
    The intuition is that small orders that can be filled at the best price level
    are more likely to be maker orders, while larger orders that consume multiple
    levels are more likely to be taker orders.
    
    Args:
        order_usd (float): The order size in USD
        orderbook (OrderBook): The current orderbook state
        side (str): The order side, either "buy" or "sell"
        
    Returns:
        str: "maker" or "taker"
        
    Raises:
        ValueError: If the side is not "buy" or "sell"
        ValueError: If the orderbook doesn't have the necessary data
    """
    if side not in ["buy", "sell"]:
        raise ValueError('Side must be either "buy" or "sell"')
    
    # Get the mid price
    mid_price = orderbook.mid_price()
    if mid_price is None:
        raise ValueError("Cannot classify order: orderbook has no mid price")
    
    # Get the best level based on the side
    if side == "buy":
        if not orderbook.asks:
            raise ValueError("Cannot classify buy order: orderbook has no asks")
        best_price, best_size = orderbook.asks[0]
    else:  # sell
        if not orderbook.bids:
            raise ValueError("Cannot classify sell order: orderbook has no bids")
        best_price, best_size = orderbook.bids[0]
    
    # Calculate the USD value of the best level using the actual price of the level
    best_level_usd = best_size * best_price
    
    # Apply the heuristic
    # Note: We use <= to classify orders equal to the best level as "maker"
    if order_usd <= best_level_usd:
        return "maker"
    else:
        return "taker"


def extract_orderbook_features(orderbook: OrderBook) -> List[float]:
    """
    Extract features from the orderbook for machine learning.
    
    Args:
        orderbook (OrderBook): The current orderbook state
        
    Returns:
        list: A list of features extracted from the orderbook
        
    Raises:
        ValueError: If the orderbook doesn't have the necessary data
    """
    # Check if orderbook has necessary data
    if not orderbook.asks or not orderbook.bids:
        raise ValueError("Cannot extract features: orderbook is incomplete")
    
    mid_price = orderbook.mid_price()
    if mid_price is None:
        raise ValueError("Cannot extract features: orderbook has no mid price")
    
    # Extract basic features
    spread = orderbook.spread() or 0
    spread_pct = (spread / mid_price) if mid_price > 0 else 0
    
    # Get top 5 levels from each side
    bids, asks = orderbook.depth(5)
    
    # Calculate bid and ask volumes
    bid_volumes = [size for _, size in bids]
    ask_volumes = [size for _, size in asks]
    
    # Calculate bid-ask imbalance
    total_bid_volume = sum(bid_volumes)
    total_ask_volume = sum(ask_volumes)
    volume_imbalance = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume) if (total_bid_volume + total_ask_volume) > 0 else 0
    
    # Calculate price distances from mid price
    bid_distances = [(mid_price - price) / mid_price for price, _ in bids] if bids else [0] * 5
    ask_distances = [(price - mid_price) / mid_price for price, _ in asks] if asks else [0] * 5
    
    # Ensure we have 5 levels by padding with zeros if necessary
    bid_volumes = bid_volumes + [0] * (5 - len(bid_volumes))
    ask_volumes = ask_volumes + [0] * (5 - len(ask_volumes))
    bid_distances = bid_distances + [0] * (5 - len(bid_distances))
    ask_distances = ask_distances + [0] * (5 - len(ask_distances))
    
    # Combine all features
    features = [
        mid_price,
        spread,
        spread_pct,
        volume_imbalance,
        *bid_volumes,
        *ask_volumes,
        *bid_distances,
        *ask_distances
    ]
    
    return features


def train_maker_taker_model(orderbooks: List[OrderBook], 
                           orders: List[Dict[str, Union[float, str, bool]]],
                           save_path: Optional[str] = None) -> Tuple[LogisticRegression, StandardScaler]:
    """
    Train a logistic regression model to classify orders as maker or taker.
    
    Args:
        orderbooks (list): List of OrderBook instances
        orders (list): List of dictionaries with keys 'size_usd', 'side', and 'is_maker'
        save_path (str, optional): Path to save the trained model
        
    Returns:
        tuple: (model, scaler) - The trained model and feature scaler
        
    Raises:
        ValueError: If the input data is invalid
    """
    if len(orderbooks) != len(orders):
        raise ValueError("Number of orderbooks must match number of orders")
    
    # Extract features and labels
    X = []
    y = []
    
    for i, (book, order) in enumerate(zip(orderbooks, orders)):
        try:
            # Extract orderbook features
            book_features = extract_orderbook_features(book)
            
            # Add order-specific features
            order_size = order['size_usd']
            side = order['side']
            
            # Get the best level size based on the side
            if side == "buy":
                best_price, best_size = book.asks[0]
            else:  # sell
                best_price, best_size = book.bids[0]
            
            # Calculate order size relative to best level using the actual price of the level
            mid_price = book.mid_price()
            best_level_usd = best_size * best_price
            relative_size = order_size / best_level_usd if best_level_usd > 0 else 1.0
            
            # Combine features
            features = book_features + [order_size, relative_size]
            X.append(features)
            
            # Get the label
            y.append(1 if order['is_maker'] else 0)
            
        except (ValueError, KeyError) as e:
            print(f"Skipping sample {i}: {e}")
    
    if not X or not y:
        raise ValueError("No valid samples for training")
    
    # Convert to numpy arrays
    X = np.array(X)
    y = np.array(y)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train logistic regression model
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_scaled, y)
    
    # Save the model if a path is provided
    if save_path:
        model_dir = os.path.dirname(save_path)
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump({'model': model, 'scaler': scaler}, save_path)
    
    return model, scaler


def classify_order_ml(order_usd: float, orderbook: OrderBook, side: str, 
                     model_path: str = '../models/maker_taker_model.joblib') -> str:
    """
    Classify an order as "maker" or "taker" using a trained machine learning model.
    
    Args:
        order_usd (float): The order size in USD
        orderbook (OrderBook): The current orderbook state
        side (str): The order side, either "buy" or "sell"
        model_path (str): Path to the trained model file
        
    Returns:
        str: "maker" or "taker"
        
    Raises:
        ValueError: If the side is not "buy" or "sell"
        FileNotFoundError: If the model file is not found
    """
    if side not in ["buy", "sell"]:
        raise ValueError('Side must be either "buy" or "sell"')
    
    # Check if model file exists
    if not os.path.exists(model_path):
        # Fall back to heuristic if model is not available
        return classify_order_heuristic(order_usd, orderbook, side)
    
    try:
        # Load the model and scaler
        model_data = joblib.load(model_path)
        model = model_data['model']
        scaler = model_data['scaler']
        
        # Extract orderbook features
        book_features = extract_orderbook_features(orderbook)
        
        # Add order-specific features
        mid_price = orderbook.mid_price()
        
        # Get the best level size based on the side
        if side == "buy":
            best_price, best_size = orderbook.asks[0]
        else:  # sell
            best_price, best_size = orderbook.bids[0]
        
        # Calculate order size relative to best level using the actual price of the level
        best_level_usd = best_size * best_price
        relative_size = order_usd / best_level_usd if best_level_usd > 0 else 1.0
        
        # Combine features
        features = book_features + [order_usd, relative_size]
        
        # Scale features
        features_scaled = scaler.transform([features])
        
        # Make prediction
        prediction = model.predict(features_scaled)[0]
        
        return "maker" if prediction == 1 else "taker"
        
    except Exception as e:
        # Fall back to heuristic if there's an error with the model
        print(f"Error using ML model: {e}. Falling back to heuristic.")
        return classify_order_heuristic(order_usd, orderbook, side)


if __name__ == "__main__":
    # Example usage
    from src.orderbook import OrderBook
    
    # Create a sample orderbook
    book = OrderBook("BTC-USDT-SWAP")
    
    # Sample tick data
    sample_tick = {
        "timestamp": "2023-01-01T00:00:00Z",
        "exchange": "OKX",
        "symbol": "BTC-USDT-SWAP",
        "asks": [
            ["50000.0", "1.0"],   # $50,000 per BTC, 1.0 BTC available
            ["50010.0", "2.0"],   # $50,010 per BTC, 2.0 BTC available
            ["50020.0", "3.0"],   # $50,020 per BTC, 3.0 BTC available
        ],
        "bids": [
            ["49990.0", "1.5"],   # $49,990 per BTC, 1.5 BTC available
            ["49980.0", "2.5"],   # $49,980 per BTC, 2.5 BTC available
            ["49970.0", "3.5"],   # $49,970 per BTC, 3.5 BTC available
        ]
    }
    
    book.update_from_tick(sample_tick)
    
    # Test the heuristic classification
    small_order = 25000.0  # $25,000 USD (should be "maker")
    large_order = 150000.0  # $150,000 USD (should be "taker")
    
    small_classification = classify_order_heuristic(small_order, book, "buy")
    large_classification = classify_order_heuristic(large_order, book, "buy")
    
    print(f"Small order ({small_order} USD) classification: {small_classification}")
    print(f"Large order ({large_order} USD) classification: {large_classification}")