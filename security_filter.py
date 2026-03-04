"""
Security-Aware Filtering Module
Detects and blocks unsafe quick fixes and provides secure alternatives
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class SecurityRisk(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class SecurityIssue:
    risk_level: SecurityRisk
    category: str
    description: str
    unsafe_pattern: str
    secure_alternative: str
    cwe_id: Optional[str] = None  # Common Weakness Enumeration
    
@dataclass
class SecurityAnalysisResult:
    is_safe: bool
    issues: List[SecurityIssue]
    filtered_suggestion: str
    security_warnings: List[str]

class SecurityFilter:
    def __init__(self):
        self.unsafe_patterns = self._initialize_unsafe_patterns()
        self.secure_alternatives = self._initialize_secure_alternatives()
    
    def _initialize_unsafe_patterns(self) -> List[Dict]:
        """Initialize patterns for detecting unsafe code suggestions"""
        return [
            {
                'name': 'disable_warnings',
                'pattern': r'#pragma\s+warning\s*\(\s*disable',
                'category': 'Warning Suppression',
                'risk': SecurityRisk.HIGH,
                'description': 'Disabling compiler warnings hides potential bugs and security issues',
                'cwe': 'CWE-1164'
            },
            {
                'name': 'c_style_cast',
                'pattern': r'\([a-zA-Z_][a-zA-Z0-9_]*\s*\*?\s*\)',
                'category': 'Unsafe Type Casting',
                'risk': SecurityRisk.MEDIUM,
                'description': 'C-style casts bypass type safety checks',
                'cwe': 'CWE-704'
            },
            {
                'name': 'gets_function',
                'pattern': r'\bgets\s*\(',
                'category': 'Buffer Overflow',
                'risk': SecurityRisk.CRITICAL,
                'description': 'gets() is unsafe and can cause buffer overflows',
                'cwe': 'CWE-120'
            },
            {
                'name': 'strcpy_function',
                'pattern': r'\bstrcpy\s*\(',
                'category': 'Buffer Overflow',
                'risk': SecurityRisk.HIGH,
                'description': 'strcpy() does not check buffer bounds',
                'cwe': 'CWE-120'
            },
            {
                'name': 'sprintf_function',
                'pattern': r'\bsprintf\s*\(',
                'category': 'Buffer Overflow',
                'risk': SecurityRisk.HIGH,
                'description': 'sprintf() can overflow buffer',
                'cwe': 'CWE-120'
            },
            {
                'name': 'strcat_function',
                'pattern': r'\bstrcat\s*\(',
                'category': 'Buffer Overflow',
                'risk': SecurityRisk.HIGH,
                'description': 'strcat() does not check buffer bounds',
                'cwe': 'CWE-120'
            },
            {
                'name': 'scanf_no_width',
                'pattern': r'scanf\s*\([^)]*%s[^0-9]',
                'category': 'Buffer Overflow',
                'risk': SecurityRisk.HIGH,
                'description': 'scanf() with %s and no width specifier can overflow',
                'cwe': 'CWE-120'
            },
            {
                'name': 'null_pointer_bypass',
                'pattern': r'if\s*\(\s*\w+\s*==\s*NULL\s*\)\s*\w+\s*=\s*',
                'category': 'Null Pointer Bypass',
                'risk': SecurityRisk.MEDIUM,
                'description': 'Assigning value when pointer is NULL without proper handling',
                'cwe': 'CWE-476'
            },
            {
                'name': 'malloc_no_check',
                'pattern': r'=\s*malloc\s*\([^)]+\)\s*;(?!\s*if)',
                'category': 'Memory Safety',
                'risk': SecurityRisk.HIGH,
                'description': 'malloc() result not checked for NULL',
                'cwe': 'CWE-252'
            },
            {
                'name': 'unsafe_reinterpret_cast',
                'pattern': r'reinterpret_cast\s*<',
                'category': 'Unsafe Type Casting',
                'risk': SecurityRisk.MEDIUM,
                'description': 'reinterpret_cast bypasses type system safety',
                'cwe': 'CWE-704'
            },
            {
                'name': 'system_call',
                'pattern': r'\bsystem\s*\(',
                'category': 'Command Injection',
                'risk': SecurityRisk.CRITICAL,
                'description': 'system() calls can lead to command injection',
                'cwe': 'CWE-78'
            },
            {
                'name': 'atoi_no_validation',
                'pattern': r'atoi\s*\(',
                'category': 'Input Validation',
                'risk': SecurityRisk.MEDIUM,
                'description': 'atoi() has no error handling for invalid input',
                'cwe': 'CWE-20'
            },
            {
                'name': 'rand_for_security',
                'pattern': r'\brand\s*\(',
                'category': 'Weak Randomness',
                'risk': SecurityRisk.HIGH,
                'description': 'rand() is not cryptographically secure',
                'cwe': 'CWE-338'
            },
            {
                'name': 'hardcoded_credentials',
                'pattern': r'password\s*=\s*["\']',
                'category': 'Hardcoded Credentials',
                'risk': SecurityRisk.CRITICAL,
                'description': 'Hardcoded passwords in source code',
                'cwe': 'CWE-798'
            },
            {
                'name': 'buffer_size_calculation',
                'pattern': r'sizeof\s*\(\s*\w+\s*\)\s*-\s*1',
                'category': 'Off-by-One Error',
                'risk': SecurityRisk.MEDIUM,
                'description': 'Potential off-by-one error in buffer size',
                'cwe': 'CWE-193'
            }
        ]
    
    def _initialize_secure_alternatives(self) -> Dict[str, str]:
        """Initialize secure alternatives for unsafe patterns"""
        return {
            'gets_function': (
                "Use fgets() instead:\n"
                "    char buffer[100];\n"
                "    fgets(buffer, sizeof(buffer), stdin);\n"
                "    // Remove trailing newline if needed\n"
                "    buffer[strcspn(buffer, \"\\n\")] = '\\0';"
            ),
            'strcpy_function': (
                "Use strncpy() or strlcpy():\n"
                "    char dest[100];\n"
                "    strncpy(dest, source, sizeof(dest) - 1);\n"
                "    dest[sizeof(dest) - 1] = '\\0';  // Ensure null termination"
            ),
            'sprintf_function': (
                "Use snprintf():\n"
                "    char buffer[100];\n"
                "    snprintf(buffer, sizeof(buffer), \"format %d\", value);\n"
                "    // Automatically ensures null termination"
            ),
            'strcat_function': (
                "Use strncat() or calculate remaining space:\n"
                "    size_t remaining = sizeof(dest) - strlen(dest) - 1;\n"
                "    strncat(dest, source, remaining);"
            ),
            'scanf_no_width': (
                "Use width specifier with scanf():\n"
                "    char buffer[100];\n"
                "    scanf(\"%99s\", buffer);  // Read max 99 chars + null terminator"
            ),
            'malloc_no_check': (
                "Always check malloc() result:\n"
                "    int* ptr = malloc(sizeof(int) * n);\n"
                "    if (ptr == NULL) {\n"
                "        fprintf(stderr, \"Memory allocation failed\\n\");\n"
                "        return -1;\n"
                "    }"
            ),
            'c_style_cast': (
                "Use C++ static_cast for safe casting:\n"
                "    // Instead of: int x = (int)value;\n"
                "    int x = static_cast<int>(value);"
            ),
            'disable_warnings': (
                "Fix the underlying issue instead of disabling warnings.\n"
                "Warnings indicate potential problems that should be addressed."
            ),
            'system_call': (
                "Avoid system() calls. Use safer alternatives:\n"
                "    // Instead of: system(\"ls\");\n"
                "    // Use: fork() + execve() or platform-specific APIs\n"
                "    // Or validate and sanitize input carefully"
            ),
            'atoi_no_validation': (
                "Use strtol() with error checking:\n"
                "    char* endptr;\n"
                "    errno = 0;\n"
                "    long val = strtol(str, &endptr, 10);\n"
                "    if (errno != 0 || *endptr != '\\0') {\n"
                "        // Handle error\n"
                "    }"
            ),
            'rand_for_security': (
                "For security-critical randomness, use:\n"
                "    // C++: <random> with std::random_device\n"
                "    // POSIX: /dev/urandom\n"
                "    // Windows: CryptGenRandom\n"
                "    // OpenSSL: RAND_bytes()"
            ),
            'hardcoded_credentials': (
                "Never hardcode credentials:\n"
                "    // Use environment variables\n"
                "    const char* password = getenv(\"DB_PASSWORD\");\n"
                "    // Or configuration files with proper permissions\n"
                "    // Or secure credential management systems"
            )
        }
    
    def analyze_suggestion(self, code_suggestion: str, error_context: Dict) -> SecurityAnalysisResult:
        """Analyze a code suggestion for security issues"""
        issues = []
        warnings = []
        
        for pattern_info in self.unsafe_patterns:
            pattern = re.compile(pattern_info['pattern'], re.IGNORECASE)
            matches = pattern.findall(code_suggestion)
            
            if matches:
                issue = SecurityIssue(
                    risk_level=pattern_info['risk'],
                    category=pattern_info['category'],
                    description=pattern_info['description'],
                    unsafe_pattern=pattern_info['pattern'],
                    secure_alternative=self.secure_alternatives.get(
                        pattern_info['name'], 
                        "Consult secure coding guidelines"
                    ),
                    cwe_id=pattern_info.get('cwe')
                )
                issues.append(issue)
                
                warning = (
                    f"⚠️  {pattern_info['risk'].value.upper()} RISK - "
                    f"{pattern_info['category']}: {pattern_info['description']}"
                )
                warnings.append(warning)
        
        # Determine if suggestion is safe
        is_safe = not any(issue.risk_level in [SecurityRisk.CRITICAL, SecurityRisk.HIGH] 
                         for issue in issues)
        
        # Filter suggestion if unsafe
        filtered_suggestion = code_suggestion if is_safe else self._create_safe_alternative(
            code_suggestion, issues
        )
        
        return SecurityAnalysisResult(
            is_safe=is_safe,
            issues=issues,
            filtered_suggestion=filtered_suggestion,
            security_warnings=warnings
        )
    
    def _create_safe_alternative(self, unsafe_code: str, issues: List[SecurityIssue]) -> str:
        """Create a safe alternative by replacing unsafe patterns"""
        safe_code = unsafe_code
        
        # Apply replacements based on detected issues
        replacements = {
            r'\bgets\s*\(': 'fgets(',
            r'\bstrcpy\s*\(': 'strncpy(',
            r'\bsprintf\s*\(': 'snprintf(',
            r'\bstrcat\s*\(': 'strncat(',
            r'\bsystem\s*\(': '// UNSAFE: system(',
            r'#pragma\s+warning\s*\(\s*disable': '// WARNING DISABLED: #pragma warning(disable'
        }
        
        for pattern, replacement in replacements.items():
            safe_code = re.sub(pattern, replacement, safe_code)
        
        return safe_code
    
    def generate_security_report(self, result: SecurityAnalysisResult) -> str:
        """Generate formatted security analysis report"""
        if result.is_safe and not result.issues:
            return "✅ No security issues detected in this suggestion.\n"
        
        report = []
        report.append("🔒 SECURITY ANALYSIS REPORT")
        report.append("=" * 60)
        
        if not result.is_safe:
            report.append("\n❌ THIS SUGGESTION HAS BEEN BLOCKED DUE TO SECURITY RISKS\n")
        
        for issue in result.issues:
            report.append(f"\n📋 Issue: {issue.category}")
            report.append(f"   Risk Level: {issue.risk_level.value.upper()}")
            if issue.cwe_id:
                report.append(f"   CWE: {issue.cwe_id}")
            report.append(f"   Description: {issue.description}")
            report.append(f"\n   ✅ Secure Alternative:")
            report.append(f"   {issue.secure_alternative}")
            report.append("-" * 60)
        
        return "\n".join(report)
    
    def validate_fix_suggestion(self, fix: str) -> Tuple[bool, List[str]]:
        """Quick validation of a fix suggestion"""
        result = self.analyze_suggestion(fix, {})
        return result.is_safe, result.security_warnings

# Example usage
if __name__ == "__main__":
    filter_engine = SecurityFilter()
    
    # Test cases
    test_cases = [
        # Unsafe: gets()
        """char buffer[100];
gets(buffer);  // Read user input""",
        
        # Unsafe: strcpy without bounds check
        """strcpy(dest, source);""",
        
        # Unsafe: malloc without null check
        """int* arr = malloc(sizeof(int) * 100);
arr[0] = 5;""",
        
        # Safe: fgets with proper size
        """char buffer[100];
fgets(buffer, sizeof(buffer), stdin);""",
        
        # Unsafe: system call
        """system("rm -rf /tmp/*");""",
        
        # Unsafe: C-style cast
        """int* ptr = (int*)malloc(100);""",
    ]
    
    for i, code in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test Case {i}:")
        print(f"{'='*70}")
        print("Code:")
        print(code)
        print()
        
        result = filter_engine.analyze_suggestion(code, {})
        print(f"Is Safe: {result.is_safe}")
        print(f"Issues Found: {len(result.issues)}")
        
        if result.issues:
            print("\nSecurity Report:")
            print(filter_engine.generate_security_report(result))