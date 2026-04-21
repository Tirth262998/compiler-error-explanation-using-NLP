from main_system import CompilerErrorExplainerSystem, SystemConfig

def test_simulation_logic():
    print("Testing Simulation Logic...")
    
    # User's Code
    code = """#include<iostream>
using namespace std;

int main(){

  int x =5;
  float y= 3;
  int z = x+y
  cout<<z<<endl;
return 0;
}"""

    # Initialize System with Simulation Enabled
    config = SystemConfig(use_simulation=True, verbose=True)
    system = CompilerErrorExplainerSystem(config)
    
    # Direct access to the internal simulation method to test logic
    print("\n--- Simulating GCC Output ---")
    output = system._simulate_gcc_output("test.cpp", code)
    print(output)
    
    # Check compatibility with ErrorCollector
    from error_collector import ErrorCollector
    collector = ErrorCollector()
    parsed_errors = collector.parse_gcc_output(output)
    
    print(f"\n--- Parsed {len(parsed_errors)} errors ---")
    
    if len(parsed_errors) > 0:
        print("✅ SUCCESS: ErrorCollector successfully parsed the simulated errors.")
        for e in parsed_errors:
            print(f"- [{e.severity.value}] {e.error_type.value}: {e.message}")
    else:
        print("❌ FAILED: ErrorCollector found NO errors. output format mismatch?")
        
    # Check for specific logic
    if "expected ';'" in output:
        print("✅ SUCCESS: Logic detected missing semicolon.")
    else:
        print("❌ FAILED: Logic did not detect missing semicolon.")

if __name__ == "__main__":
    test_simulation_logic()
