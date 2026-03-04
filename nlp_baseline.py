
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Explanation:
    title: str
    description: str
    root_cause: str
    fix_suggestion: str
    example: Optional[str] = None
    analogy: Optional[str] = None
    security_note: Optional[str] = None
    
    def format_output(self) -> str:
        """Format explanation for display"""
        output = []
        output.append(f"━━━ {self.title} ━━━\n")
        output.append(f" Description:\n{self.description}\n")
        output.append(f" Root Cause:\n{self.root_cause}\n")
        output.append(f" Fix Suggestion:\n{self.fix_suggestion}\n")
        
        if self.example:
            output.append(f" Example:\n{self.example}\n")
        
        if self.analogy:
            output.append(f" Think of it like:\n{self.analogy}\n")
        
        if self.security_note:
            output.append(f"  Security Note:\n{self.security_note}\n")
        
        return "\n".join(output)

class ExplanationTemplate:
    def __init__(self, patterns: List[str], generator):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
        self.generator = generator
    
    def matches(self, message: str) -> bool:
        """Check if any pattern matches the error message"""
        return any(pattern.search(message) for pattern in self.patterns)
    
    def generate(self, error_message: str, context: Dict) -> Explanation:
        """Generate explanation using the template"""
        return self.generator(error_message, context)

