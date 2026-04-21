"""
Enhanced AST Extractor Module
Extracts Abstract Syntax Tree and semantic context using tree-sitter (with fallback).

New Capabilities:
  - Variable dependency tracking (who uses whom)
  - Data flow analysis (definition → usage tracking)
  - Control flow awareness (if/else, loops, unreachable code detection)
  - Contextual code window (±3 lines around error)
  - Semantic labeling for AST nodes (declaration, assignment, function_call, etc.)
"""

import re
try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("Warning: tree-sitter not found. Using fallback parsing.")

import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ASTNode:
    node_type: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    text: str
    children: List['ASTNode']
    semantic_label: str = "unknown"   # NEW: declaration/assignment/function_call/…

    def to_dict(self):
        return {
            'node_type': self.node_type,
            'semantic_label': self.semantic_label,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'start_col': self.start_col,
            'end_col': self.end_col,
            'text': self.text[:100],
            'children': [child.to_dict() for child in self.children],
        }


@dataclass
class Symbol:
    name: str
    symbol_type: str          # variable / function / parameter / struct
    data_type: Optional[str]
    scope: str
    line_defined: int


@dataclass
class VariableDependency:
    """Tracks which variables a given variable depends on."""
    variable: str
    depends_on: List[str] = field(default_factory=list)
    used_by: List[str] = field(default_factory=list)


@dataclass
class DataFlowEntry:
    """One definition or use event for a variable."""
    variable: str
    event: str          # 'definition' | 'usage'
    line: int
    context: str        # the raw line text


@dataclass
class ControlFlowBlock:
    """Represents a control-flow block found in the source."""
    block_type: str     # 'if' | 'else' | 'for' | 'while' | 'do_while' | 'switch'
    start_line: int
    end_line: int
    condition: str


@dataclass
class CodeWindow:
    """±N lines around an error location."""
    error_line: int
    window_start: int
    window_end: int
    lines: List[Tuple[int, str]]    # (line_number, line_text)
    highlighted_line: str


@dataclass
class CodeContext:
    ast_root: ASTNode
    symbols: List[Symbol]
    functions: List[Dict]
    variables: List[Dict]
    error_node: Optional[ASTNode]
    scope_chain: List[str]
    # ── NEW fields ────────────────────────────────────────────────
    dependencies: List[VariableDependency] = field(default_factory=list)
    data_flow: List[DataFlowEntry] = field(default_factory=list)
    control_flow: List[ControlFlowBlock] = field(default_factory=list)
    code_window: Optional[CodeWindow] = None
    unreachable_lines: List[int] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Semantic label helpers
# ---------------------------------------------------------------------------

_DECL_RE = re.compile(
    r'^\s*(int|float|double|char|void|long|short|unsigned|bool|auto)\s+\w+', re.IGNORECASE
)
_ASSIGN_RE = re.compile(r'^\s*\w+\s*(\+|-|\*|/|%|&|\||\^|<<|>>)?=\s*')
_CALL_RE = re.compile(r'\b\w+\s*\(')
_RETURN_RE = re.compile(r'^\s*return\b')
_IF_RE = re.compile(r'^\s*if\s*\(')
_LOOP_RE = re.compile(r'^\s*(for|while|do)\b')
_INCLUDE_RE = re.compile(r'^\s*#\s*include\b')


def _semantic_label_for_line(line: str) -> str:
    if _INCLUDE_RE.match(line):
        return "preprocessor"
    if _DECL_RE.match(line):
        return "declaration"
    if _RETURN_RE.match(line):
        return "return"
    if _IF_RE.match(line):
        return "conditional"
    if _LOOP_RE.match(line):
        return "loop"
    if _ASSIGN_RE.match(line):
        return "assignment"
    if _CALL_RE.search(line):
        return "function_call"
    return "statement"


def _label_for_ts_node(node_type: str) -> str:
    label_map = {
        "declaration": "declaration",
        "init_declarator": "declaration",
        "assignment_expression": "assignment",
        "call_expression": "function_call",
        "if_statement": "conditional",
        "for_statement": "loop",
        "while_statement": "loop",
        "do_statement": "loop",
        "return_statement": "return",
        "preproc_include": "preprocessor",
        "function_definition": "function_definition",
        "parameter_declaration": "parameter",
    }
    return label_map.get(node_type, "statement")


