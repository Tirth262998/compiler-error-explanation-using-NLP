
import re
import json
import subprocess
import os
import ast
import symtable
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum



class ErrorType(Enum):
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    TYPE = "type"
    LINKER = "linker"
    WARNING = "warning"
    UNKNOWN = "unknown"

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"
    FATAL = "fatal"

@dataclass
class ErrorLocation:
    file: str
    line: int
    column: int

@dataclass
class CompilerError:
    error_id: str
    error_type: ErrorType
    severity: Severity
    location: ErrorLocation
    message: str
    raw_message: str
    code_snippet: Optional[str] = None
    ast_context: Optional[Dict] = None      # New: AST node info
    symbol_table: Optional[Dict] = None    # New: Scope/Variable info
    secure_fix_note: Optional[str] = None  # New: Security requirement
    
    def to_dict(self):
        d = asdict(self)
        d['error_type'] = self.error_type.value
        d['severity'] = self.severity.value
        return d

# --- Main Collector Class (Week 6 Requirements) ---

class ErrorCollector:
    """Parses compiler diagnostics and enriches them with AST and real-time logs."""
    
    def __init__(self):
        # Regex for GCC/Clang format: file:line:col: type: message
        self.gcc_pattern = re.compile(r"([^:\n]+):(\d+):(?:(\d+):)?\s(error|warning|note):\s+(.+)")

    def collect_real_errors(self, file_path: str, language: str = "python") -> List[CompilerError]:
        """
        Requirement: 'Collect real compiler errors using faulty programs'.
        Invokes a real compiler/interpreter to capture live diagnostic logs.
        """
        if not os.path.exists(file_path):
            return []

        if language.lower() == "python":
            # Use python's compile module to find syntax errors without executing
            cmd = ["python3", "-m", "py_compile", file_path]
        elif language.lower() == "c":
            cmd = ["gcc", "-fsyntax-only", file_path]
        else:
            raise ValueError("Unsupported language for real-time collection.")

        # Run process and capture stderr
        result = subprocess.run(cmd, capture_output=True, text=True)
        raw_output = result.stderr if result.stderr else result.stdout
        
        parsed_errors = self.parse_gcc_output(raw_output)
        
        # Enrich with AST and Symbol Table if it's Python
        if language.lower() == "python":
            with open(file_path, 'r') as f:
                source = f.read()
                for err in parsed_errors:
                    err.ast_context = self.get_ast_context(source, err.location.line)
                    err.symbol_table = self.get_symbol_table(source)
        
        return parsed_errors

    def get_ast_context(self, source_code: str, line_no: int) -> Dict:
        """
        Requirement: 'Extract AST and symbol-table context'.
        Analyzes the structure of the code at the error location.
        """
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if hasattr(node, 'lineno') and node.lineno == line_no:
                    return {
                        "node_type": type(node).__name__,
                        "parent_context": "Expression" if isinstance(node, ast.expr) else "Statement",
                        "details": str(node.__dict__.get('id', 'N/A'))
                    }
        except Exception as e:
            return {"error": f"AST Parsing failed: {str(e)}"}
        return {"info": "No specific AST node matched the exact line."}

    def get_symbol_table(self, source_code: str) -> Dict:
        """Requirement: 'Extract symbol-table context'."""
        try:
            table = symtable.symtable(source_code, "input_file", "exec")
            return {
                "scope_name": table.get_name(),
                "identifiers": table.get_identifiers(),
                "is_nested": table.is_nested()
            }
        except:
            return {"info": "Symbol table unavailable (likely due to syntax error)."}

    def parse_gcc_output(self, content: str) -> List[CompilerError]:
        """Existing logic updated to initialize new fields."""
        errors = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            match = self.gcc_pattern.search(line)
            if match:
                file, l_no, c_no, sev_str, msg = match.groups()
                
                # Basic inference of error type
                err_type = ErrorType.SYNTAX
                if "type" in msg.lower() or "conversion" in msg.lower():
                    err_type = ErrorType.TYPE
                
                location = ErrorLocation(file, int(l_no), int(c_no) if c_no else 0)
                
                error_obj = CompilerError(
                    error_id=f"ERR_{l_no}_{i}",
                    error_type=err_type,
                    severity=Severity[sev_str.upper()],
                    location=location,
                    message=msg.strip(),
                    raw_message=line.strip(),
                    secure_fix_note="Ensure input is validated before use." # Default secure note
                )
                errors.append(error_obj)
        
        return errors

    def export_to_json(self, errors: List[CompilerError], output_path: str):
        """Export parsed and enriched errors to JSON"""
        data = [error.to_dict() for error in errors]
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

# --- Test Script ---
if __name__ == "__main__":
    # Create a dummy faulty python file for testing Week 6
    test_file = "test_backend.py"
    with open(test_file, "w") as f:
        f.write("x = 10\ny = 'string'\nprint(x + y") # Syntax error: missing paren
    
    collector = ErrorCollector()
    
    print("--- Running Real-Time Collection (Week 6) ---")
    results = collector.collect_real_errors(test_file, language="python")
    
    # Export to JSON
    output_json = "error.json"
    collector.export_to_json(results, output_json)
    print(f"[*] Errors exported to {output_json}")

    for e in results:
        print(f"[{e.severity.value.upper()}] Line {e.location.line}: {e.message}")
        # print(f"AST Context: {e.ast_context}")
        # print(f"Symbol Table: {e.symbol_table}")
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)