
import json
import os
from typing import List, Dict
import random

class DatasetGenerator:
   
    
    def __init__(self):
        self.examples = []
        self._initialize_templates()
    
    def _initialize_templates(self):
       
        
        # Syntax errors
        self.syntax_errors = [
            {
                'code': 'int main() {\n    int x = 5\n    return 0;\n}',
                'error': "expected ';' before 'return'",
                'type': 'syntax',
                'explanation': {
                    'description': 'You forgot to end the statement with a semicolon. In C/C++, almost every statement must end with a semicolon.',
                    'root_cause': 'The compiler expected a semicolon after "int x = 5" but found "return" instead.',
                    'fix': 'Add a semicolon after "int x = 5": int x = 5;',
                    'example': 'CORRECT: int x = 5; // Add semicolon'
                }
            },
            {
                'code': 'int main() {\n    int arr[5 = {1,2,3,4,5};\n}',
                'error': "expected ']' before '='",
                'type': 'syntax',
                'explanation': {
                    'description': 'Array declaration has incorrect syntax. The closing bracket is missing.',
                    'root_cause': 'You wrote [ instead of ] for the array size.',
                    'fix': 'Change int arr[5 to int arr[5]',
                    'example': 'CORRECT: int arr[5] = {1,2,3,4,5};'
                }
            },
            {
                'code': 'int main() {\n    printf("Hello\n}\n}',
                'error': "missing terminating \" character",
                'type': 'syntax',
                'explanation': {
                    'description': 'String literal is not properly closed with a quote.',
                    'root_cause': 'The opening quote for the string has no matching closing quote.',
                    'fix': 'Add closing quote: printf("Hello");',
                    'example': 'CORRECT: printf("Hello\\n");'
                }
            },
            {
                'code': 'int main() \n    int x = 5;\n    return 0;\n}',
                'error': "expected '{' before 'int'",
                'type': 'syntax',
                'explanation': {
                    'description': 'Function definition missing opening brace.',
                    'root_cause': 'After function declaration, you need { to start the function body.',
                    'fix': 'Add { after main(): int main() {',
                    'example': 'CORRECT: int main() { // Add opening brace'
                }
            },
            {
                'code': 'int main() {\n    if (x > 0\n        printf("Positive");\n}',
                'error': "expected ')' before 'printf'",
                'type': 'syntax',
                'explanation': {
                    'description': 'Parenthesis not properly closed in if condition.',
                    'root_cause': 'The opening ( in the if statement has no matching closing ).',
                    'fix': 'Add closing parenthesis: if (x > 0)',
                    'example': 'CORRECT: if (x > 0) // Close parenthesis'
                }
            }
        ]
        
        # Semantic errors
        self.semantic_errors = [
            {
                'code': 'int main() {\n    printf("%d", count);\n    return 0;\n}',
                'error': "'count' was not declared in this scope",
                'type': 'semantic',
                'explanation': {
                    'description': 'The variable "count" is being used without being declared first.',
                    'root_cause': 'Variables must be declared before use. The compiler does not know what "count" is.',
                    'fix': 'Declare the variable before using it: int count = 0;',
                    'example': 'int count = 0; // Declare first\nprintf("%d", count);'
                }
            },
            {
                'code': '#include <stdio.h>\nint main() {\n    int x = 5;\n}\nint x = 10;',
                'error': "redefinition of 'x'",
                'type': 'semantic',
                'explanation': {
                    'description': 'Variable "x" is defined more than once at the global scope.',
                    'root_cause': 'You cannot have two variables with the same name in the same scope.',
                    'fix': 'Remove one definition or rename one variable.',
                    'example': 'Use different names: int x = 5; int y = 10;'
                }
            },
            {
                'code': 'void func(int a, int b);\nint main() {\n    func(5);\n}',
                'error': "too few arguments to function 'func'",
                'type': 'semantic',
                'explanation': {
                    'description': 'Function "func" expects 2 arguments but only 1 was provided.',
                    'root_cause': 'The function declaration specifies 2 parameters (a and b), but the call only passes 1.',
                    'fix': 'Provide all required arguments: func(5, 10);',
                    'example': 'CORRECT: func(5, 10); // Pass both arguments'
                }
            },
            {
                'code': 'int main() {\n    const int x = 5;\n    x = 10;\n}',
                'error': "assignment of read-only variable 'x'",
                'type': 'semantic',
                'explanation': {
                    'description': 'Attempting to modify a const variable, which is not allowed.',
                    'root_cause': 'Variable "x" is declared as const, meaning its value cannot be changed.',
                    'fix': 'Either remove const or do not modify the variable.',
                    'example': 'int x = 5; // Remove const if you need to modify'
                }
            }
        ]
        
        # Type errors
        self.type_errors = [
            {
                'code': 'int main() {\n    int x = "hello";\n    return 0;\n}',
                'error': "invalid conversion from 'const char*' to 'int'",
                'type': 'type',
                'explanation': {
                    'description': 'Attempting to assign a string to an integer variable.',
                    'root_cause': 'Strings and integers are different types and cannot be directly assigned.',
                    'fix': 'Use correct type: const char* x = "hello";',
                    'example': 'const char* x = "hello"; // Correct type for strings'
                }
            },
            {
                'code': 'int add(int a, int b) {\n    return a + b;\n}\nint main() {\n    add(3.14, 2.5);\n}',
                'error': "cannot convert 'double' to 'int' in argument passing",
                'type': 'type',
                'explanation': {
                    'description': 'Passing double values to function expecting int parameters.',
                    'root_cause': 'Function "add" expects int arguments, but floating-point values were passed.',
                    'fix': 'Either cast to int or change function to accept double.',
                    'example': 'double add(double a, double b) { ... } // Accept doubles'
                }
            },
            {
                'code': 'int main() {\n    int* ptr;\n    int x = ptr;\n}',
                'error': "invalid conversion from 'int*' to 'int'",
                'type': 'type',
                'explanation': {
                    'description': 'Attempting to assign a pointer to a non-pointer variable.',
                    'root_cause': 'ptr is a pointer (int*) but x is a regular int. These types are incompatible.',
                    'fix': 'Dereference the pointer: int x = *ptr; or make x a pointer: int* x = ptr;',
                    'example': 'int x = *ptr; // Dereference to get the value'
                }
            },
            {
                'code': 'int main() {\n    int arr[5];\n    int x = arr;\n}',
                'error': "invalid conversion from 'int*' to 'int'",
                'type': 'type',
                'explanation': {
                    'description': 'Array name decays to pointer, cannot be assigned to int.',
                    'root_cause': 'Array name "arr" is treated as a pointer to its first element.',
                    'fix': 'Use int* x = arr; or access element: int x = arr[0];',
                    'example': 'int* x = arr; // arr is a pointer\nint y = arr[0]; // Get first element'
                }
            }
        ]
        
        # Missing include errors
        self.include_errors = [
            {
                'code': 'int main() {\n    printf("Hello");\n    return 0;\n}',
                'error': "'printf' was not declared in this scope",
                'type': 'semantic',
                'explanation': {
                    'description': 'Function "printf" is not declared because <stdio.h> is not included.',
                    'root_cause': 'printf is defined in the standard I/O library, which requires including <stdio.h>.',
                    'fix': 'Add #include <stdio.h> at the beginning of the file.',
                    'example': '#include <stdio.h>\nint main() { printf("Hello"); }'
                }
            },
            {
                'code': 'int main() {\n    int* ptr = malloc(sizeof(int));\n}',
                'error': "'malloc' was not declared in this scope",
                'type': 'semantic',
                'explanation': {
                    'description': 'Function "malloc" requires including <stdlib.h>.',
                    'root_cause': 'malloc is part of the standard library, defined in <stdlib.h>.',
                    'fix': 'Add #include <stdlib.h> at the beginning.',
                    'example': '#include <stdlib.h>\nint* ptr = malloc(sizeof(int));'
                }
            },
            {
                'code': 'int main() {\n    char str[20];\n    strcpy(str, "hello");\n}',
                'error': "'strcpy' was not declared in this scope",
                'type': 'semantic',
                'explanation': {
                    'description': 'String function "strcpy" requires <string.h>.',
                    'root_cause': 'strcpy and other string functions are declared in <string.h>.',
                    'fix': 'Add #include <string.h>',
                    'example': '#include <string.h>\nstrcpy(str, "hello");'
                }
            }
        ]
    
    def generate_dataset(self, num_examples: int = 1000) -> List[Dict]:
        """Generate complete dataset with variations"""
        dataset = []
        
        all_templates = (
            self.syntax_errors + 
            self.semantic_errors + 
            self.type_errors + 
            self.include_errors
        )
        
        # Generate base examples
        for template in all_templates:
            dataset.append({
                'error_message': template['error'],
                'error_type': template['type'],
                'code_snippet': template['code'],
                'explanation': template['explanation'],
                'context': self._extract_context(template['code'])
            })
        
        # Generate variations to reach target count
        while len(dataset) < num_examples:
            template = random.choice(all_templates)
            
            # Create variation
            varied_example = self._create_variation(template)
            dataset.append(varied_example)
        
        return dataset[:num_examples]
    
    def _extract_context(self, code: str) -> str:
        """Extract contextual information from code"""
        lines = code.split('\n')
        functions = [line.strip() for line in lines if 'int main' in line or 'void ' in line]
        variables = [line.strip() for line in lines if 'int ' in line or 'char ' in line]
        
        context = f"Functions: {', '.join(functions[:3]) if functions else 'None'}"
        return context
    
    def _create_variation(self, template: Dict) -> Dict:
        """Create variation of existing template"""
        # Simple variations: change variable names, values, etc.
        code = template['code']
        
        # Variations dictionary
        variations = {
            'x': random.choice(['num', 'value', 'data', 'result']),
            'count': random.choice(['total', 'sum', 'counter', 'index']),
            'arr': random.choice(['array', 'list', 'data', 'values']),
            '5': str(random.randint(1, 100)),
            '10': str(random.randint(1, 100)),
        }
        
        varied_code = code
        for old, new in variations.items():
            if random.random() < 0.3:  # 30% chance to apply variation
                varied_code = varied_code.replace(old, new)
        
        return {
            'error_message': template['error'],
            'error_type': template['type'],
            'code_snippet': varied_code,
            'explanation': template['explanation'],
            'context': self._extract_context(varied_code)
        }
    
    def save_dataset(self, output_dir: str, train_ratio: float = 0.8):
        """Generate and save train/val/test splits"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate dataset
        print("Generating dataset...")
        dataset = self.generate_dataset(1000)
        
        # Shuffle
        random.shuffle(dataset)
        
        # Split
        train_size = int(len(dataset) * train_ratio)
        val_size = int(len(dataset) * 0.1)
        
        train_data = dataset[:train_size]
        val_data = dataset[train_size:train_size + val_size]
        test_data = dataset[train_size + val_size:]
        
        # Save
        print(f"Saving datasets to {output_dir}/...")
        print(f"  Train: {len(train_data)} examples")
        print(f"  Val: {len(val_data)} examples")
        print(f"  Test: {len(test_data)} examples")
        
        with open(os.path.join(output_dir, 'train.json'), 'w') as f:
            json.dump(train_data, f, indent=2)
        
        with open(os.path.join(output_dir, 'val.json'), 'w') as f:
            json.dump(val_data, f, indent=2)
        
        with open(os.path.join(output_dir, 'test.json'), 'w') as f:
            json.dump(test_data, f, indent=2)
        
        print("✓ Dataset generation complete!")

def generate_faulty_programs(output_dir: str):
    """Generate sample faulty C programs for testing"""
    
    programs = [
        # Program 1: Missing semicolon
        {
            'filename': 'missing_semicolon.c',
            'code': '''#include <stdio.h>

int main() {
    int x = 5
    int y = 10;
    printf("Sum: %d\\n", x + y);
    return 0;
}
'''
        },
        
        # Program 2: Undeclared variable
        {
            'filename': 'undeclared_var.c',
            'code': '''#include <stdio.h>

int main() {
    int x = 5;
    printf("Value: %d\\n", count);
    return 0;
}
'''
        },
        
        # Program 3: Type mismatch
        {
            'filename': 'type_mismatch.c',
            'code': '''#include <stdio.h>

int main() {
    int x = "hello world";
    printf("X: %d\\n", x);
    return 0;
}
'''
        },
        
        # Program 4: Missing header
        {
            'filename': 'missing_header.c',
            'code': '''int main() {
    printf("Hello World\\n");
    return 0;
}
'''
        },
        
        # Program 5: Unmatched braces
        {
            'filename': 'unmatched_braces.c',
            'code': '''#include <stdio.h>

int main() {
    if (1 > 0) {
        printf("Positive\\n");
    
    return 0;
}
'''
        },
        
        # Program 6: Buffer overflow (unsafe)
        {
            'filename': 'unsafe_buffer.c',
            'code': '''#include <stdio.h>
#include <string.h>

int main() {
    char buffer[10];
    char* input = "This is a very long string that will overflow";
    strcpy(buffer, input);  // Unsafe!
    printf("Buffer: %s\\n", buffer);
    return 0;
}
'''
        },
        
        # Program 7: Null pointer
        {
            'filename': 'null_pointer.c',
            'code': '''#include <stdio.h>
#include <stdlib.h>

int main() {
    int* ptr = malloc(sizeof(int));
    *ptr = 100;  // No null check!
    printf("Value: %d\\n", *ptr);
    free(ptr);
    return 0;
}
'''
        },
        
        # Program 8: Array bounds
        {
            'filename': 'array_bounds.c',
            'code': '''#include <stdio.h>

int main() {
    int arr[5] = {1, 2, 3, 4, 5};
    for (int i = 0; i <= 5; i++) {  // Off-by-one!
        printf("%d ", arr[i]);
    }
    return 0;
}
'''
        }
    ]
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating {len(programs)} test programs in {output_dir}/...")
    
    for prog in programs:
        filepath = os.path.join(output_dir, prog['filename'])
        with open(filepath, 'w') as f:
            f.write(prog['code'])
        print(f"  ✓ {prog['filename']}")
    
    print("✓ Test programs generated!")

# Main execution
if __name__ == "__main__":
    # Generate training dataset
    generator = DatasetGenerator()
    generator.save_dataset('data')
    
    # Generate test programs
    generate_faulty_programs('test_programs')
    
    print("\n" + "="*60)
    print("Dataset generation complete!")
    print("="*60)
    print("\nGenerated files:")
    print("  data/train.json - Training dataset")
    print("  data/val.json - Validation dataset")
    print("  data/test.json - Test dataset")
    print("  test_programs/*.c - Sample faulty programs")