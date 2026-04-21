import os
import re
import csv
import time
import psutil
import matplotlib.pyplot as plt
import webbrowser

# Import Project Pipeline
try:
    from main_system import CompilerErrorExplainerSystem, SystemConfig
    from vulnerability_detector import VulnerabilityDetector
    PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"Error importing pipeline components: {e}")
    PIPELINE_AVAILABLE = False

# Configuration
TEST_DIR = "./test_programs"
RESULTS_CSV = "test_case_results.csv"
DASHBOARD_HTML = "report_dashboard.html"
DPI = 300
FIGSIZE = (6, 4)

def natural_sort_key(s):
    """Key for natural sorting."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def count_loc(source_code):
    """Count non-blank, non-comment lines."""
    count = 0
    in_block_comment = False
    for line in source_code.splitlines():
        stripped = line.strip()
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False
            continue
        if stripped.startswith('/*'):
            in_block_comment = True
            continue
        if stripped and not stripped.startswith('//'):
            count += 1
    return max(count, 1)

def run_project_pipeline(file_path, explainer_system, vuln_detector):
    """Execute the test case through the full project pipeline."""
    file_name = os.path.basename(file_path)
    
    source_code = ""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading {file_name}: {e}")
        return None

    loc = count_loc(source_code)
    
    # Initialize metrics
    metrics = {
        "test_case": file_name,
        "loc": loc,
        "time": 0,
        "cpu": 0,
        "energy": 0,
        "vulnerabilities": 0,
        "status": "failed"
    }

    try:
        # Run Pipeline
        print(f"--- Pipeline processing: {file_name} ---")
        pipeline_results = explainer_system.process_file(file_path)
        metrics["status"] = "success"
        
        # Extract Green Metrics
        est = None
        if pipeline_results and pipeline_results[0].energy_estimate:
            est = pipeline_results[0].energy_estimate
        else:
            # Fallback: Run green analysis standalone if pipeline returned no errors
            print(f"(!) No compiler errors found for {file_name}. Running standalone green analysis...")
            est = explainer_system.run_standalone_green_analysis(source_code)
            
        if est:
            metrics["time"] = round(getattr(est, 'estimated_execution_time_sec', 0), 6)
            # Use cpu_avg or cpu_utilization
            cpu_val = getattr(est, 'cpu_avg', 0)
            if cpu_val == 0: cpu_val = getattr(est, 'cpu_utilization', 0) * 100
            metrics["cpu"] = round(cpu_val, 2)
            metrics["energy"] = round(getattr(est, 'energy_joules', 0), 8)
        
        # Independent Vulnerability Detection (part of the security requirement)
        detected_vulns = vuln_detector.analyze(source_code)
        metrics["vulnerabilities"] = len(detected_vulns)
        
        print(f"Status: {metrics['status'].upper()} (Time: {metrics['time']}s, Energy: {metrics['energy']}J)")
        return metrics

    except Exception as e:
        print(f"Pipeline error for {file_name}: {e}")
        metrics["status"] = "failed"
        return metrics

def generate_graphs(results):
    """Generate the 5 required graphs using Matplotlib."""
    # Ensure sequential IDs for X-axis
    results.sort(key=lambda r: natural_sort_key(r['file_name']))
    
    test_ids = [str(r['test_case']) for r in results]
    locs = [r['loc'] for r in results]
    times = [r['time'] for r in results]
    energies = [r['energy'] for r in results]
    cpus = [r['cpu'] for r in results]

    plt.rcParams.update({'font.size': 10})

    # A. Execution Time vs Test Case
    plt.figure(figsize=FIGSIZE)
    plt.plot(test_ids, times, marker='o', linestyle='-')
    plt.title("Pipeline Execution Time Comparison")
    plt.xlabel("Test Case ID")
    plt.ylabel("Execution Time (seconds)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("execution_time.png", dpi=DPI)
    plt.close()

    # B. Energy Consumption vs Test Case
    plt.figure(figsize=FIGSIZE)
    plt.plot(test_ids, energies, marker='s', linestyle='-', color='green')
    plt.title("Pipeline Energy Consumption Comparison")
    plt.xlabel("Test Case ID")
    plt.ylabel("Energy Consumption (Joules)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("energy_comparison.png", dpi=DPI)
    plt.close()

    # C. CPU Utilization vs Test Case
    plt.figure(figsize=FIGSIZE)
    plt.bar(test_ids, cpus, color='orange')
    plt.title("Pipeline CPU Utilization per Test Case")
    plt.xlabel("Test Case ID")
    plt.ylabel("CPU Utilization (%)")
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.savefig("cpu_utilization.png", dpi=DPI)
    plt.close()

    # D. LOC vs Execution Time
    plt.figure(figsize=FIGSIZE)
    plt.scatter(locs, times, color='blue', alpha=0.6)
    plt.title("LOC vs Pipeline Execution Time")
    plt.xlabel("Lines of Code (LOC)")
    plt.ylabel("Execution Time (seconds)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("loc_vs_time.png", dpi=DPI)
    plt.close()

    # E. LOC vs Energy Consumption
    plt.figure(figsize=FIGSIZE)
    plt.scatter(locs, energies, color='red', alpha=0.6)
    plt.title("LOC vs Pipeline Energy Consumption")
    plt.xlabel("Lines of Code (LOC)")
    plt.ylabel("Energy Consumption (Joules)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("loc_vs_energy.png", dpi=DPI)
    plt.close()

def generate_dashboard(results):
    """Create report_dashboard.html with results table and all graphs."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Project Pipeline Performance Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #ffffff; color: #333; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            header {{ border-bottom: 3px solid #4CAF50; padding-bottom: 20px; margin-bottom: 30px; text-align: center; }}
            h1 {{ color: #2E7D32; }}
            section {{ margin-bottom: 60px; text-align: center; }}
            img {{ max-width: 100%; border: 1px solid #ddd; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 4px; }}
            h2 {{ color: #424242; border-left: 5px solid #4CAF50; padding-left: 10px; text-align: left; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #fff; }}
            th, td {{ border: 1px solid #eee; padding: 12px; text-align: center; }}
            th {{ background-color: #f8f9fa; color: #555; }}
            .status-failed {{ color: #d32f2f; font-weight: bold; }}
            .status-success {{ color: #388e3c; font-weight: bold; }}
            .caption {{ font-size: 0.9em; color: #666; font-style: italic; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Project Execution Report</h1>
                <p>Metrics captured through the full internal system pipeline.</p>
            </header>
            
            <section>
                <h2>1. Execution Time Comparison</h2>
                <img src="execution_time.png">
                <p class="caption">Analysis of pipeline duration across all test cases.</p>
            </section>

            <section>
                <h2>2. Energy Consumption Analysis</h2>
                <img src="energy_comparison.png">
                <p class="caption">Energy footprint estimation calculated during pipeline processing.</p>
            </section>

            <section>
                <h2>3. CPU Utilization Analysis</h2>
                <img src="cpu_utilization.png">
                <p class="caption">Peak CPU consumption overhead for each test scenario.</p>
            </section>

            <section>
                <h2>4. Correlation: LOC vs Time</h2>
                <img src="loc_vs_time.png">
                <p class="caption">Relationship between source code scale and processing latency.</p>
            </section>

            <section>
                <h2>5. Correlation: LOC vs Energy</h2>
                <img src="loc_vs_energy.png">
                <p class="caption">Impact of code volume on environmental metrics (Energy/CO2).</p>
            </section>

            <section>
                <h2>📊 Pipeline Results Summary</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>File Name</th>
                            <th>LOC</th>
                            <th>Time (s)</th>
                            <th>CPU (%)</th>
                            <th>Energy (J)</th>
                            <th>Vulns</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    for r in sorted(results, key=lambda x: x['test_case']):
        status_class = "status-success" if r['status'] == "success" else "status-failed"
        html_content += f"""
                        <tr>
                            <td>{r['test_case']}</td>
                            <td>{r['file_name']}</td>
                            <td>{r['loc']}</td>
                            <td>{r['time']}</td>
                            <td>{r['cpu']}</td>
                            <td>{r['energy']}</td>
                            <td>{r['vulnerabilities']}</td>
                            <td class="{status_class}">{r['status'].upper()}</td>
                        </tr>"""
    html_content += """
                    </tbody>
                </table>
            </section>
        </div>
    </body>
    </html>
    """
    with open(DASHBOARD_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    if not PIPELINE_AVAILABLE:
        print("❌ Cannot proceed without project pipeline modules.")
        return

    if not os.path.exists(TEST_DIR):
        print(f"❌ Error: Directory {TEST_DIR} not found.")
        return

    # Initialize Pipeline
    print("Initialising Project Compiler Explainer System...")
    config = SystemConfig(run_green_analysis=True, verbose=False)
    explainer_system = CompilerErrorExplainerSystem(config)
    vuln_detector = VulnerabilityDetector()

    all_files = sorted([f for f in os.listdir(TEST_DIR) if f.endswith(".c")], key=natural_sort_key)
    print(f"Found {len(all_files)} test programs. Commencing analysis...")
    
    results = []
    for i, file in enumerate(all_files, 1):
        file_path = os.path.join(TEST_DIR, file)
        res = run_project_pipeline(file_path, explainer_system, vuln_detector)
        
        if res:
            res['test_case'] = i
            res['file_name'] = file
            results.append(res)

    # Export CSV
    with open(RESULTS_CSV, 'w', newline='') as f:
        fieldnames = ["test_case", "file_name", "loc", "time", "cpu", "energy", "vulnerabilities", "status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Data exported to {RESULTS_CSV}")

    if results:
        print("Generating performance visualizations...")
        generate_graphs(results)
        generate_dashboard(results)
        print(f"Web Dashboard created: {DASHBOARD_HTML}")
        print("Opening report...")
        webbrowser.open('file://' + os.path.realpath(DASHBOARD_HTML))
    
    print("Pipeline Analysis Complete.")

if __name__ == "__main__":
    main()
