"""
AST Extractor Module
Extracts Abstract Syntax Tree and semantic context using tree-sitter
"""

import re
import re
try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("Warning: tree-sitter not found. Using fallback parsing.")
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Note: In production, compile tree-sitter languages first:
# from tree_sitter import Language
# Language.build_library('build/languages.so', ['tree-sitter-c', 'tree-sitter-cpp'])

@dataclass
class ASTNode:
    node_type: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    text: str
    children: List['ASTNode']
    
    def to_dict(self):
        return {
            'node_type': self.node_type,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'start_col': self.start_col,
            'end_col': self.end_col,
            'text': self.text[:100],  # Truncate long text
            'children': [child.to_dict() for child in self.children]
        }

@dataclass
class Symbol:
    name: str
    symbol_type: str  # variable, function, parameter, struct, etc.
    data_type: Optional[str]
    scope: str
    line_defined: int
    
@dataclass
class CodeContext:
    ast_root: ASTNode
    symbols: List[Symbol]
    functions: List[Dict]
    variables: List[Dict]
    error_node: Optional[ASTNode]
    scope_chain: List[str]

class ASTExtractor:
    def __init__(self, language='c'):
        """
        Initialize AST extractor
        For production: precompile tree-sitter languages
        """
        self.language = language
        self.parser = None
        self._init_parser()
    
    def _init_parser(self):
        """Initialize tree-sitter parser"""

        if not TREE_SITTER_AVAILABLE:
            self.parser = None
            return

        try:
            from tree_sitter import Language, Parser
            import tree_sitter_c

            C_LANGUAGE = Language(tree_sitter_c.language())
            self.parser = Parser()
            self.parser.language = C_LANGUAGE

        except Exception as e:
            print("Tree-sitter init failed:", e)
            self.parser = None
    
    def parse_code(self, source_code: str):
        """Parse source code and return tree-sitter tree"""
        if self.parser:
            return self.parser.parse(bytes(source_code, 'utf8'))
        return None
    
    def extract_ast(self, source_code: str) -> ASTNode:
        """Extract complete AST structure"""
        tree = self.parse_code(source_code)
        
        if tree:
            return self._convert_tree_sitter_node(tree.root_node, source_code)
        else:
            # Fallback: create simplified AST
            return self._create_fallback_ast(source_code)
    
    def _convert_tree_sitter_node(self, node, source_code: str) -> ASTNode:
        """Convert tree-sitter node to our ASTNode format"""
        start_point = node.start_point
        end_point = node.end_point
        
        text = source_code[node.start_byte:node.end_byte]
        
        children = []
        for child in node.children:
            children.append(self._convert_tree_sitter_node(child, source_code))
        
        return ASTNode(
            node_type=node.type,
            start_line=start_point[0] + 1,
            end_line=end_point[0] + 1,
            start_col=start_point[1],
            end_col=end_point[1],
            text=text,
            children=children
        )
    
    def _create_fallback_ast(self, source_code: str) -> ASTNode:
        """Create simplified AST when tree-sitter unavailable"""
        lines = source_code.split('\n')
        return ASTNode(
            node_type='translation_unit',
            start_line=1,
            end_line=len(lines),
            start_col=0,
            end_col=len(lines[-1]) if lines else 0,
            text=source_code[:200],
            children=[]
        )
    
    def find_node_at_location(self, ast: ASTNode, line: int, col: int) -> Optional[ASTNode]:
        """Find the AST node at specific line and column"""
        if ast.start_line <= line <= ast.end_line:
            # Check if position is within this node
            if line == ast.start_line and col < ast.start_col:
                return None
            if line == ast.end_line and col > ast.end_col:
                return None
            
            # Try to find more specific child node
            for child in ast.children:
                result = self.find_node_at_location(child, line, col)
                if result:
                    return result
            
            return ast
        return None
    
    def extract_symbols(self, source_code: str) -> List[Symbol]:
        """Extract symbol table (variables, functions, types)"""
        symbols = []
        
        # Extract function declarations
        import re
        func_pattern = r'(\w+)\s+(\w+)\s*\([^)]*\)\s*{'
        for match in re.finditer(func_pattern, source_code):
            line_num = source_code[:match.start()].count('\n') + 1
            symbols.append(Symbol(
                name=match.group(2),
                symbol_type='function',
                data_type=match.group(1),
                scope='global',
                line_defined=line_num
            ))
        
        # Extract variable declarations
        var_pattern = r'(?:int|float|double|char|void|long|short|unsigned)\s+(\w+)\s*[;=]'
        for match in re.finditer(var_pattern, source_code):
            line_num = source_code[:match.start()].count('\n') + 1
            # Determine scope based on line number
            scope = self._determine_scope(source_code, line_num)
            symbols.append(Symbol(
                name=match.group(1),
                symbol_type='variable',
                data_type=match.group(0).split()[0],
                scope=scope,
                line_defined=line_num
            ))
        
        return symbols
    
    def _determine_scope(self, source_code: str, line_num: int) -> str:
        """Determine scope of a declaration"""
        lines = source_code.split('\n')
        brace_count = 0
        
        for i, line in enumerate(lines[:line_num], 1):
            brace_count += line.count('{') - line.count('}')
        
        if brace_count == 0:
            return 'global'
        else:
            # Find enclosing function
            for i in range(line_num - 1, -1, -1):
                if '{' in lines[i] and any(keyword in lines[i] for keyword in ['int', 'void', 'float']):
                    func_match = re.search(r'(\w+)\s*\(', lines[i])
                    if func_match:
                        return func_match.group(1)
            return 'local'
    
    def extract_context(self, source_code: str, error_line: int, error_col: int) -> CodeContext:
        """Extract complete context around an error"""
        ast = self.extract_ast(source_code)
        symbols = self.extract_symbols(source_code)
        error_node = self.find_node_at_location(ast, error_line, error_col)
        
        # Build scope chain
        scope_chain = self._build_scope_chain(source_code, error_line)
        
        # Extract functions and variables
        functions = [s for s in symbols if s.symbol_type == 'function']
        variables = [s for s in symbols if s.symbol_type == 'variable']
        
        return CodeContext(
            ast_root=ast,
            symbols=symbols,
            functions=[asdict(f) for f in functions],
            variables=[asdict(v) for v in variables],
            error_node=error_node,
            scope_chain=scope_chain
        )
    
    def _build_scope_chain(self, source_code: str, error_line: int) -> List[str]:
        """Build chain of scopes from global to error location"""
        lines = source_code.split('\n')
        scope_chain = ['global']
        
        # Find enclosing function
        for i in range(error_line - 1, -1, -1):
            if '{' in lines[i]:
                func_match = re.search(r'(\w+)\s*\([^)]*\)\s*{', lines[i])
                if func_match:
                    scope_chain.append(func_match.group(1))
                    break
        
        return scope_chain
    
    def visualize_ast(self, node: ASTNode, indent: int = 0) -> str:
        """Create text visualization of AST"""
        result = "  " * indent + f"{node.node_type} [{node.start_line}:{node.start_col}]\n"
        for child in node.children[:5]:  # Limit children for readability
            result += self.visualize_ast(child, indent + 1)
        if len(node.children) > 5:
            result += "  " * (indent + 1) + "... (more children)\n"
        return result

# Example usage
if __name__ == "__main__":
    sample_code = """
#include <stdio.h>

int global_var = 10;

int add(int a, int b) {
    int result = a + b;
    return result;
}

int main() {
    int x = 5;
    int y = 3;
    printf("Sum: %d\\n", add(x, y));
    return 0
}
"""
    
    extractor = ASTExtractor()
    
    # Extract AST
    ast = extractor.extract_ast(sample_code)
    print("AST Structure:")
    print(extractor.visualize_ast(ast))
    print("\n" + "="*80 + "\n")
    
    # Extract symbols
    symbols = extractor.extract_symbols(sample_code)
    print(f"Found {len(symbols)} symbols:")
    for sym in symbols:
        print(f"  {sym.name} ({sym.symbol_type}) - {sym.data_type} @ line {sym.line_defined}")
    print("\n" + "="*80 + "\n")
    
    # Extract context for error at line 15 (missing semicolon)
    context = extractor.extract_context(sample_code, 15, 15)
    print(f"Context at line 15:")
    print(f"  Scope chain: {' -> '.join(context.scope_chain)}")
    print(f"  Error node type: {context.error_node.node_type if context.error_node else 'Not found'}")