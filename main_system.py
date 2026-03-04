
import os
import re
import json
import subprocess
import argparse
from typing import List, Optional
from dataclasses import dataclass
try:
    import torch
except ImportError:
    torch = None
print(">>> main_system.py is running")


from error_collector import ErrorCollector, CompilerError

# Optional modules (graceful fallback)
try:
    from ast_extractor import ASTExtractor, CodeContext
except ImportError:
    ASTExtractor = None
    CodeContext = None

try:
    from nlp_baseline import RuleBasedNLPEngine, Explanation
except ImportError:
    RuleBasedNLPEngine = None


    @dataclass
    class Explanation:
        title: str
        description: str
        root_cause: str
        fix_suggestion: str
        example: str = ""
        analogy: str = ""
        security_note: str = ""

        def format_output(self) -> str:
            return (
                f"\n🧠 {self.title}\n"
                f"📖 Description: {self.description}\n"
                f"🔍 Root Cause: {self.root_cause}\n"
                f"🛠 Fix: {self.fix_suggestion}\n"
            )

try:
    from security_filter import SecurityFilter, SecurityAnalysisResult
except ImportError:
    SecurityFilter = None
    SecurityAnalysisResult = None


@dataclass
class SystemConfig:
    use_simulation: bool = False  # Added flag
    use_transformer: bool = False
    transformer_model_path: Optional[str] = None
    security_check_enabled: bool = True
    output_format: str = "text"
    verbose: bool = False


@dataclass
class ExplanationOutput:
    error: CompilerError
    explanation: Explanation
    security_analysis: Optional[object] = None

    def to_dict(self):
        return {
            "error": self.error.to_dict(),
            "explanation": {
                "title": self.explanation.title,
                "description": self.explanation.description,
                "root_cause": self.explanation.root_cause,
                "fix": self.explanation.fix_suggestion,
            }
        }


