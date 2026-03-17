#!/usr/bin/env python3
"""Test report completeness validation"""

import sys
sys.path.insert(0, '.')
from honeybadger_server import check_completeness

def test_completeness():
    """Test report completeness validation"""

    mandatory = ['neofetch', 'lynis']
    one_of = ['trivy', 'vulnix']

    # Test 4.5: Complete with trivy
    is_complete, missing = check_completeness(['neofetch', 'lynis', 'trivy'], mandatory, one_of)
    assert is_complete == True, f"Complete with trivy: expected True, got {is_complete}"
    assert missing == [], f"Complete with trivy: expected no missing, got {missing}"
    print("✓ 4.5: Complete set with trivy - PASS")

    # Test 4.6: Complete with vulnix
    is_complete, missing = check_completeness(['neofetch', 'lynis', 'vulnix'], mandatory, one_of)
    assert is_complete == True, f"Complete with vulnix: expected True, got {is_complete}"
    assert missing == [], f"Complete with vulnix: expected no missing, got {missing}"
    print("✓ 4.6: Complete set with vulnix - PASS")

    # Test 4.7: Complete with both trivy and vulnix
    is_complete, missing = check_completeness(['neofetch', 'lynis', 'trivy', 'vulnix'], mandatory, one_of)
    assert is_complete == True, f"Complete with both: expected True, got {is_complete}"
    assert missing == [], f"Complete with both: expected no missing, got {missing}"
    print("✓ 4.7: Complete set with both scanners - PASS")

    # Test 4.8: Incomplete - missing lynis
    is_complete, missing = check_completeness(['neofetch', 'trivy'], mandatory, one_of)
    assert is_complete == False, f"Missing lynis: expected False, got {is_complete}"
    assert 'lynis' in missing, f"Missing lynis: expected 'lynis' in missing, got {missing}"
    print("✓ 4.8: Incomplete - missing lynis - PASS")

    # Test 4.8: Incomplete - missing scanner
    is_complete, missing = check_completeness(['neofetch', 'lynis'], mandatory, one_of)
    assert is_complete == False, f"Missing scanner: expected False, got {is_complete}"
    assert any('trivy' in str(m) or 'vulnix' in str(m) for m in missing), f"Missing scanner: expected trivy/vulnix in missing, got {missing}"
    print("✓ 4.8: Incomplete - missing scanner - PASS")

    # Test 4.8: Incomplete - missing neofetch
    is_complete, missing = check_completeness(['lynis', 'trivy'], mandatory, one_of)
    assert is_complete == False, f"Missing neofetch: expected False, got {is_complete}"
    assert 'neofetch' in missing, f"Missing neofetch: expected 'neofetch' in missing, got {missing}"
    print("✓ 4.8: Incomplete - missing neofetch - PASS")

    # Test 4.8: Incomplete - multiple missing
    is_complete, missing = check_completeness(['neofetch'], mandatory, one_of)
    assert is_complete == False, f"Multiple missing: expected False, got {is_complete}"
    assert len(missing) == 2, f"Multiple missing: expected 2 items, got {len(missing)}"
    print("✓ 4.8: Incomplete - multiple missing - PASS")

    # Test 4.2-4.4: Verify missing reports list
    is_complete, missing = check_completeness(['neofetch'], mandatory, one_of)
    assert 'lynis' in missing, "Should identify lynis as missing"
    assert 'trivy or vulnix' in missing or any('trivy' in str(m) for m in missing), "Should identify scanner as missing"
    print("✓ 4.2-4.4: Missing reports correctly identified - PASS")

    print("\n✅ All completeness validation tests passed!")

if __name__ == '__main__':
    test_completeness()