class RuleBasedNLPEngine:
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> List[ExplanationTemplate]:
        """Initialize all explanation templates"""
        templates = []
        
        # Template 1: Missing semicolon
        templates.append(ExplanationTemplate(
            patterns=[r"expected\s+';'\s+before", r"expected\s+';'\s+at end"],
            generator=self._explain_missing_semicolon
        ))
        
        # Template 2: Undeclared variable
        templates.append(ExplanationTemplate(
            patterns=[
                r"'(\w+)'\s+was not declared in this scope",
                r"'(\w+)'\s+undeclared",
                r"use of undeclared identifier\s+'(\w+)'"
            ],
            generator=self._explain_undeclared_variable
        ))
        
        # Template 3: Type mismatch
        templates.append(ExplanationTemplate(
            patterns=[
                r"invalid conversion from\s+'([^']+)'\s+to\s+'([^']+)'",
                r"cannot convert\s+'([^']+)'\s+to\s+'([^']+)'",
                r"incompatible types"
            ],
            generator=self._explain_type_mismatch
        ))
        
        # Template 4: Missing header
        templates.append(ExplanationTemplate(
            patterns=[
                r"'(\w+)'\s+was not declared.*did you mean",
                r"implicit declaration of function\s+'(\w+)'"
            ],
            generator=self._explain_missing_header
        ))
        
        # Template 5: Unmatched braces
        templates.append(ExplanationTemplate(
            patterns=[
                r"expected\s+'}'\s+at end",
                r"expected\s+unqualified-id before\s+'}'",
                r"expected.*before\s+'}'"
            ],
            generator=self._explain_unmatched_brace
        ))
        
        # Template 6: Redefinition
        templates.append(ExplanationTemplate(
            patterns=[
                r"redefinition of\s+'(\w+)'",
                r"conflicting types for\s+'(\w+)'"
            ],
            generator=self._explain_redefinition
        ))
        
        # Template 7: Array subscript
        templates.append(ExplanationTemplate(
            patterns=[
                r"subscripted value is not an array",
                r"invalid types.*for array subscript"
            ],
            generator=self._explain_array_subscript
        ))
        
        # Template 8: Pointer issues
        templates.append(ExplanationTemplate(
            patterns=[
                r"invalid type argument of\s+'->'",
                r"request for member.*in something not a structure"
            ],
            generator=self._explain_pointer_issue
        ))

        # Template 9: Printf Format Mismatch
        templates.append(ExplanationTemplate(
            patterns=[
                r"format\s+'%[a-z]'\s+expects argument of type",
                r"format specifies type"
            ],
            generator=self._explain_printf_mismatch
        ))
        
        return templates
    
    def generate_explanation(self, error_message: str, context: Dict) -> Explanation:
        """Generate explanation for an error message"""
        # Try to match with templates
        for template in self.templates:
            if template.matches(error_message):
                return template.generate(error_message, context)
        
        # Fallback to generic explanation
        return self._explain_generic(error_message, context)
    
    def _explain_generic(self, msg: str, ctx: Dict) -> Explanation:
        return Explanation(
            title="🤔 Hmmm, let's look at this...",
            description=(
                f"The compiler is reporting: **{msg}**\n\n"
                "This isn't one of the usual suspects, but don't worry! "
                "It usually means the compiler got confused by the structure of your code."
            ),
            root_cause=(
                "The compiler reached a point where it couldn't understand your instructions. "
                "This often happens when there's a typo, a missing character, or a mismatch in brackets/parentheses "
                "that happened *before* the line reported."
            ),
            fix_suggestion=(
                "1. **Read the error message** carefully - does it mention a specific symbol?\n"
                "2. **Look closely at the line number** reported.\n"
                "3. **Check the lines *above*** the error. Missing semicolons `;` or braces `}` often cause errors on the *next* line.\n"
                "4. Check for typos in variable names or keywords."
            ),
            analogy=(
                "It's like reading a book where a sentence is missing a period. "
                "You might not realize something is wrong until you start the *next* sentence and it doesn't make sense."
            )
        )

    def _explain_missing_semicolon(self, msg: str, ctx: Dict) -> Explanation:
        return Explanation(
            title="💡 Missing Semicolon",
            description=(
                "It looks like you missed a semicolon `;` at the end of a statement. "
                "In C/C++, this is how we tell the computer 'I'm done with this specific instruction'."
            ),
            root_cause=(
                "The compiler was reading your code and expected to see a `;` to finish the command, "
                "but it bumped into something else instead. This usually happens right before the spot marked with `^`."
            ),
            fix_suggestion=(
                "**Add a semicolon (;)** at the end of the line.\n\n"
                "Check the line *above* the error error too, sometimes the compiler blames the next line!"
            ),
            example=(
                "**❌ Incorrect:**\n"
                "```c\n"
                "int x = 5\n"
                "return 0;\n"
                "```\n"
                "**✅ Correct:**\n"
                "```c\n"
                "int x = 5;  // Added semicolon here!\n"
                "return 0;\n"
                "```"
            ),
            analogy=(
                "Think of a semicolon like the full stop (period) at the end of a sentence. "
                "Without it, two sentences run together and become confusing!"
            )
        )

    def _explain_undeclared_variable(self, msg: str, ctx: Dict) -> Explanation:
        var_match = re.search(r"'(\w+)'", msg)
        var_name = var_match.group(1) if var_match else "variable"
        
        return Explanation(
            title=f"❓ Who is '{var_name}'?",
            description=(
                f"You're using a name **'{var_name}'** that the compiler doesn't recognize. "
                "It's like mentioning a friend's name to someone who has never met them!"
            ),
            root_cause=(
                f"The variable `{var_name}` hasn't been introduced (declared) in this part of the code (scope).\n\n"
                "Common reasons:\n"
                "1. You forgot to create it (e.g., `int {var_name};`).\n"
                "2. You made a typo (e.g., typing `count` as `cnt`).\n"
                "3. It was created inside another `{{}}` block, so it's hidden from here."
            ),
            fix_suggestion=(
                f"1. **Declare the variable** before using it: `int {var_name} = 0;`\n"
                f"2. **Check for spelling mistakes**.\n"
                f"3. Ensure the variable is defined in the correct `{{curly braces}}`."
            ),
            example=(
                "**❌ Incorrect:**\n"
                "```c\n"
                f"printf(\"%d\", {var_name}); // {var_name}? Who is that?\n"
                "```\n\n"
                "**✅ Correct:**\n"
                "```c\n"
                f"int {var_name} = 10; // Introduce {var_name} first!\n"
                f"printf(\"%d\", {var_name});\n"
                "```"
            ),
            analogy=(
                "Imagine walking into a coffee shop and saying 'I'll have the usual' "
                "without ever having been there before. The barista (compiler) won't know what you mean "
                "until you explain what 'the usual' is!"
            )
        )

    def _explain_type_mismatch(self, msg: str, ctx: Dict) -> Explanation:
        type_match = re.search(r"from\s+'([^']+)'\s+to\s+'([^']+)'", msg)
        if type_match:
            from_type = type_match.group(1)
            to_type = type_match.group(2)
        else:
            from_type, to_type = "one type", "another type"
        
        return Explanation(
            title="Type Mismatch / Invalid Conversion",
            description=(
                f"You're trying to convert from '{from_type}' to '{to_type}', "
                f"but C++ doesn't allow this conversion automatically. "
                f"Different data types store information differently."
            ),
            root_cause=(
                f"The compiler found a value of type '{from_type}' where it expected "
                f"type '{to_type}'. These types are incompatible, and automatic "
                f"conversion could lose data or cause undefined behavior."
            ),
            fix_suggestion=(
                f"1. Use the correct type from the start\n"
                f"2. Use explicit type casting if you understand the risks:\n"
                f"   {to_type} var = static_cast<{to_type}>(value);\n"
                f"3. Reconsider your design - maybe you need a different data structure"
            ),
            example=(
                "WRONG:\n"
                "    int x = \"hello\";  // Can't assign string to int\n\n"
                "CORRECT:\n"
                "    const char* x = \"hello\";  // Use correct type\n"
                "    // OR\n"
                "    std::string x = \"hello\";  // Use string class"
            ),
            analogy=(
                "It's like trying to fit a square peg in a round hole. "
                "The data shapes don't match, so the compiler refuses rather than "
                "risk corrupting your data."
            ),
            security_note=(
                " Forcing type conversions with C-style casts can bypass safety checks "
                "and lead to security vulnerabilities. Always prefer static_cast or "
                "reconsider your design."
            )
        )
    
    def _explain_missing_header(self, msg: str, ctx: Dict) -> Explanation:
        func_match = re.search(r"'(\w+)'", msg)
        func_name = func_match.group(1) if func_match else "function"
        
        # Common function -> header mappings
        header_map = {
            'printf': '<stdio.h>',
            'scanf': '<stdio.h>',
            'malloc': '<stdlib.h>',
            'free': '<stdlib.h>',
            'strlen': '<string.h>',
            'strcpy': '<string.h>',
            'strcmp': '<string.h>',
            'sqrt': '<math.h>',
            'pow': '<math.h>',
        }
        
        suggested_header = header_map.get(func_name, '<appropriate_header.h>')
        
        return Explanation(
            title=f"Missing Header for '{func_name}'",
            description=(
                f"The function '{func_name}' is being used but the compiler doesn't "
                f"know about it. This usually means you forgot to include the header "
                f"file that declares this function."
            ),
            root_cause=(
                f"Function '{func_name}' is defined in a standard library, but you "
                f"haven't included the necessary header file. The compiler needs the "
                f"declaration to know how to call the function properly."
            ),
            fix_suggestion=(
                f"Add this line at the top of your file:\n"
                f"    #include {suggested_header}\n\n"
                f"For standard C functions, always include the appropriate headers."
            ),
            example=(
                f"WRONG:\n"
                f"    int main() {{\n"
                f"        {func_name}(...);  // No header included\n"
                f"    }}\n\n"
                f"CORRECT:\n"
                f"    #include {suggested_header}  // Add this\n"
                f"    int main() {{\n"
                f"        {func_name}(...);\n"
                f"    }}"
            ),
            analogy=(
                "Headers are like phone books. If you want to call someone (use a function), "
                "you need to look up their number (function declaration) in the phone book "
                "(header file) first."
            )
        )
    
    def _explain_unmatched_brace(self, msg: str, ctx: Dict) -> Explanation:
        return Explanation(
            title="Unmatched Curly Brace",
            description=(
                "You have mismatched curly braces { }. Every opening brace needs a "
                "closing brace, and they must be properly nested."
            ),
            root_cause=(
                "Either you're missing a closing brace somewhere, or you have an extra "
                "one. This breaks the structure of your code and confuses the compiler "
                "about where blocks begin and end."
            ),
            fix_suggestion=(
                "1. Count your opening { and closing } braces - they should match\n"
                "2. Use proper indentation to see the structure clearly\n"
                "3. Many editors can highlight matching braces - use this feature\n"
                "4. Check functions, if statements, and loops for missing braces"
            ),
            example=(
                "WRONG:\n"
                "    int main() {\n"
                "        if (x > 0) {\n"
                "            printf(\"Positive\");\n"
                "        // Missing closing brace for if\n"
                "    // Missing closing brace for main\n\n"
                "CORRECT:\n"
                "    int main() {\n"
                "        if (x > 0) {\n"
                "            printf(\"Positive\");\n"
                "        }  // Closes if\n"
                "    }  // Closes main"
            ),
            analogy=(
                "Curly braces are like parentheses in math: (2 + (3 × 4)). "
                "Every opening needs a closing, and they must be in the right order. "
                "Your code's structure depends on this."
            )
        )
    
    def _explain_redefinition(self, msg: str, ctx: Dict) -> Explanation:
        name_match = re.search(r"of\s+'(\w+)'", msg)
        name = name_match.group(1) if name_match else "identifier"
        
        return Explanation(
            title=f"Redefinition of '{name}'",
            description=(
                f"You've defined '{name}' more than once, and the compiler doesn't "
                f"know which one to use. Each variable or function can only be defined once."
            ),
            root_cause=(
                f"The identifier '{name}' appears in multiple definitions. This could be:\n"
                f"  • The same variable declared twice\n"
                f"  • A function defined in multiple places\n"
                f"  • Including the same implementation file twice"
            ),
            fix_suggestion=(
                f"1. Search for all occurrences of '{name}' in your code\n"
                f"2. Keep only one definition\n"
                f"3. If you need '{name}' in multiple files, use:\n"
                f"   • extern for variables (declare in .h, define in one .c)\n"
                f"   • Function declarations in .h, definition in one .c\n"
                f"4. Use include guards in header files"
            ),
            example=(
                "WRONG:\n"
                f"    int {name} = 10;\n"
                f"    int {name} = 20;  // Redefinition!\n\n"
                "CORRECT:\n"
                f"    int {name} = 10;  // Defined once\n"
                f"    {name} = 20;      // Assignment, not definition"
            ),
            analogy=(
                "It's like having two people with the exact same name in a room. "
                "When you call that name, who should respond? The compiler has the "
                "same confusion."
            )
        )
    
    def _explain_array_subscript(self, msg: str, ctx: Dict) -> Explanation:
        return Explanation(
            title="Invalid Array Subscript",
            description=(
                "You're trying to use array indexing (brackets []) on something that "
                "isn't an array or pointer. Only arrays and pointers can be accessed "
                "using subscript notation."
            ),
            root_cause=(
                "The variable you're using brackets on is not an array type. It might be:\n"
                "  • A simple integer or other non-array type\n"
                "  • A variable you thought was an array but isn't\n"
                "  • A typo in the variable name"
            ),
            fix_suggestion=(
                "1. Check that you're using the correct variable name\n"
                "2. Make sure the variable is declared as an array: int arr[10];\n"
                "3. Or as a pointer: int* ptr;\n"
                "4. If it's supposed to be an array, fix the declaration"
            ),
            example=(
                "WRONG:\n"
                "    int x = 5;\n"
                "    int value = x[0];  // x is not an array!\n\n"
                "CORRECT:\n"
                "    int arr[5] = {1, 2, 3, 4, 5};\n"
                "    int value = arr[0];  // Now it works"
            ),
            analogy=(
                "It's like trying to open chapter 3 of a single-page document. "
                "Only books (arrays) have chapters (indices), not single pages (simple variables)."
            )
        )
    
    def _explain_pointer_issue(self, msg: str, ctx: Dict) -> Explanation:
        return Explanation(
            title="Pointer/Structure Access Error",
            description=(
                "You're trying to access a member using -> or . incorrectly. "
                "Use -> for pointers to structs, and . for struct variables directly."
            ),
            root_cause=(
                "Mismatch between the access operator and the variable type:\n"
                "  • Using -> on a non-pointer\n"
                "  • Using . on a pointer\n"
                "  • Trying to access members of a non-struct type"
            ),
            fix_suggestion=(
                "1. Use . for direct struct access: struct_var.member\n"
                "2. Use -> for pointer access: struct_ptr->member\n"
                "3. If you have a pointer, dereference first: (*struct_ptr).member\n"
                "4. Make sure your variable is actually a struct/class"
            ),
            example=(
                "WRONG:\n"
                "    struct Point p = {1, 2};\n"
                "    int x = p->x;  // Wrong! p is not a pointer\n\n"
                "CORRECT:\n"
                "    struct Point p = {1, 2};\n"
                "    int x = p.x;   // Use . for direct access\n\n"
                "    struct Point* ptr = &p;\n"
                "    int y = ptr->y;  // Use -> for pointers"
            ),
            analogy=(
                "Think of . as walking directly into a house, and -> as following "
                "an arrow (pointer) to find the house first, then entering. "
                "Use the right method based on what you have."
            )
        )

    def _explain_printf_mismatch(self, msg: str, ctx: Dict) -> Explanation:
        return Explanation(
            title="Printf Format Mismatch",
            description=(
                "You are telling `printf` to expect one type of data (like an integer), "
                "but you gave it something else (like a float or string)."
            ),
            root_cause=(
                "The format specifier (like `%d`) doesn't match the variable type you passed. "
                "For example, `%d` expects an `int`, but you might have passed a `float`."
            ),
            fix_suggestion=(
                "Match the format specifier to your variable type:\n"
                "- `%d` or `%i` for **int**\n"
                "- `%f` for **float**\n"
                "- `%lf` for **double**\n"
                "- `%c` for **char**\n"
                "- `%s` for **string** (char*)"
            ),
            example=(
                "**❌ Incorrect:**\n"
                "```c\n"
                "float pi = 3.14;\n"
                "printf(\"%d\", pi); // %d expects int, got float\n"
                "```\n"
                "**✅ Correct:**\n"
                "```c\n"
                "float pi = 3.14;\n"
                "printf(\"%f\", pi); // %f triggers correct handling\n"
                "```"
            ),
            analogy=(
                "It's like expecting a square peg to fit into a round hole. "
                "The placeholder `%d` is a specific shape (integer), and you tried to put a "
                "different shape (float) into it."
            )
        )

# Example usage
if __name__ == "__main__":
    engine = RuleBasedNLPEngine()
    
    # Test cases
    test_errors = [
        ("expected ';' before '}' token", {}),
        ("'count' was not declared in this scope", {}),
        ("invalid conversion from 'const char*' to 'int'", {}),
        ("'printf' was not declared in this scope", {}),
    ]
    
    for error_msg, context in test_errors:
        explanation = engine.generate_explanation(error_msg, context)
        print(explanation.format_output())
        print("\n" + "="*80 + "\n")