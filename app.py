import streamlit as st
import os
import tempfile
from main_system import CompilerErrorExplainerSystem, SystemConfig

st.set_page_config(
    page_title="Compiler Error Explainer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Mode (Developer Theme)
st.markdown("""
<style>
    /* Dark Background */
    .stApp {
        background-color: #0e1117;
        color: #e6e6e6;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        padding-bottom: 20px;
    }
    
    h2, h3 {
        color: #f0f2f6;
        font-weight: 600;
    }
    
    /* Code Input Area */
    .stTextArea textarea {
        background-color: #1e1e1e;
        color: #d4d4d4;
        font-family: 'JetBrains Mono', monospace;
        border: 1px solid #333;
        border-radius: 8px;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        background-color: #262730;
        border: 1px solid #4facfe;
        color: #4facfe;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4facfe;
        color: white;
        box-shadow: 0 0 15px rgba(79, 172, 254, 0.4);
    }
    
    /* Cards */
    .error-card {
        background: #2d1b1b;
        border-left: 4px solid #ff4b4b;
        padding: 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        color: #ffcccc;
    }
    
    .explanation-card {
        background: #1b262c;
        border-top: 4px solid #00d2d3;
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
        color: #e1e1e1;
    }
    
    /* Security Warning */
    .security-box {
        background: rgba(255, 75, 75, 0.15);
        color: #ff4b4b;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        font-weight: 600;
        border: 1px solid #ff4b4b;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #171b21;
        border-right: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
col_head1, col_head2 = st.columns([1, 6])
with col_head1:
    st.image("https://cdn-icons-png.flaticon.com/512/9062/9062564.png", width=70) # Dark mode friendly icon
with col_head2:
    st.title("CompilerAI")
    st.markdown("### 🌙 Intelligent Error Analysis - Dark Mode")

st.markdown("---")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Settings")
    use_simulation = st.checkbox(
        "Simulation Mode", 
        value=True, 
        help="Use intelligent simulation if GCC is not available."
    )
    security_check = st.checkbox(
        "🛡 Security Guard", 
        value=True, 
        help="Scan code for vulnerabilities and unsafe functions."
    )
    
    st.write("---")
    st.markdown("### 📊 Stats")
    st.caption("Powered by: **Transformer NLP & Static Analysis**")

# Main Content Layout
input_col, output_col = st.columns([1, 1], gap="medium")

with input_col:
    st.subheader("💻 Code Editor")
    code_input = st.text_area(
        "Write your C/C++ code here",
        height=500,
        label_visibility="collapsed",
        placeholder="// Type your C code here...\n#include <stdio.h>\n\nint main() {\n    return 0;\n}"
    )
    
    if st.button("🚀 Analyze & Explain", type="primary"):
        with st.spinner("Compiling and thinking..."):
            # Initialize System
            config = SystemConfig(
                use_simulation=use_simulation, # Pass UI flag to config
                security_check_enabled=security_check,
                verbose=True
            )
            system = CompilerErrorExplainerSystem(config)
            
            # Temporary file handling
            # Detect language to choose extension
            is_cpp = "#include" in code_input and ("iostream" in code_input or "using namespace" in code_input)
            ext = ".cpp" if is_cpp else ".c"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as tmp:
                tmp.write(code_input)
                tmp_path = tmp.name
            
            try:
                # We no longer pass simulated_output string manually, 
                # main_system will generate it dynamically if config.use_simulation is True
                results = system.process_file(tmp_path)
                
                # Store results in session state to persist after rerun (if any)
                st.session_state['results'] = results
                st.session_state['analyzed'] = True
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

with output_col:
    st.subheader("🧠 AI Tutor Feedback")
    
    if st.session_state.get('analyzed'):
        results = st.session_state.get('results')
        
        if not results:
            st.success("🎉 compiles successfully! Great job!")
            st.balloons()
        else:
            for i, res in enumerate(results, 1):
                error = res.error
                expl = res.explanation
                
                # --- Visualization ---
                st.markdown(f"""
                <div class="error-card">
                    <h4>❌ Error detected at Line {error.location.line}</h4>
                    <code>{error.message}</code>
                </div>
                """, unsafe_allow_html=True)
                
                # --- Explanation ---
                with st.expander(f"📖 Read Explanation: {expl.title}", expanded=True):
                    st.markdown(f"""
                    <div class="explanation-card">
                        <h3>{expl.title}</h3>
                        <p>{expl.description}</p>
                        
                        <h4>🔍 Why did this happen?</h4>
                        <p>{expl.root_cause}</p>
                        
                        <h4>🛠 How to fix it:</h4>
                        <div style="background: #f1f2f6; padding: 10px; border-radius: 5px; font-family: monospace;">
                            {expl.fix_suggestion}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if expl.example:
                         st.markdown("#### 💡 Correct Example:")
                         st.markdown(expl.example)
                         
                    if expl.analogy:
                        st.info(f"🤔 **Analogy:** {expl.analogy}")
                    
                    # Security Warning
                    if expl.security_note:
                        st.markdown(f"""
                        <div class="security-box">
                            <span>⚠️ SECURITY ALERT:</span>
                            {expl.security_note}
                        </div>
                        """, unsafe_allow_html=True)
                        
                    st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("👈 Click **Analyze** to see explanations here.")


if not st.session_state.get('first_run'):
    st.session_state.first_run = True
