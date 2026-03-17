#!/usr/bin/env python3
"""Test audit period calculation"""

from datetime import datetime
import sys
sys.path.insert(0, '.')
from honeybadger_server import get_audit_period

def test_audit_period():
    """Test audit period mapping"""
    audit_months = [3, 9]

    # Test 2.2: Upload during audit month
    result = get_audit_period(datetime(2026, 3, 15), audit_months)
    assert result == "2026-03", f"During audit month: expected 2026-03, got {result}"
    print("✓ 2.2: Upload during audit month - PASS")

    # Test 2.3: Upload between audit months
    result = get_audit_period(datetime(2026, 4, 10), audit_months)
    assert result == "2026-09", f"Between audit months: expected 2026-09, got {result}"
    print("✓ 2.3: Upload between audit months - PASS")

    result = get_audit_period(datetime(2026, 5, 15), audit_months)
    assert result == "2026-09", f"Between audit months: expected 2026-09, got {result}"
    print("✓ 2.3: Upload between audit months (May) - PASS")

    # Test 2.4: Upload after last audit month of year
    result = get_audit_period(datetime(2026, 10, 5), audit_months)
    assert result == "2027-03", f"After last audit month: expected 2027-03, got {result}"
    print("✓ 2.4: Upload after last audit month - PASS")

    result = get_audit_period(datetime(2026, 12, 31), audit_months)
    assert result == "2027-03", f"December: expected 2027-03, got {result}"
    print("✓ 2.4: Upload in December - PASS")

    # Test 2.5: Upload before first audit month of year
    result = get_audit_period(datetime(2026, 1, 15), audit_months)
    assert result == "2026-03", f"Before first audit month: expected 2026-03, got {result}"
    print("✓ 2.5: Upload before first audit month - PASS")

    result = get_audit_period(datetime(2026, 2, 20), audit_months)
    assert result == "2026-03", f"February: expected 2026-03, got {result}"
    print("✓ 2.5: Upload in February - PASS")

    # Test 2.6: Year boundary edge cases
    result = get_audit_period(datetime(2025, 12, 31), audit_months)
    assert result == "2026-03", f"Year boundary: expected 2026-03, got {result}"
    print("✓ 2.6: Year boundary (Dec 31) - PASS")

    result = get_audit_period(datetime(2026, 9, 30), audit_months)
    assert result == "2026-09", f"Last day of audit month: expected 2026-09, got {result}"
    print("✓ 2.6: Last day of audit month - PASS")

    # Additional edge case: single audit month
    result = get_audit_period(datetime(2026, 6, 15), [12])
    assert result == "2026-12", f"Single audit month: expected 2026-12, got {result}"
    print("✓ 2.6: Single audit month - PASS")

    print("\n✅ All audit period tests passed!")

if __name__ == '__main__':
    test_audit_period()
