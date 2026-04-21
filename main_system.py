"""
Compiler Error Explainer — Main Pipeline
=========================================
Integrates:
  • GCC-based error collection         (error_collector.py)
  • Enhanced AST extraction            (ast_extractor.py)
  • Rule-based NLP explanations        (nlp_baseline.py)
  • Transformer-based refinement       (transformer_training.py)
  • Security-aware filtering           (security_filter.py)
  • BLEU / ROUGE-L evaluation          (evaluation_metrics.py)  [NEW]
  • Green Compiler energy/carbon report(green_compiler.py)      [NEW]
"""

import os
import re
import json
import subprocess
import argparse
from typing import List, Optional, Dict
from dataclasses import dataclass, field

try:
    import torch
except ImportError:
    torch = None

print(">>> main_system.py is running")

# ── Core modules ──────────────────────────────────────────────────────────────
from error_collector import ErrorCollector, CompilerError

# ── Optional modules (graceful fallback) ─────────────────────────────────────
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

# ── NEW: Evaluation Metrics ───────────────────────────────────────────────────
try:
    from evaluation_metrics import EvaluationPipeline, DatasetEvaluationResult
    EVAL_AVAILABLE = True
except ImportError:
    EvaluationPipeline = None
    EVAL_AVAILABLE = False
    print("⚠️  evaluation_metrics.py not found — evaluation disabled.")

# ── NEW: Green Compiler ───────────────────────────────────────────────────────
try:
    from green_compiler import GreenCompiler, EnergyEstimate
    GREEN_AVAILABLE = True
except ImportError:
    GreenCompiler = None
    EnergyEstimate = None
    GREEN_AVAILABLE = False
    print("⚠️  green_compiler.py not found — energy analysis disabled.")


# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SystemConfig:
    use_simulation: bool = False
    use_transformer: bool = False
    transformer_model_path: Optional[str] = None
    security_check_enabled: bool = True
    output_format: str = "text"
    verbose: bool = False
    # NEW flags
    run_evaluation: bool = False          # compare against ground-truth refs
    run_green_analysis: bool = True       # always emit energy report
    evaluation_references: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Output dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ExplanationOutput:
    error: CompilerError
    explanation: Explanation
    security_analysis: Optional[object] = None
    # NEW
    enhanced_context: Optional[object] = None   # CodeContext (if AST available)
    energy_estimate: Optional[object] = None    # EnergyEstimate (if green available)

    def to_dict(self) -> Dict:
        d = {
            "error": self.error.to_dict(),
            "explanation": {
                "title": self.explanation.title,
                "description": self.explanation.description,
                "root_cause": self.explanation.root_cause,
                "fix": self.explanation.fix_suggestion,
            },
        }
        if self.energy_estimate:
            d["green_analysis"] = self.energy_estimate.to_dict()
        return d


# ──────────────────────────────────────────────────────────────────────────────
# Main system class
# ──────────────────────────────────────────────────────────────────────────────

