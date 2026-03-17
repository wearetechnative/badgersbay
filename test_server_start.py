#!/usr/bin/env python3
"""Test that server can start without errors"""

import sys
sys.path.insert(0, '.')

def test_imports():
    """Test that all imports work"""
    try:
        from honeybadger_server import (
            Config,
            ComplianceCache,
            check_completeness,
            get_audit_period,
            ReportHandler
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_config_loading():
    """Test config loading with compliance disabled (backward compatibility)"""
    try:
        from honeybadger_server import Config
        config = Config('config.yaml')

        # Check basic config
        assert config.networkport == 7123
        assert config.storage_location == './reports'

        # Check compliance defaults (should be disabled)
        assert config.compliance_enabled == False

        print("✓ Config loading (legacy mode) successful")
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_init():
    """Test ComplianceCache initialization"""
    try:
        from honeybadger_server import Config, ComplianceCache
        config = Config('config.yaml')
        cache = ComplianceCache(config)

        # Should work even with compliance disabled
        cache.rebuild()

        print("✓ ComplianceCache initialization successful")
        return True
    except Exception as e:
        print(f"✗ Cache initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compliance_config():
    """Test compliance configuration parsing"""
    try:
        import yaml
        from honeybadger_server import Config

        # Create temp config with compliance enabled
        test_config = {
            'networkport': 7123,
            'storage_location': './reports',
            'compliance': {
                'enabled': True,
                'audit_months': [3, 9],
                'required_reports': {
                    'mandatory': ['neofetch', 'lynis'],
                    'one_of': ['trivy', 'vulnix']
                }
            }
        }

        # Write temp config
        with open('test_config.yaml', 'w') as f:
            yaml.dump(test_config, f)

        # Load it
        config = Config('test_config.yaml')

        assert config.compliance_enabled == True
        assert config.audit_months == [3, 9]
        assert config.required_reports_mandatory == ['neofetch', 'lynis']
        assert config.required_reports_one_of == ['trivy', 'vulnix']

        # Cleanup
        import os
        os.remove('test_config.yaml')

        print("✓ Compliance config parsing successful")
        return True
    except Exception as e:
        print(f"✗ Compliance config test failed: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup
        try:
            import os
            os.remove('test_config.yaml')
        except:
            pass
        return False

if __name__ == '__main__':
    print("Running server startup tests...\n")

    tests = [
        test_imports,
        test_config_loading,
        test_cache_init,
        test_compliance_config
    ]

    results = [test() for test in tests]

    print(f"\n{'='*50}")
    if all(results):
        print("✅ All startup tests passed!")
        print("Server is ready to run.")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
