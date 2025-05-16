#!/usr/bin/env python
"""
Unit tests for the fee module.
"""

import sys
import os
import unittest

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.fee import compute_fee, FEE_TIERS


class TestFee(unittest.TestCase):
    """Test cases for the fee module."""

    def test_taker_fees(self):
        """Test taker fee calculations for different tiers."""
        amount = 10000.0  # $10,000 USD
        price = 50000.0   # $50,000 per BTC
        
        # Test each tier
        for tier, (taker_rate, _) in FEE_TIERS.items():
            expected_fee = amount * (taker_rate / 100.0)
            calculated_fee = compute_fee(amount, price, tier, is_taker=True)
            
            self.assertAlmostEqual(
                calculated_fee, 
                expected_fee, 
                places=2,
                msg=f"Taker fee calculation failed for tier {tier}"
            )

    def test_maker_fees(self):
        """Test maker fee calculations for different tiers."""
        amount = 10000.0  # $10,000 USD
        price = 50000.0   # $50,000 per BTC
        
        # Test each tier
        for tier, (_, maker_rate) in FEE_TIERS.items():
            expected_fee = amount * (maker_rate / 100.0)
            calculated_fee = compute_fee(amount, price, tier, is_taker=False)
            
            self.assertAlmostEqual(
                calculated_fee, 
                expected_fee, 
                places=2,
                msg=f"Maker fee calculation failed for tier {tier}"
            )

    def test_invalid_tier(self):
        """Test that an error is raised for an invalid tier."""
        amount = 10000.0
        price = 50000.0
        invalid_tier = "INVALID_TIER"
        
        with self.assertRaises(ValueError):
            compute_fee(amount, price, invalid_tier)

    def test_zero_amount(self):
        """Test fee calculation with zero amount."""
        amount = 0.0
        price = 50000.0
        tier = "VIP0"
        
        fee = compute_fee(amount, price, tier)
        self.assertEqual(fee, 0.0)

    def test_large_amount(self):
        """Test fee calculation with a large amount."""
        amount = 1000000.0  # $1,000,000 USD
        price = 50000.0
        tier = "VIP0"
        
        # Expected taker fee: $1,000,000 * 0.08% = $800
        expected_fee = 800.0
        calculated_fee = compute_fee(amount, price, tier, is_taker=True)
        
        self.assertAlmostEqual(calculated_fee, expected_fee, places=2)


if __name__ == "__main__":
    unittest.main()