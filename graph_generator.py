import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections

# Global settings for compact display
plt.rcParams.update({'font.size': 8})

def generate_vulnerability_graphs(vulnerabilities):
    """
    Generate 3 vulnerability visualization graphs using matplotlib.
    Returns the list of figure objects.
    """
    # 1. Edge Case: Empty list
    if not vulnerabilities:
        fig1, ax1 = plt.subplots(figsize=(5, 3))
        ax1.set_title("No Vulnerabilities Detected")
        ax1.text(0.5, 0.5, "No issues found in the code analysis.", ha='center', va='center')
        fig1.tight_layout()

        fig2, ax2 = plt.subplots(figsize=(5, 3))
        ax2.set_title("No Vulnerabilities Detected")
        fig2.tight_layout()

        fig3, ax3 = plt.subplots(figsize=(5, 3))
        ax3.set_title("No Vulnerabilities Detected")
        fig3.tight_layout()

        return [fig1, fig2, fig3]

    # Data Preparation
    types = [v['type'] for v in vulnerabilities]
    severities = [v['severity'] for v in vulnerabilities]
    lines = [v['line'] for v in vulnerabilities]

    type_counts = collections.Counter(types)
    severity_counts = collections.Counter(severities)

    # 1. Bar Chart: Vulnerability Count vs Type
    fig1, ax1 = plt.subplots(figsize=(5, 3))
    ax1.bar(type_counts.keys(), type_counts.values())
    ax1.set_title("Vulnerability Count vs Type")
    ax1.set_xlabel("Vulnerability Type")
    ax1.set_ylabel("Count")
    plt.xticks(rotation=30, ha='right')
    fig1.tight_layout()

    # 2. Pie Chart: Severity Distribution
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    ax2.pie(severity_counts.values(), labels=severity_counts.keys(), autopct='%1.1f%%')
    ax2.set_title("Severity Distribution")
    fig2.tight_layout()

    # 3. Scatter Plot: Vulnerabilities vs Line Number
    fig3, ax3 = plt.subplots(figsize=(5, 3))
    ax3.scatter(lines, [1] * len(lines), alpha=0.5, s=80) 
    ax3.set_title("Vulnerabilities vs Line Number")
    ax3.set_xlabel("Line Number")
    ax3.set_ylabel("Occurrences")
    ax3.set_yticks([]) # Hide Y axis as it's just a distribution
    plt.xticks(rotation=30)
    fig3.tight_layout()

    return [fig1, fig2, fig3]