class CompilerErrorExplainerSystem:

    def __init__(self, config: SystemConfig):
        self.config = config
        self.error_collector = ErrorCollector()

        self.ast_extractor = ASTExtractor() if ASTExtractor else None
        self.nlp_engine = RuleBasedNLPEngine() if RuleBasedNLPEngine else None
        self.security_filter = SecurityFilter() if SecurityFilter else None

        if config.verbose:
            print(" System initialized")

    def compile_code(self, source_file: str) -> str:
        """Compile source file using GCC and capture raw output"""
        print(f"\n[Backend] Executing GCC on {source_file}...")
        try:
           
            result = subprocess.run(
                ["gcc", source_file, "-Wall", "-o", "output_exec"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Combine stdout and stderr (GCC usually writes errors to stderr)
            raw_output = result.stderr + result.stdout
            
            print("[Backend] Raw Compiler Output Captured:")
            print("-" * 40)
            print(raw_output)
            print("-" * 40)
            
            return raw_output
            
        except FileNotFoundError:
            return "Error: 'gcc' compiler not found. Please ensure GCC is installed and in your PATH."
        except subprocess.TimeoutExpired:
            return "Error: Compilation timed out."
        except Exception as e:
            print(f"[Backend] Execution Error: {e}")
            return f"Error executing compiler: {str(e)}"

    def process_file(self, source_file: str, simulate_output: Optional[str] = None) -> List[ExplanationOutput]:
        compiler_output = ""
        
        # Check if we should use simulation (either string provided, or config flag)
        if simulate_output:
            print("(!) SIMULATION MODE: Using provided static output")
            compiler_output = simulate_output
        elif self.config.use_simulation:  # New config flag check
             print("(!) SIMULATION MODE: Generating dynamic errors")
             with open(source_file, 'r') as f:
                 code = f.read()
             compiler_output = self._simulate_gcc_output(source_file, code)
        else:
            compiler_output = self.compile_code(source_file)
            
        print("\n=== RAW COMPILER OUTPUT ===\n", compiler_output, "\n===========================\n")

        errors = self.error_collector.parse_gcc_output(compiler_output)

        print("\n===== DEBUG: PARSED ERRORS FROM ERROR_COLLECTOR =====")
        print(errors)

        # 🔥 FALLBACK PARSER IF MAIN PARSER FAILS
        if not errors:
            print("⚠️ Primary parser failed. Using fallback regex parser.")

            fallback_pattern = r"(.+?):(\d+):(?:\d+:)?\s*(error|warning):\s*(.*)"
            matches = re.findall(fallback_pattern, compiler_output)

            print("Fallback matches:", matches)

            for match in matches:
                file_name, line, severity_str, message = match
                
                # Check mapping for severity
                severity = self.error_collector._parse_severity(severity_str) if self.error_collector else CompilerError.Severity.ERROR # Assuming accessing helper or default

                # We need to construct ErrorLocation first
                from error_collector import ErrorLocation, ErrorType, Severity # Safe to import here if needed, or rely on top level
                
                loc = ErrorLocation(file=file_name, line=int(line), column=1)
                
                fake_error = CompilerError(
                    error_id=f"{file_name}:{line}",
                    error_type=ErrorType.UNKNOWN, # Default
                    severity=severity,
                    location=loc,
                    message=message.strip(),
                    raw_message=f"{file_name}:{line}: {severity_str}: {message}",
                    code_snippet=None,
                    context_lines=None
                )
                errors.append(fake_error)

        if not errors:
            print("❌ STILL NO ERRORS DETECTED AFTER FALLBACK")
            return []

        results = []
        for error in errors:
            explanation = self.generate_explanation(error)
            results.append(
                ExplanationOutput(
                    error=error,
                    explanation=explanation
                )
            )
        return results

    def _simulate_gcc_output(self, filename: str, code: str) -> str:
        """Simulate GCC output with symbol tracking and printf format checking"""
        output = []
        lines = code.split('\n')
        symbols = {}  # {name: type}
        
        for i, line in enumerate(lines, 1):
            line_str = line.strip()
            
            # Skip empty lines/comments
            if not line_str or line_str.startswith('//') or line_str.startswith('/*'):
                continue
                
            # Track Declarations (naive)
            # int x = 5; or int x;
            decl_match = re.search(r'\b(int|float|double|char|bool|string)\s+(\w+)', line_str)
            if decl_match:
                var_type = decl_match.group(1)
                var_name = decl_match.group(2)
                symbols[var_name] = var_type

            # 1. Missing Semicolon Check
            # Stronger heuristic: if line starts with a type or identifier or keyword, 
            # and doesn't end with ; or { or } or > or , (for multi-line)
            # Also ignore #include, #define
            if (not line_str.startswith('#') and 
                not line_str.startswith('//') and
                not line_str.endswith(';') and 
                not line_str.endswith('{') and 
                not line_str.endswith('}') and 
                not line_str.endswith('>')):
                
                # Check if it looks like a statement
                if (re.match(r'^(int|float|double|char|return|printf|scanf|cout|cin)\b', line_str) or 
                    re.match(r'^\w+\s*=', line_str)): # assignment x = 5
                     # Added column :1: to match ErrorCollector regex
                     output.append(f"{filename}:{i}:{len(line)}: error: expected ';' before end of line")
                     output.append(f"    {i} | {line}")
                     output.append(f"      | {' ' * len(line)}^")
                     output.append("      | ;")

            # 2. printf Format Mismatch Check
            # printf("... %d ...", z);
            if 'printf' in line_str:
                # Extract format string and arguments
                # Very basic parsing: find strings like "%d", "%f" and args
                # printf("val: %d", x);
                printf_match = re.search(r'printf\s*\(\s*"([^"]+)"\s*,\s*([^)]+)\s*\)', line_str)
                if printf_match:
                    fmt_string = printf_match.group(1)
                    args_str = printf_match.group(2)
                    args = [a.strip() for a in args_str.split(',')]
                    
                    # Find specifiers
                    specifiers = re.findall(r'%[dfs]', fmt_string)
                    
                    for idx, spec in enumerate(specifiers):
                        if idx < len(args):
                            arg_name = args[idx]
                            if arg_name in symbols:
                                arg_type = symbols[arg_name]
                                
                                # Mismatch logic
                                if spec == '%d' and arg_type in ['float', 'double']:
                                    col_idx = line.find('%d')
                                    if col_idx == -1: col_idx = 1
                                    output.append(f"{filename}:{i}:{col_idx}: warning: format '{spec}' expects argument of type 'int', but argument {idx+2} has type '{arg_type}' [-Wformat=]")
                                    output.append(f"    {i} | {line}")
                                    output.append(f"      | {' ' * len(line)}^")
                                elif spec == '%f' and arg_type == 'int':
                                     # This is often technically allowed but good to warn if aiming for precision
                                     pass 
            
            # 3. Type Mismatch / Conversion Warning
            # Check assignments: var = expression
            assign_match = re.search(r'\b(\w+)\s*=\s*(.+)', line_str.rstrip(';'))
            if assign_match:
                lhs_name = assign_match.group(1)
                rhs_expr = assign_match.group(2).strip()
                col_idx = line.find('=')
                if col_idx == -1: col_idx = 1
                
                # Check 3a: String literal assigned to int/float
                # e.g. int x = "hello";
                if rhs_expr.startswith('"') and rhs_expr.endswith('"'):
                    # It's a string literal
                    lhs_type = symbols.get(lhs_name)
                    # If we know the type and it's NOT a char* or string
                    if lhs_type and lhs_type not in ['char', 'string', 'char*']:
                         output.append(f"{filename}:{i}:{col_idx}: error: invalid conversion from 'char*' to '{lhs_type}' [-fpermissive]")
                         output.append(f"    {i} | {line}")
                         output.append(f"      | {' ' * col_idx}^")
                         
                # Check 3b: Type Compatibility Check (Enhanced)
                if lhs_name in symbols:
                    lhs_type = symbols[lhs_name]
                    rhs_vars = re.findall(r'\b[a-zA-Z_]\w*\b', rhs_expr)

                    for rv in rhs_vars:
                        if rv in symbols:
                            rhs_type = symbols[rv]

                            # int <- float/double
                            if lhs_type == 'int' and rhs_type in ['float', 'double']:
                                output.append(f"{filename}:{i}:{col_idx}: warning: possible loss of data converting '{rhs_type}' to 'int' [-Wconversion]")
                                output.append(f"    {i} | {line}")
                                output.append(f"      | {' ' * line.find('=')}^")

                            # float/double ← int
                            elif lhs_type in ['float', 'double'] and rhs_type == 'int':
                                output.append(f"{filename}:{i}:{col_idx}: warning: implicit conversion from 'int' to '{lhs_type}'")
                                output.append(f"    {i} | {line}")
                                output.append(f"      | {' ' * line.find('=')}^")

                            # char ← int
                            elif lhs_type == 'char' and rhs_type == 'int':
                                output.append(f"{filename}:{i}:{col_idx}: warning: conversion from 'int' to 'char' may change value")
                                output.append(f"    {i} | {line}")
                                output.append(f"      | {' ' * line.find('=')}^")

                            # incompatible types
                            elif lhs_type != rhs_type and lhs_type != 'string' and rhs_type != 'char*': # basic check, ignoring string literals handled above
                                output.append(f"{filename}:{i}:{col_idx}: error: incompatible types '{rhs_type}' to '{lhs_type}'")
                                output.append(f"    {i} | {line}")
                                output.append(f"      | {' ' * line.find('=')}^")


        # Fallback for empty code or no main
        if not output and len(code.strip()) > 0 and 'main' not in code:
             output.append(f"{filename}:1: error: undefined reference to 'main'")

        return "\n".join(output)

    def generate_explanation(self, error: CompilerError) -> Explanation:
        # Generate baseline explanation
        explanation = None
        if self.nlp_engine:
            explanation = self.nlp_engine.generate_explanation(
                error.message,
                {}
            )
        else:
             # Fallback explanation
            explanation = Explanation(
                title=f"{error.error_type.value.capitalize()} Error",
                description=error.message,
                root_cause="Compiler detected an issue in the code.",
                fix_suggestion="Review the error location and correct the syntax or declaration."
            )

        # Apply Security Filter to the fix suggestion
        if self.security_filter and self.config.security_check_enabled:
            security_result = self.security_filter.analyze_suggestion(explanation.fix_suggestion, {})
            
            if not security_result.is_safe:
                # Append security warning to the explanation
                security_note = "\n".join(security_result.security_warnings)
                if explanation.security_note:
                    explanation.security_note += "\n" + security_note
                else:
                    explanation.security_note = security_note
                
                # Optionally replace the fix with a filtered one (if available)
                if security_result.filtered_suggestion:
                     explanation.fix_suggestion = security_result.filtered_suggestion

        return explanation

    def format_output(self, results: List[ExplanationOutput]) -> str:
        output = []
        output.append("\n" + "=" * 60)
        output.append("COMPILER ERROR EXPLANATION REPORT")
        output.append("=" * 60)

        for i, r in enumerate(results, 1):
            e = r.error
            output.append(f"\nError {i}")
            output.append("-" * 60)
            output.append(
                f"📍 {e.location.file}:{e.location.line}:{e.location.column}"
            )
            output.append(f"⚠️ {e.severity.value.upper()}")
            output.append(f"💬 {e.message}")
            output.append(r.explanation.format_output())

        return "\n".join(output)


# =================
if __name__ == "__main__":
    print(">>> Starting full pipeline...")

    config = SystemConfig(
        use_simulation=False,
        verbose=True
    )

    system = CompilerErrorExplainerSystem(config)

    test_file = "backend_test.c"

    if not os.path.exists(test_file):
        print(f"❌ File not found: {test_file}")
        exit()

    results = system.process_file(test_file)

    if results:
        print(system.format_output(results))
    else:
        print("No errors detected.")