# ---------------------------------------------------------------------------
# ASTExtractor
# ---------------------------------------------------------------------------

class ASTExtractor:
    def __init__(self, language: str = 'c'):
        self.language = language
        self.parser = None
        self._init_parser()

    # ── Initialisation ─────────────────────────────────────────────

    def _init_parser(self):
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

    # ── Core parsing ───────────────────────────────────────────────

    def parse_code(self, source_code: str):
        if self.parser:
            return self.parser.parse(bytes(source_code, 'utf8'))
        return None

    def extract_ast(self, source_code: str) -> ASTNode:
        tree = self.parse_code(source_code)
        if tree:
            return self._convert_tree_sitter_node(tree.root_node, source_code)
        return self._create_fallback_ast(source_code)

    def _convert_tree_sitter_node(self, node, source_code: str) -> ASTNode:
        start_point = node.start_point
        end_point = node.end_point
        text = source_code[node.start_byte:node.end_byte]
        children = [self._convert_tree_sitter_node(c, source_code) for c in node.children]
        return ASTNode(
            node_type=node.type,
            start_line=start_point[0] + 1,
            end_line=end_point[0] + 1,
            start_col=start_point[1],
            end_col=end_point[1],
            text=text,
            children=children,
            semantic_label=_label_for_ts_node(node.type),
        )

    def _create_fallback_ast(self, source_code: str) -> ASTNode:
        lines = source_code.split('\n')
        return ASTNode(
            node_type='translation_unit',
            start_line=1,
            end_line=len(lines),
            start_col=0,
            end_col=len(lines[-1]) if lines else 0,
            text=source_code[:200],
            children=[],
            semantic_label='statement',
        )

    # ── Location lookup ────────────────────────────────────────────

    def find_node_at_location(self, ast: ASTNode, line: int, col: int) -> Optional[ASTNode]:
        if ast.start_line <= line <= ast.end_line:
            if line == ast.start_line and col < ast.start_col:
                return None
            if line == ast.end_line and col > ast.end_col:
                return None
            for child in ast.children:
                result = self.find_node_at_location(child, line, col)
                if result:
                    return result
            return ast
        return None

    # ── Symbol extraction ──────────────────────────────────────────

    def extract_symbols(self, source_code: str) -> List[Symbol]:
        symbols: List[Symbol] = []

        func_pattern = re.compile(r'(\w+)\s+(\w+)\s*\([^)]*\)\s*\{')
        for match in func_pattern.finditer(source_code):
            line_num = source_code[:match.start()].count('\n') + 1
            symbols.append(Symbol(
                name=match.group(2),
                symbol_type='function',
                data_type=match.group(1),
                scope='global',
                line_defined=line_num,
            ))

        var_pattern = re.compile(
            r'(?:int|float|double|char|void|long|short|unsigned)\s+(\w+)\s*[;=,\)]'
        )
        for match in var_pattern.finditer(source_code):
            line_num = source_code[:match.start()].count('\n') + 1
            scope = self._determine_scope(source_code, line_num)
            symbols.append(Symbol(
                name=match.group(1),
                symbol_type='variable',
                data_type=match.group(0).split()[0],
                scope=scope,
                line_defined=line_num,
            ))

        return symbols

    def _determine_scope(self, source_code: str, line_num: int) -> str:
        lines = source_code.split('\n')
        brace_count = 0
        for i, line in enumerate(lines[:line_num], 1):
            brace_count += line.count('{') - line.count('}')
        if brace_count == 0:
            return 'global'
        for i in range(line_num - 1, -1, -1):
            if '{' in lines[i] and any(
                keyword in lines[i] for keyword in ['int', 'void', 'float', 'double', 'char']
            ):
                func_match = re.search(r'(\w+)\s*\(', lines[i])
                if func_match:
                    return func_match.group(1)
        return 'local'

    # ── NEW: Variable dependency tracking ─────────────────────────

    def extract_variable_dependencies(self, source_code: str) -> List[VariableDependency]:
        """
        Build a dependency graph: for each assignment `x = expr`,
        record which variables on the RHS x depends on, and annotate
        the RHS variables with `used_by = x`.
        """
        lines = source_code.split('\n')
        dep_map: Dict[str, VariableDependency] = {}

        assign_re = re.compile(r'^\s*(?:\w+\s+)?(\w+)\s*(?:\+|-|\*|/|%)?=\s*(.+)')
        word_re = re.compile(r'\b([a-zA-Z_]\w*)\b')
        type_kws = {'int', 'float', 'double', 'char', 'void', 'long',
                    'short', 'unsigned', 'bool', 'return', 'if', 'else',
                    'for', 'while', 'do', 'NULL', 'true', 'false'}

        for line in lines:
            m = assign_re.match(line)
            if not m:
                continue
            lhs = m.group(1)
            rhs = m.group(2).rstrip(';').strip()

            # Collect identifiers on RHS (skip keywords and literals)
            rhs_vars = [
                v for v in word_re.findall(rhs)
                if v not in type_kws and not v[0].isdigit()
            ]
            if not rhs_vars:
                continue

            if lhs not in dep_map:
                dep_map[lhs] = VariableDependency(variable=lhs)
            dep_map[lhs].depends_on = list(set(
                dep_map[lhs].depends_on + rhs_vars
            ))

            for rv in rhs_vars:
                if rv not in dep_map:
                    dep_map[rv] = VariableDependency(variable=rv)
                if lhs not in dep_map[rv].used_by:
                    dep_map[rv].used_by.append(lhs)

        return list(dep_map.values())

    # ── NEW: Data flow analysis ────────────────────────────────────

    def extract_data_flow(self, source_code: str) -> List[DataFlowEntry]:
        """
        Produce an ordered list of definition/usage events for every
        variable, enabling def-use chain analysis.
        """
        lines = source_code.split('\n')
        events: List[DataFlowEntry] = []

        decl_re = re.compile(
            r'^\s*(?:int|float|double|char|void|long|short|unsigned|bool)\s+(\w+)\s*(?:=\s*(.+?))?;'
        )
        assign_re = re.compile(r'^\s*(\w+)\s*(?:\+|-|\*|/|%|&|\|)?=\s*(.+?);')
        word_re = re.compile(r'\b([a-zA-Z_]\w*)\b')
        type_kws = {'int', 'float', 'double', 'char', 'void', 'long',
                    'short', 'unsigned', 'bool', 'return', 'if', 'else',
                    'for', 'while', 'do', 'printf', 'scanf', 'NULL',
                    'true', 'false'}

        declared: Set[str] = set()

        for lineno, raw_line in enumerate(lines, 1):
            stripped = raw_line.strip()
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue

            # Declaration (with optional initialiser)
            dm = decl_re.match(raw_line)
            if dm:
                var = dm.group(1)
                declared.add(var)
                events.append(DataFlowEntry(
                    variable=var, event='definition', line=lineno, context=stripped
                ))
                # If there's an RHS, also record usages of any variables on it
                if dm.group(2):
                    for rv in word_re.findall(dm.group(2)):
                        if rv in declared and rv != var and rv not in type_kws:
                            events.append(DataFlowEntry(
                                variable=rv, event='usage', line=lineno, context=stripped
                            ))
                continue

            # Assignment (re-definition)
            am = assign_re.match(raw_line)
            if am:
                lhs = am.group(1)
                if lhs in declared:
                    events.append(DataFlowEntry(
                        variable=lhs, event='definition', line=lineno, context=stripped
                    ))
                rhs = am.group(2)
                for rv in word_re.findall(rhs):
                    if rv in declared and rv != lhs and rv not in type_kws:
                        events.append(DataFlowEntry(
                            variable=rv, event='usage', line=lineno, context=stripped
                        ))
                continue

            # Generic usage scan (expressions, function calls, conditions)
            for rv in word_re.findall(stripped):
                if rv in declared and rv not in type_kws:
                    events.append(DataFlowEntry(
                        variable=rv, event='usage', line=lineno, context=stripped
                    ))

        return events

    # ── NEW: Control flow extraction ───────────────────────────────

    def extract_control_flow(self, source_code: str) -> List[ControlFlowBlock]:
        """
        Identify control-flow blocks (if/else/for/while/do-while/switch)
        with their line ranges and conditions.
        """
        lines = source_code.split('\n')
        blocks: List[ControlFlowBlock] = []

        patterns = [
            ('if',       re.compile(r'^\s*if\s*\((.+)\)\s*\{?')),
            ('else_if',  re.compile(r'^\s*else\s+if\s*\((.+)\)\s*\{?')),
            ('else',     re.compile(r'^\s*else\s*\{?')),
            ('for',      re.compile(r'^\s*for\s*\((.+)\)\s*\{?')),
            ('while',    re.compile(r'^\s*while\s*\((.+)\)\s*\{?')),
            ('do_while', re.compile(r'^\s*do\s*\{?')),
            ('switch',   re.compile(r'^\s*switch\s*\((.+)\)\s*\{?')),
        ]

        # Stack-based brace tracker to find end lines
        block_stack: List[Tuple[int, str, str]] = []   # (start_line, type, cond)
        brace_depth = 0

        for lineno, raw_line in enumerate(lines, 1):
            line = raw_line.strip()

            # Detect block opening
            for block_type, pat in patterns:
                m = pat.match(line)
                if m:
                    cond = m.group(1) if block_type not in ('else', 'do_while') else ''
                    block_stack.append((lineno, block_type, cond.strip()))
                    break

            open_count = raw_line.count('{')
            close_count = raw_line.count('}')
            brace_depth += open_count - close_count

            # When we close a block, pop the stack
            if close_count > 0 and block_stack:
                start_line, block_type, cond = block_stack.pop()
                blocks.append(ControlFlowBlock(
                    block_type=block_type,
                    start_line=start_line,
                    end_line=lineno,
                    condition=cond,
                ))

        return blocks

    # ── NEW: Unreachable code detection (heuristic) ─────────────────

    def detect_unreachable_code(self, source_code: str) -> List[int]:
        """
        Simple heuristic: any statement on a line immediately after
        an unconditional `return` or `break` at the same or lower
        brace depth is likely unreachable.
        """
        lines = source_code.split('\n')
        unreachable: List[int] = []
        after_jump = False
        jump_depth = 0
        brace_depth = 0

        for lineno, raw_line in enumerate(lines, 1):
            stripped = raw_line.strip()
            brace_depth += raw_line.count('{') - raw_line.count('}')

            if after_jump:
                # If we went back up in scope the jump no longer applies
                if brace_depth < jump_depth:
                    after_jump = False
                elif stripped and not stripped.startswith('//'):
                    # Ignore closing braces / labels
                    if stripped not in ('}', '{') and not stripped.endswith(':'):
                        unreachable.append(lineno)

            jump_re = re.compile(r'^\s*(return|break|continue|goto)\b')
            if jump_re.match(raw_line):
                after_jump = True
                jump_depth = brace_depth

        return unreachable

    # ── NEW: Code window ───────────────────────────────────────────

    def get_code_window(
        self, source_code: str, error_line: int, window: int = 3
    ) -> CodeWindow:
        """Return ±window lines around error_line with the error line highlighted."""
        lines = source_code.split('\n')
        total = len(lines)
        start = max(1, error_line - window)
        end = min(total, error_line + window)

        window_lines = [
            (i, lines[i - 1]) for i in range(start, end + 1)
        ]
        highlighted = lines[error_line - 1] if 1 <= error_line <= total else ''

        return CodeWindow(
            error_line=error_line,
            window_start=start,
            window_end=end,
            lines=window_lines,
            highlighted_line=highlighted,
        )

    def format_code_window(self, window: CodeWindow) -> str:
        """Pretty-print the code window."""
        lines_out = []
        for lineno, text in window.lines:
            marker = '>>>' if lineno == window.error_line else '   '
            lines_out.append(f"  {marker} {lineno:4d} | {text}")
        return '\n'.join(lines_out)

    # ── Full context extraction ────────────────────────────────────

    def extract_context(
        self, source_code: str, error_line: int, error_col: int
    ) -> CodeContext:
        """Extract complete context around an error (all enhanced features)."""
        ast = self.extract_ast(source_code)
        symbols = self.extract_symbols(source_code)
        error_node = self.find_node_at_location(ast, error_line, error_col)
        scope_chain = self._build_scope_chain(source_code, error_line)

        functions = [s for s in symbols if s.symbol_type == 'function']
        variables = [s for s in symbols if s.symbol_type == 'variable']

        return CodeContext(
            ast_root=ast,
            symbols=symbols,
            functions=[asdict(f) for f in functions],
            variables=[asdict(v) for v in variables],
            error_node=error_node,
            scope_chain=scope_chain,
            dependencies=self.extract_variable_dependencies(source_code),
            data_flow=self.extract_data_flow(source_code),
            control_flow=self.extract_control_flow(source_code),
            code_window=self.get_code_window(source_code, error_line),
            unreachable_lines=self.detect_unreachable_code(source_code),
        )

    def _build_scope_chain(self, source_code: str, error_line: int) -> List[str]:
        lines = source_code.split('\n')
        scope_chain = ['global']
        for i in range(error_line - 1, -1, -1):
            if '{' in lines[i]:
                func_match = re.search(r'(\w+)\s*\([^)]*\)\s*\{', lines[i])
                if func_match:
                    scope_chain.append(func_match.group(1))
                    break
        return scope_chain

    # ── Visualisation ──────────────────────────────────────────────

    def visualize_ast(self, node: ASTNode, indent: int = 0) -> str:
        label = f"[{node.semantic_label}]" if node.semantic_label != "unknown" else ""
        result = (
            "  " * indent
            + f"{node.node_type}{label} "
            + f"[{node.start_line}:{node.start_col}]\n"
        )
        for child in node.children[:5]:
            result += self.visualize_ast(child, indent + 1)
        if len(node.children) > 5:
            result += "  " * (indent + 1) + "... (more children)\n"
        return result

    def summarize_context(self, ctx: CodeContext) -> str:
        """Return a concise human-readable summary of the enhanced context."""
        lines = ["=== Enhanced Code Context ==="]

        lines.append(f"Scope chain: {' -> '.join(ctx.scope_chain)}")

        if ctx.code_window:
            lines.append("\nCode Window:")
            lines.append(self.format_code_window(ctx.code_window))

        if ctx.control_flow:
            lines.append("\nControl Flow Blocks:")
            for cf in ctx.control_flow:
                cond_txt = f" ({cf.condition})" if cf.condition else ""
                lines.append(
                    f"  [{cf.block_type.upper()}]{cond_txt} "
                    f"lines {cf.start_line}–{cf.end_line}"
                )

        if ctx.unreachable_lines:
            lines.append(f"\nPotentially Unreachable Lines: {ctx.unreachable_lines}")

        if ctx.dependencies:
            lines.append("\nVariable Dependencies:")
            for dep in ctx.dependencies:
                if dep.depends_on:
                    lines.append(
                        f"  {dep.variable}  ←  {', '.join(dep.depends_on)}"
                    )

        if ctx.data_flow:
            lines.append("\nData Flow (definitions only):")
            for ev in ctx.data_flow:
                if ev.event == 'definition':
                    lines.append(f"  DEF  {ev.variable:15s} @ line {ev.line}")

        return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_code = """
#include <stdio.h>

int global_var = 10;

int add(int a, int b) {
    int result = a + b;
    return result;
    int dead = 99;
}

int main() {
    int x = 5;
    int y = 3;
    int z = x + y;
    if (z > 5) {
        printf("Big: %d\\n", z);
    } else {
        printf("Small: %d\\n", z);
    }
    for (int i = 0; i < z; i++) {
        printf("i=%d\\n", i);
    }
    return 0
}
"""

    extractor = ASTExtractor()

    # AST
    ast = extractor.extract_ast(sample_code)
    print("=== AST Structure ===")
    print(extractor.visualize_ast(ast))

    # Symbols
    symbols = extractor.extract_symbols(sample_code)
    print(f"\nFound {len(symbols)} symbols:")
    for sym in symbols:
        print(f"  {sym.name} ({sym.symbol_type}) : {sym.data_type} @ line {sym.line_defined}")

    # Full context around the missing-semicolon error (line 22 approx)
    ctx = extractor.extract_context(sample_code, 22, 12)
    print("\n" + extractor.summarize_context(ctx))