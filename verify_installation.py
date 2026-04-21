from main_system import CompilerErrorExplainerSystem, SystemConfig
import sys

def verify():
    print("Verifying installation...")
    try:
        config = SystemConfig(verbose=True, security_check_enabled=True)
        system = CompilerErrorExplainerSystem(config)
        
        simulated_output = """test.c:10:5: error: expected ';' before 'return'
    10 |     return 0
       |     ^
"""
        print("Running simulation...")
        results = system.process_file("dummy.c", simulate_output=simulated_output)
        
        if results and len(results) > 0:
            print("✓ Simulation successful")
            print(f"✓ Found {len(results)} errors")
            print(results[0].explanation.format_output())
        else:
            print("✗ Simulation failed to produce results")
            sys.exit(1)
            
    except ImportError as e:
        print(f"✗ Import Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
