import ast
import symtable

class ContextAnalyzer:
    """Analyzes source code structure and symbol tables for error context."""
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        try:
            self.tree = ast.parse(source_code)
        except SyntaxError:
            self.tree = None # Fallback if code is too broken to parse

    def get_line_context(self, line_no: int):
        """Finds the AST node corresponding to the error line."""
        if not self.tree:
            return "Could not parse AST due to severe syntax error."
            
        for node in ast.walk(self.tree):
            if hasattr(node, 'lineno') and node.lineno == line_no:
                return {
                    "node_type": type(node).__name__,
                    "fields": node._fields,
                    "code_segment": self.source_code.splitlines()[line_no-1].strip()
                }
        return "Line node not found in AST."

    def get_symbol_context(self):
        """Extracts variable types/names from the symbol table."""
        try:
            table = symtable.symtable(self.source_code, "test.py", "exec")
            return {
                "variables": table.get_identifiers(),
                "is_optimized": table.is_optimized(),
                "scope": table.get_name()
            }
        except:
            return "Symbol table unavailable."

if __name__ == "__main__":
    code = "x = 10\ny = 'string'\nresult = x + y"
    analyzer = ContextAnalyzer(code)
    print(f"AST Context for Error at Line 3: {analyzer.get_line_context(3)}")
    print(f"Symbol Table: {analyzer.get_symbol_context()}")