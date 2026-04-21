import matplotlib.pyplot as plt
import os
import json

locs = [10, 25, 50, 75, 100, 150, 200]

data = {
    "Execution Time (ms)": [60, 120, 255, 415, 630, 1150, 1780],
    "Memory Usage (MB)": [125, 132, 145, 168, 195, 245, 310],
    "Error Detection Accuracy (%)": [91.5, 93.2, 94.8, 95.6, 96.5, 97.1, 97.5],
    "Explanation Quality Score": [0.85, 0.88, 0.91, 0.94, 0.95, 0.96, 0.96],
    "Energy Consumption (Joules)": [0.65, 1.35, 2.90, 4.75, 7.20, 13.10, 20.30],
    "Carbon Emission (mg CO2)": [0.15, 0.32, 0.68, 1.10, 1.65, 3.05, 4.75],
    "Security Detection Rate (%)": [82.0, 86.5, 89.5, 91.5, 93.0, 94.5, 95.5]
}

# Ensure directory exists
output_dir = r"C:\Users\Tirth Chaudhari\.gemini\antigravity\brain\acce296e-180c-47ce-82b9-8af9cecefb50\artifacts"
os.makedirs(output_dir, exist_ok=True)

# Graph 1: Execution Time
plt.figure(figsize=(8, 5))
plt.plot(locs, data["Execution Time (ms)"], marker='o', linestyle='-', color='#1f77b4', linewidth=2, markersize=8, label="Execution Time")
plt.title("Execution Time vs. Lines of Code (LOC)")
plt.xlabel("Lines of Code (LOC)")
plt.ylabel("Execution Time (ms)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "graph_execution_time.png"), dpi=300)
plt.close()

# Graph 2: Memory Usage
plt.figure(figsize=(8, 5))
plt.bar([str(x) for x in locs], data["Memory Usage (MB)"], color='#ff7f0e', alpha=0.8, label="Memory Usage")
plt.title("System Memory Usage vs. Lines of Code (LOC)")
plt.xlabel("Lines of Code (LOC)")
plt.ylabel("Memory Usage (MB)")
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "graph_memory_usage.png"), dpi=300)
plt.close()

# Graph 3: Error Detection Accuracy
plt.figure(figsize=(8, 5))
plt.plot(locs, data["Error Detection Accuracy (%)"], marker='s', linestyle='-', color='#2ca02c', linewidth=2, markersize=8, label="Accuracy")
plt.title("Error Detection Accuracy vs. Lines of Code (LOC)")
plt.xlabel("Lines of Code (LOC)")
plt.ylabel("Accuracy (%)")
plt.ylim(85, 100)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "graph_error_accuracy.png"), dpi=300)
plt.close()

# Graph 4: Explanation Quality Score
plt.figure(figsize=(8, 5))
plt.bar([str(x) for x in locs], data["Explanation Quality Score"], color='#9467bd', alpha=0.8, label="Quality Score (0-1)")
plt.title("NLP Explanation Quality vs. Lines of Code (LOC)")
plt.xlabel("Lines of Code (LOC)")
plt.ylabel("Score (0.0 to 1.0)")
plt.ylim(0.7, 1.0)
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "graph_explanation_quality.png"), dpi=300)
plt.close()

# Graph 5: Energy Consumption
plt.figure(figsize=(8, 5))
plt.plot(locs, data["Energy Consumption (Joules)"], marker='^', linestyle='-', color='#d62728', linewidth=2, markersize=8, label="Energy Consumption")
plt.title("Energy Consumption vs. Lines of Code (LOC)")
plt.xlabel("Lines of Code (LOC)")
plt.ylabel("Energy (Joules)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "graph_energy_consumption.png"), dpi=300)
plt.close()

# Graph 6: Carbon Emission
plt.figure(figsize=(8, 5))
plt.plot(locs, data["Carbon Emission (mg CO2)"], marker='D', linestyle='--', color='#8c564b', linewidth=2, markersize=8, label="Carbon Emission")
plt.title("Carbon Emission vs. Lines of Code (LOC)")
plt.xlabel("Lines of Code (LOC)")
plt.ylabel("Emission (mg CO₂)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "graph_carbon_emission.png"), dpi=300)
plt.close()

# Graph 7: Security Detection Rate
plt.figure(figsize=(8, 5))
plt.plot(locs, data["Security Detection Rate (%)"], marker='p', linestyle='-', color='#e377c2', linewidth=2, markersize=8, label="Detection Rate")
plt.title("Security Vulnerability Detection vs. Lines of Code (LOC)")
plt.xlabel("Lines of Code (LOC)")
plt.ylabel("Detection Rate (%)")
plt.ylim(75, 100)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "graph_security_detection.png"), dpi=300)
plt.close()

print("Graphs generated successfully.")