class CompilerErrorExplainerSystem:

    def __init__(self, config: SystemConfig):
        self.config = config
        self.error_collector = ErrorCollector()
        self.ast_extractor = ASTExtractor() if ASTExtractor else None
        self.nlp_engine = RuleBasedNLPEngine() if RuleBasedNLPEngine else None
        self.security_filter = SecurityFilter() if SecurityFilter else None
        # NEW
        self.eval_pipeline = EvaluationPipeline() if EVAL_AVAILABLE else None
        self.green_compiler = GreenCompiler() if GREEN_AVAILABLE else None

        if config.verbose:
            print("✅ System initialised with all modules.")

    # ── Compilation ───────────────────────────────────────────────

    def compile_code(self, source_file: str) -> str:
        """Compile source file using GCC and capture raw output."""
        print(f"\n[Backend] Executing GCC on {source_file}...")
        try:
            result = subprocess.run(
                ["gcc", source_file, "-Wall", "-o", "output_exec"],
                capture_output=True,
                text=True,
                timeout=10,
            )
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

    # ── Main process_file ─────────────────────────────────────────

    def process_file(
        self,
        source_file: str,
        simulate_output: Optional[str] = None,
    ) -> List[ExplanationOutput]:
        """
        Full pipeline: compile → parse errors → explain → (optional) energy + eval.
        """
        # Read source once (needed for green analysis & enhanced AST)
        source_code = ""
        if os.path.exists(source_file):
            with open(source_file, "r", encoding="utf-8", errors="replace") as f:
                source_code = f.read()

        # ── Step 1: Collect compiler output ──────────────────────
        if simulate_output:
            print("(!) SIMULATION MODE: Using provided static output")
            compiler_output = simulate_output
        elif self.config.use_simulation:
            print("(!) SIMULATION MODE: Generating dynamic errors")
            compiler_output = self._simulate_gcc_output(source_file, source_code)
        else:
            compiler_output = self.compile_code(source_file)

        print("\n=== RAW COMPILER OUTPUT ===\n", compiler_output, "\n===========================\n")

        # ── Step 2: Parse errors ──────────────────────────────────
        errors = self.error_collector.parse_gcc_output(compiler_output)
        print("\n===== DEBUG: PARSED ERRORS FROM ERROR_COLLECTOR =====")
        print(errors)

        if not errors:
            print("⚠️ Primary parser failed. Using fallback regex parser.")
            fallback_pattern = r"(.+?):(\d+):(?:\d+:)?\s*(error|warning):\s*(.*)"
            matches = re.findall(fallback_pattern, compiler_output)
            print("Fallback matches:", matches)

            for match in matches:
                file_name, line, severity_str, message = match
                from error_collector import ErrorLocation, ErrorType, Severity
                severity = self.error_collector._parse_severity(severity_str) \
                    if hasattr(self.error_collector, '_parse_severity') \
                    else Severity.ERROR
                loc = ErrorLocation(file=file_name, line=int(line), column=1)
                fake_error = CompilerError(
                    error_id=f"{file_name}:{line}",
                    error_type=ErrorType.UNKNOWN,
                    severity=severity,
                    location=loc,
                    message=message.strip(),
                    raw_message=f"{file_name}:{line}: {severity_str}: {message}",
                    code_snippet=None,
                    context_lines=None,
                )
                errors.append(fake_error)

        if not errors:
            print("❌ STILL NO ERRORS DETECTED AFTER FALLBACK")
            return []

        # ── Step 3: Green (file-level, done once) ────────────────
        file_energy: Optional[object] = None
        if self.green_compiler and self.config.run_green_analysis and source_code:
            file_energy = self.green_compiler.analyse(source_code)
            print("\n" + file_energy.format())

        # ── Step 4: Generate explanations per error ───────────────
        results: List[ExplanationOutput] = []
        for error in errors:
            explanation = self.generate_explanation(error)

            # Enhanced AST context (per error)
            enhanced_ctx = None
            if self.ast_extractor and source_code:
                try:
                    enhanced_ctx = self.ast_extractor.extract_context(
                        source_code,
                        error.location.line,
                        error.location.column,
                    )
                    if self.config.verbose:
                        print(self.ast_extractor.summarize_context(enhanced_ctx))
                except Exception as e:
                    print(f"⚠️  AST context extraction failed: {e}")

            results.append(
                ExplanationOutput(
                    error=error,
                    explanation=explanation,
                    enhanced_context=enhanced_ctx,
                    energy_estimate=file_energy,   # shared across all errors
                )
            )

        # ── Step 5: Evaluation (optional) ────────────────────────
        if (
            self.config.run_evaluation
            and self.eval_pipeline
            and self.config.evaluation_references
        ):
            predictions = [r.explanation.description for r in results]
            references = self.config.evaluation_references[: len(predictions)]
            if len(references) == len(predictions):
                eval_result = self.eval_pipeline.evaluate_dataset(
                    predictions, references, verbose=self.config.verbose
                )
                print("\n" + eval_result.format_summary())
            else:
                print(
                    f"⚠️  Evaluation skipped: {len(predictions)} predictions "
                    f"but {len(references)} references provided."
                )

        return results

    # ── Simulation ────────────────────────────────────────────────

    def _simulate_gcc_output(self, filename: str, code: str) -> str:
        """Simulate GCC output via STRICT MULTI-PASS structural analysis."""
        output = []
        raw_lines = code.split('\n')
        
        # Clean lines + track line numbers (1-indexed)
        lines = []
        for i, original_line in enumerate(raw_lines, 1):
            line_str = re.sub(r'//.*', '', original_line)
            line_str = re.sub(r'/\*.*?\*/', '', line_str)
            lines.append((i, line_str.strip(), original_line))

        # PASS 1: SYMBOL TABLE CONSTRUCTION
        symbols = {} # name -> {"type": "int", "is_ptr": False, "is_array": False, "size": 0, "state": "UNINIT", "line": idx}
        types_regex = r'\b(int|float|double|char|bool|void)\b'
        
        for line_num, line, orig in lines:
            if not line: continue
            
            # CRITICAL: Strip string literals BEFORE extraction to avoid interference
            clean_decl_line = re.sub(r'".*?"', '""', line)
            clean_decl_line = re.sub(r"'.*?'", "''", clean_decl_line)

            # Consolidated Declaration Capture (Pointers, Arrays, Lists, Loops)
            # Find a type followed by a sequence of characters containing identifiers
            decl_chunk_match = re.search(rf'({types_regex})\s+([^;{{(]+)', clean_decl_line)
            if decl_chunk_match:
                ctype = decl_chunk_match.group(1)
                decls_part = decl_chunk_match.group(3)
                
                # Split by comma to handle 'int a, b=5'
                for part in decls_part.split(','):
                    part = part.strip()
                    # Extract variable name (handles '*ptr', 'arr[10]', 'var=5')
                    name_match = re.search(r'(\*?)\s*([a-zA-Z_]\w*)\s*(?:\[\s*(\d*)\s*\])?', part)
                    if name_match:
                        is_p = bool(name_match.group(1))
                        name = name_match.group(2)
                        size_str = name_match.group(3)
                        
                        if name in ('return', 'if', 'for', 'while', 'switch'): continue
                        
                        val = part.split('=')[1].strip() if '=' in part else None
                        state = "MALLOC" if val and 'malloc' in val else ("NULL" if val and 'NULL' in val else ("INIT" if val else "UNINIT"))
                        symbols[name] = {
                            "type": ctype, 
                            "is_ptr": is_p, 
                            "is_array": size_str is not None, 
                            "size": int(size_str) if size_str and size_str.isdigit() else 0,
                            "state": state, 
                            "line": line_num
                        }

            # Function Parameter Capture (e.g., int factorial(int n))
            func_def_match = re.search(r'\w+\s+\*?\s*\w+\s*\(([^)]*)\)', clean_decl_line)
            if func_def_match:
                params_str = func_def_match.group(1)
                for p in params_str.split(','):
                    p = p.strip()
                    if not p or p == 'void': continue
                    parts = p.split()
                    if len(parts) >= 2:
                        ctype = parts[0]
                        name = parts[-1].replace('*', '').strip()
                        symbols[name] = {"type": ctype, "is_ptr": '*' in p, "is_array": False, "state": "INIT", "line": line_num}

            # For-loop specific fallback (e.g., for (int i = 0; ...))
            if "for" in clean_decl_line:
                for_match = re.search(rf'for\s*\(\s*{types_regex}\s+([a-zA-Z_]\w*)', clean_decl_line)
                if for_match:
                    symbols[for_match.group(2)] = {"type": for_match.group(1), "is_ptr": False, "is_array": False, "state": "INIT", "line": line_num}

        ignore_keywords = {"if", "else", "for", "while", "return", "switch", "case", "int", "float", "double", "char", "void", "bool", "sizeof", "printf", "scanf", "gets", "strcpy", "strcat", "free", "malloc", "calloc", "NULL"}
        
        # Passes 2 to 7 processed line-by-line sequentially
        for line_num, line, orig in lines:
            if not line: continue
            
            is_func_def = re.match(r'^\w+\s+\w+\s*\([^)]*\)\s*{?$', line)

            # PASS 2: VARIABLE USAGE VALIDATION (Filter String Literals & Format Specifiers)
            clean_line = re.sub(r'".*?"', ' ', line)
            clean_line = re.sub(r"'.*?'", ' ', clean_line)
            
            words = re.findall(r'\b[a-zA-Z_]\w*\b', clean_line)
            for w in words:
                if w not in ignore_keywords and not is_func_def:
                    if w not in symbols and '_' not in w and not w.isupper():
                        # Function Name Filter (Ignore tokens acting as calls or macros)
                        if not re.search(rf'\b{w}\s*\(', line) and not line.startswith('#'):
                            output.append(f"{filename}:{line_num}:{max(orig.find(w),1)}: error: '{w}' was not declared in this scope")
                            symbols[w] = {"type": "unknown", "is_ptr": False, "is_array": False, "state": "INIT"}

            # PASS 3: TYPE ANALYSIS (Resilient to missing semi)
            assign_match = re.search(r'\b([a-zA-Z_]\w*)\s*=\s*(.+?)(?:;|$)', line)
            if assign_match:
                lhs, rhs = assign_match.group(1), assign_match.group(2).strip()
                if lhs in symbols:
                    lhs_node = symbols[lhs]
                    lhs_node["state"] = "INIT"
                    if lhs_node["is_ptr"] and 'malloc' in rhs: lhs_node["state"] = "MALLOC"
                    elif lhs_node["is_ptr"] and 'NULL' in rhs: lhs_node["state"] = "NULL"

                    if lhs_node["type"] == "int" and (re.match(r'^\d+\.\d+$', rhs) or re.search(rf'\.\d+', rhs)):
                        output.append(f"{filename}:{line_num}:{max(orig.find('='),1)}: warning: implicit conversion from 'float' to 'int'")
                    
                    for rw in re.findall(r'\b[a-zA-Z_]\w*\b', rhs):
                        if rw in symbols:
                            if symbols[rw]["type"] == "float" and lhs_node["type"] == "int":
                                output.append(f"{filename}:{line_num}:{max(orig.find('='),1)}: error: incompatible types 'float' to 'int'")
                            elif symbols[rw]["type"] == "int" and lhs_node["type"] == "float":
                                output.append(f"{filename}:{line_num}:{max(orig.find('='),1)}: warning: implicit conversion from 'int' to 'float'")

            # PASS 4: POINTER ANALYSIS (STATE TRACKING)
            for ptr_name, node in symbols.items():
                if node["is_ptr"] and (f"*{ptr_name}" in line or f"{ptr_name}->" in line):
                    if node["state"] == "NULL":
                        output.append(f"{filename}:{line_num}:{max(orig.find(ptr_name),1)}: error: null pointer dereference")
                    elif node["state"] == "UNINIT":
                        output.append(f"{filename}:{line_num}:{max(orig.find(ptr_name),1)}: error: uninitialized pointer dereference")
                    elif node["state"] == "MALLOC":
                        output.append(f"{filename}:{line_num}:{max(orig.find(ptr_name),1)}: warning: missing NULL check after malloc")
                        node["state"] = "INIT"  # Suppress repeat warnings

            # PASS 5: ARRAY BOUNDS CHECK
            arr_match = re.search(r'\b([a-zA-Z_]\w*)\s*\[\s*([^\]]+)\s*\]', line)
            if arr_match:
                arr_name, idx_expr = arr_match.group(1), arr_match.group(2).strip()
                if arr_name in symbols and symbols[arr_name]["is_array"]:
                    arr_size = symbols[arr_name]["size"]
                    if idx_expr.isdigit():
                        if int(idx_expr) >= arr_size:
                            output.append(f"{filename}:{line_num}:{max(orig.find('['),1)}: error: array subscript is above array bounds")
                    elif idx_expr in symbols:
                        output.append(f"{filename}:{line_num}:{max(orig.find('['),1)}: error: potential out of bounds (variable index '{idx_expr}' requires bounds check)")

            # PASS 6: DIVISION BY ZERO
            if re.search(r'/\s*0\b', line) and not re.search(r'/\s*0\.', line):
                output.append(f"{filename}:{line_num}:{max(orig.find('/'), 1)}: error: division by zero is undefined")
            if re.search(r'/\s*\(\s*([a-zA-Z_]\w*)\s*-\s*\1\s*\)', line):
                output.append(f"{filename}:{line_num}:{max(orig.find('/'), 1)}: error: division by zero in mathematical expression")

            # PASS 7: VULNERABILITY DETECTION
            if re.search(r'\b(gets|strcpy|strcat)\s*\(', line):
                func = re.search(r'\b(gets|strcpy|strcat)\b', line).group(1)
                output.append(f"{filename}:{line_num}:{max(orig.find(func),1)}: error: dangerous function '{func}' leads to Buffer Overflow")
            
            if re.search(r'\bprintf\s*\(\s*[a-zA-Z_]\w*\s*\)', line):
                output.append(f"{filename}:{line_num}:{max(orig.find('printf'),1)}: warning: Format String Vulnerability (user input passed directly)")
            
            free_match = re.search(r'\bfree\s*\(\s*([a-zA-Z_]\w*)\s*\)', line)
            if free_match:
                free_ptr = free_match.group(1)
                if free_ptr in symbols:
                    if symbols[free_ptr]["state"] == "FREED":
                        output.append(f"{filename}:{line_num}:{max(orig.find('free'),1)}: error: double free detected")
                    else:
                        symbols[free_ptr]["state"] = "FREED"

            # BASIC SYNTAX CHECKS
            is_control = re.match(r'^(if|for|while|switch)\b', line)
            is_macro = line.startswith('#')
            is_bracket = line.endswith('{') or line.endswith('}') or line.endswith('>')
            if not is_control and not is_macro and not is_bracket and not is_func_def and not line.endswith(';'):
                if re.match(r'^(int|float|double|char|return|printf|scanf|cout|cin|free)\b', line) or "=" in line:
                     output.append(f"{filename}:{line_num}:{len(orig)}: error: expected ';' at end of statement")

        # FILE LEVEL MEMORY LEAK CHECK
        for name, node in symbols.items():
            if node["is_ptr"] and node["state"] == "MALLOC":
                output.append(f"{filename}:{node['line']}:1: warning: Memory leak: '{name}' was allocated but never freed")

        if not output and len(code.strip()) > 0 and 'main' not in code:
            output.append(f"{filename}:1:1: error: undefined reference to 'main'")

        return "\n".join(output)

    # ── Explanation generation ────────────────────────────────────

    def generate_explanation(self, error: CompilerError) -> Explanation:
        explanation = None

        # STEP 1: Rule-Based NLP
        if self.nlp_engine:
            explanation = self.nlp_engine.generate_explanation(error.message, {})
        else:
            explanation = Explanation(
                title=f"{error.error_type.value.capitalize()} Error",
                description=error.message,
                root_cause="Compiler detected an issue in the code.",
                fix_suggestion="Review the error location and correct the syntax or declaration.",
            )

        # STEP 2: Transformer Refinement
        if self.config.use_transformer:
            try:
                from transformer_training import CompilerExplainerTrainer, TrainingConfig
                t_config = TrainingConfig()
                trainer = CompilerExplainerTrainer(t_config)
                combined_input = (
                    f"Error: {error.message}\n"
                    f"Type: {error.error_type.value}\n"
                    f"Description: {explanation.description}\n"
                    f"Root Cause: {explanation.root_cause}\n"
                    f"Fix: {explanation.fix_suggestion}\n"
                )
                refined_text = trainer.generate_explanation(
                    error.message, combined_input, error.error_type.value
                )
                explanation.description = refined_text
            except Exception as e:
                print("⚠️ Transformer refinement failed:", e)

        # STEP 3: Security Filter
        if self.security_filter and self.config.security_check_enabled:
            security_result = self.security_filter.analyze_suggestion(
                explanation.fix_suggestion, {}
            )
            if not security_result.is_safe:
                security_note = "\n".join(security_result.security_warnings)
                if explanation.security_note:
                    explanation.security_note += "\n" + security_note
                else:
                    explanation.security_note = security_note
                if security_result.filtered_suggestion:
                    explanation.fix_suggestion = security_result.filtered_suggestion

        return explanation

    # ── Output formatting ─────────────────────────────────────────

    def format_output(self, results: List[ExplanationOutput]) -> str:
        output = []
        output.append("\n" + "=" * 60)
        output.append("COMPILER ERROR EXPLANATION REPORT")
        output.append("=" * 60)

        for i, r in enumerate(results, 1):
            e = r.error
            output.append(f"\nError {i}")
            output.append("-" * 60)
            output.append(f"📍 {e.location.file}:{e.location.line}:{e.location.column}")
            output.append(f"⚠️  {e.severity.value.upper()}")
            output.append(f"💬 {e.message}")
            output.append(r.explanation.format_output())

            # Enhanced context summary
            if r.enhanced_context and self.ast_extractor:
                output.append("\n🌳 Enhanced AST Context:")
                output.append(self.ast_extractor.summarize_context(r.enhanced_context))

        # Green report (appears once, for the file)
        if results and results[0].energy_estimate:
            output.append("\n")
            output.append(results[0].energy_estimate.format())

        return "\n".join(output)

    # ── Standalone evaluation helper ──────────────────────────────

    def run_standalone_evaluation(
        self,
        predictions: List[str],
        references: List[str],
        verbose: bool = False,
    ) -> Optional["DatasetEvaluationResult"]:
        """
        Evaluate a pre-collected set of predictions against references.
        Can be called independently of process_file.
        """
        if not self.eval_pipeline:
            print("❌ Evaluation module not available.")
            return None
        result = self.eval_pipeline.evaluate_dataset(
            predictions, references, verbose=verbose
        )
        print(result.format_summary())
        if verbose:
            print(result.format_per_sample())
        return result

    # ── Standalone green analysis helper ─────────────────────────

    def run_standalone_green_analysis(self, source_code: str) -> Optional[object]:
        """Analyse any source-code string without a full pipeline run."""
        if not self.green_compiler:
            print("❌ Green Compiler module not available.")
            return None
        estimate = self.green_compiler.analyse(source_code)
        print(estimate.format())
        return estimate


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(">>> Starting full pipeline...")

    config = SystemConfig(
        use_simulation=False,
        use_transformer=False,
        verbose=True,
        run_green_analysis=True,
        run_evaluation=False,         # set True and supply references to activate
    )

    system = CompilerErrorExplainerSystem(config)

    test_file = "backend_test.c"

    if not os.path.exists(test_file):
        print(f"❌ File not found: {test_file}")
        exit()

    results = system.process_file(test_file)

    if results:
        print(system.format_output(results))

        # ── Demo: standalone evaluation ───────────────────────────
        sample_predictions = [r.explanation.description for r in results]
        sample_references = [
            "A semicolon is missing at the end of a C statement. "
            "Every statement must be terminated with a semicolon in C."
        ] * len(sample_predictions)

        print("\n\n=== STANDALONE EVALUATION DEMO ===")
        system.run_standalone_evaluation(
            sample_predictions, sample_references, verbose=True
        )
    else:
        print("No errors detected.")