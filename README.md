# AI Compiler Error Explainer

An intelligent tool that analyzes compiler errors and converts them into **simple natural-language explanations** to help developers understand and fix coding mistakes quickly.

---

##  Overview

Compiler error messages are often difficult for beginners to understand.
This project builds an AI-assisted system that **detects compiler errors, analyzes code structure, and explains the problem in plain language with suggested fixes.**

The system uses a **hybrid NLP approach** that combines rule-based techniques with transformer models.

---

##  Key Features

* Converts compiler errors into **easy-to-understand explanations**
* Uses **AST-based code analysis** for deeper context
* Suggests **best-practice fixes**
* Filters **insecure coding patterns**
* Interactive frontend built with **Streamlit**

---

##  Tech Stack

* Python
* Regular Expressions (Regex)
* **Tree-sitter** for AST parsing
* Transformer NLP models like **BERT** / **CodeBERT**
* **Streamlit** for UI

---

##  System Workflow

```
Source Code
   ↓
Compiler
   ↓
Error Collector
   ↓
Regex Parser
   ↓
AST Analysis
   ↓
NLP Explanation Engine
   ↓
Frontend Display
```

---

##  Run the Project

Install dependencies:

```
pip install -r requirements.txt
```

Run the application:

```
python -m streamlit run app.py
```

---

##  Goal

Make compiler debugging **simpler, faster, and more understandable** for students and developers using AI-assisted error explanations.
