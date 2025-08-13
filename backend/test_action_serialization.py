#!/usr/bin/env python3
"""
Test Action Serialization Logic
Tests the new action serial generation and validation without database dependencies.
"""

def validate_job_serial(serial: str) -> bool:
    """Validate job serial format: J20250000001 (7-digit format only)"""
    if not serial or len(serial) != 12:
        return False
    
    try:
        return (
            serial[0] == "J" and
            serial[1:5].isdigit() and  # Year (4 digits)
            serial[5:12].isdigit() and # Number (7 digits)
            len(serial[5:12]) == 7     # 7-digit number
        )
    except:
        return False

def validate_action_serial(serial: str) -> bool:
    """Validate action serial format: J20250000001.0001.0001.0001 (7-digit job format)"""
    if not serial or len(serial) != 27:  # 12 + 1 + 4 + 1 + 4 + 1 + 4 = 27
        return False
    
    try:
        parts = serial.split('.')
        if len(parts) != 4:
            return False
        
        job_part, exec_part, branch_part, action_part = parts
        return (
            validate_job_serial(job_part) and
            len(exec_part) == 4 and exec_part.isdigit() and
            len(branch_part) == 4 and branch_part.isdigit() and
            len(action_part) == 4 and action_part.isdigit()
        )
    except:
        return False

def parse_action_serial(serial: str) -> dict:
    """Parse action serial into components"""
    if not validate_action_serial(serial):
        return None
    
    parts = serial.split('.')
    return {
        'job_serial': parts[0],
        'execution_number': int(parts[1]),
        'branch_number': int(parts[2]),
        'action_number': int(parts[3])
    }

def test_action_serialization():
    """Test action serialization functionality"""
    print("🧪 Testing Action Serialization Logic...")
    
    # Test cases
    test_cases = [
        {
            'serial': 'J20250000001.0001.0001.0001',
            'valid': True,
            'description': 'Valid action serial'
        },
        {
            'serial': 'J20250000001.0001.0001.9999',
            'valid': True,
            'description': 'Valid action serial with high action number'
        },
        {
            'serial': 'J20250000001.0001.0001',
            'valid': False,
            'description': 'Branch serial (missing action part)'
        },
        {
            'serial': 'J20250000001.0001.0001.00001',
            'valid': False,
            'description': 'Invalid action serial (5 digits instead of 4)'
        },
        {
            'serial': 'J2025000001.0001.0001.0001',
            'valid': False,
            'description': 'Invalid job serial (wrong length)'
        },
        {
            'serial': 'T20250000001.0001.0001.0001',
            'valid': False,
            'description': 'Target serial prefix (should be J)'
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        serial = test_case['serial']
        expected_valid = test_case['valid']
        description = test_case['description']
        
        is_valid = validate_action_serial(serial)
        passed = is_valid == expected_valid
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   Test {i}: {status} - {description}")
        print(f"      Serial: {serial}")
        print(f"      Expected: {'Valid' if expected_valid else 'Invalid'}")
        print(f"      Got: {'Valid' if is_valid else 'Invalid'}")
        
        if passed and is_valid:
            # Test parsing for valid serials
            parsed = parse_action_serial(serial)
            if parsed:
                print(f"      Parsed: Job={parsed['job_serial']}, Exec={parsed['execution_number']}, Branch={parsed['branch_number']}, Action={parsed['action_number']}")
            else:
                print(f"      ❌ Parsing failed for valid serial")
                all_passed = False
        
        print()
        
        if not passed:
            all_passed = False
    
    # Test hierarchy examples
    print("📋 Hierarchy Examples:")
    examples = [
        'J20250000001',                    # Job
        'J20250000001.0001',              # Execution  
        'J20250000001.0001.0001',         # Branch
        'J20250000001.0001.0001.0001',    # Action 1
        'J20250000001.0001.0001.0002',    # Action 2
        'J20250000001.0001.0001.0003',    # Action 3
    ]
    
    for example in examples:
        parts = example.split('.')
        level = ['Job', 'Execution', 'Branch', 'Action'][len(parts) - 1]
        print(f"   {level:9}: {example}")
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    test_action_serialization()