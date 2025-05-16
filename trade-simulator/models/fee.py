#!/usr/bin/env python
"""
Fee Module for Trade Simulator

This module calculates trading fees based on OKX fee tiers.
"""

from typing import Dict, Tuple


# OKX fee tiers (taker, maker) in percentage
# Source: OKX documentation
FEE_TIERS: Dict[str, Tuple[float, float]] = {
    "VIP0": (0.08, 0.02),    # Taker: 0.08%, Maker: 0.02%
    "VIP1": (0.06, 0.01),    # Taker: 0.06%, Maker: 0.01%
    "VIP2": (0.05, 0.00),    # Taker: 0.05%, Maker: 0.00%
    "VIP3": (0.04, 0.00),    # Taker: 0.04%, Maker: 0.00%
    "VIP4": (0.03, 0.00),    # Taker: 0.03%, Maker: 0.00%
    "VIP5": (0.02, 0.00),    # Taker: 0.02%, Maker: 0.00%
}


def compute_fee(amount_usd: float, price: float, tier: str, is_taker: bool = True) -> float:
    """
    Compute the trading fee based on the amount, price, and fee tier.
    
    Args:
        amount_usd (float): The trade amount in USD
        price (float): The execution price
        tier (str): The fee tier (e.g., "VIP0", "VIP1", etc.)
        is_taker (bool): Whether the order is a taker order (True) or maker order (False)
        
    Returns:
        float: The fee amount in USD
        
    Raises:
        ValueError: If the tier is not recognized
    """
    if tier not in FEE_TIERS:
        raise ValueError(f"Unknown fee tier: {tier}. Valid tiers are: {', '.join(FEE_TIERS.keys())}")
    
    # Get the appropriate fee rate (taker or maker)
    taker_fee, maker_fee = FEE_TIERS[tier]
    fee_rate = taker_fee if is_taker else maker_fee
    
    # Convert percentage to decimal
    fee_rate_decimal = fee_rate / 100.0
    
    # Calculate fee
    fee_amount = amount_usd * fee_rate_decimal
    
    return fee_amount


if __name__ == "__main__":
    # Example usage
    amount = 10000.0  # $10,000 USD
    price = 50000.0   # $50,000 per BTC
    tier = "VIP0"
    
    taker_fee = compute_fee(amount, price, tier, is_taker=True)
    maker_fee = compute_fee(amount, price, tier, is_taker=False)
    
    print(f"For a {amount} USD trade at price {price}:")
    print(f"Taker fee ({tier}): ${taker_fee:.2f} USD")
    print(f"Maker fee ({tier}): ${maker_fee:.2f} USD")