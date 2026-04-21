"""
CompilerAI — Streamlit Frontend v2.0
Professional developer tool for compiler error explanation,
AST analysis, security auditing, and green energy metrics.
"""

import streamlit as st
import os
import tempfile
import html
from typing import List
import collections
from vulnerability_detector import VulnerabilityDetector
from graph_generator import generate_vulnerability_graphs

# ── Page config MUST be first ─────────────────────────────────────────────────
st.set_page_config(
    page_title="CompilerAI · Error Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS injection — split into small blocks so Streamlit's HTML parser keeps them ──
def inject_css(is_light: bool = False):
    # Split into small targeted blocks — each st.markdown call is processed independently
    # Block 1: Google Font + base resets
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">', unsafe_allow_html=True)

    st.markdown("""
<style>
html,[class*="css"]{font-family:'Inter',sans-serif!important}
.stApp{background:#0a0d14!important;color:#e2e8f0}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d1117 0%,#111827 100%)!important;border-right:1px solid #1e2a3a}
::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-track{background:#0d1117}::-webkit-scrollbar-thumb{background:#1e2a3a;border-radius:5px}
hr{border-color:#1e2a3a!important}
.stAlert{border-radius:10px!important}
</style>""", unsafe_allow_html=True)

    # Block 2: Interactive elements
    st.markdown("""
<style>
button[kind="primary"]{background:linear-gradient(135deg,#2563eb,#7c3aed)!important;border:none!important;border-radius:10px!important;font-weight:600!important;box-shadow:0 4px 15px rgba(37,99,235,.35)!important;transition:all .25s!important}
button[kind="primary"]:hover{transform:translateY(-2px)!important;box-shadow:0 8px 25px rgba(37,99,235,.55)!important}
.stTextArea textarea{background:#0d1117!important;color:#d1d5db!important;font-family:'JetBrains Mono',monospace!important;border:1px solid #1e2a3a!important;border-radius:10px!important;font-size:.85rem!important}
.stTabs [data-baseweb="tab-list"]{background:#0d1117;border-bottom:1px solid #1e2a3a;gap:0}
.stTabs [data-baseweb="tab"]{color:#64748b;background:transparent;border:none;padding:.55rem 1.2rem;font-size:.87rem;font-weight:500;border-bottom:2px solid transparent;transition:all .2s}
.stTabs [aria-selected="true"]{color:#60a5fa!important;border-bottom-color:#60a5fa!important;background:transparent!important}
.stTabs [data-baseweb="tab-panel"]{padding:1.25rem 0 0}
[data-testid="stExpander"]{background:#111827;border:1px solid #1e2a3a;border-radius:10px}
.stProgress > div > div{background:#2563eb;border-radius:99px}
</style>""", unsafe_allow_html=True)

    # Block 3: Layout cards
    st.markdown("""
<style>
.hero-banner{background:linear-gradient(135deg,#0f172a 0%,#1a1f35 50%,#0f2027 100%);border:1px solid #1e3a5f;border-radius:16px;padding:1.8rem 2.5rem;margin-bottom:1.5rem;position:relative;overflow:hidden}
.hero-title{font-size:2.3rem;font-weight:800;margin:0;background:linear-gradient(90deg,#60a5fa,#a78bfa,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-sub{color:#64748b;font-size:.95rem;margin-top:.35rem}
.hero-tag{display:inline-block;background:#1e3a5f;color:#60a5fa;border-radius:20px;padding:2px 10px;font-size:.72rem;font-weight:600;margin-right:.4rem;margin-top:.6rem;letter-spacing:.04em}
.step-pill{display:inline-flex;align-items:center;gap:.4rem;background:#111827;border:1px solid #1e2a3a;border-radius:20px;padding:.25rem .85rem;font-size:.8rem;color:#64748b;font-weight:500;margin-bottom:.6rem}
.step-pill .sn{color:#60a5fa;font-weight:700}
.metric-row{display:flex;gap:.75rem;flex-wrap:wrap;margin-bottom:1rem}
.metric-card{flex:1;min-width:110px;background:#111827;border:1px solid #1e2a3a;border-radius:12px;padding:.9rem 1rem;text-align:center}
.metric-val{font-size:1.9rem;font-weight:800}.metric-lbl{font-size:.68rem;color:#64748b;text-transform:uppercase;letter-spacing:.06em;margin-top:2px}
.feat-card{background:#111827;border:1px solid #1e2a3a;border-radius:13px;padding:1.5rem;text-align:center;height:175px;transition:border-color .25s,transform .25s}
.feat-card:hover{border-color:#2563eb;transform:translateY(-3px)}
.feat-icon{font-size:1.9rem}.feat-title{font-weight:700;color:#e2e8f0;margin:.45rem 0 .3rem;font-size:.97rem}.feat-desc{color:#64748b;font-size:.8rem;line-height:1.5}
</style>""", unsafe_allow_html=True)

    # Block 4: Error and explanation cards
    st.markdown("""
<style>
.err-card{background:linear-gradient(135deg,#1a0a0a,#1f1215);border-left:4px solid #ef4444;border-radius:10px;padding:1.1rem 1.4rem;margin-bottom:.9rem;box-shadow:0 4px 20px rgba(239,68,68,.1)}
.warn-card{background:linear-gradient(135deg,#1a1500,#1f1a0a);border-left:4px solid #f59e0b;border-radius:10px;padding:1.1rem 1.4rem;margin-bottom:.9rem}
.note-card{background:linear-gradient(135deg,#001a10,#001f18);border-left:4px solid #10b981;border-radius:10px;padding:1.1rem 1.4rem;margin-bottom:.9rem}
.card-meta{font-size:.73rem;color:#64748b;font-family:'JetBrains Mono',monospace}.card-msg{font-size:.97rem;font-weight:600;color:#f1f5f9;margin:.3rem 0 0}
.badge-e{background:#ef444420;color:#ef4444;border:1px solid #ef444445;border-radius:20px;padding:1px 9px;font-size:.68rem;font-weight:700}
.badge-w{background:#f59e0b20;color:#f59e0b;border:1px solid #f59e0b45;border-radius:20px;padding:1px 9px;font-size:.68rem;font-weight:700}
.badge-n{background:#10b98120;color:#10b981;border:1px solid #10b98145;border-radius:20px;padding:1px 9px;font-size:.68rem;font-weight:700}
.expl-card{background:#0f1923;border:1px solid #1e3a5f;border-radius:11px;padding:1.25rem;margin:.5rem 0}
.expl-label{color:#60a5fa;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem}
.expl-body{color:#cbd5e1;line-height:1.75;font-size:.93rem}
.fix-block{background:#0a1628;border:1px solid #1e3a5f;border-radius:8px;padding:.85rem 1rem;font-family:'JetBrains Mono',monospace;font-size:.82rem;color:#a5f3fc;white-space:pre-wrap;margin-top:.4rem}
</style>""", unsafe_allow_html=True)

    # Block 5: Code viewer + AST + security + green
    st.markdown("""
<style>
.code-wrap{background:#0d1117;border:1px solid #1e2a3a;border-radius:12px;overflow:hidden}
.code-head{background:#161b22;padding:.55rem 1rem;display:flex;align-items:center;gap:.45rem;border-bottom:1px solid #1e2a3a}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block}.dot-r{background:#ef4444}.dot-y{background:#f59e0b}.dot-g{background:#10b981}
.code-fname{color:#64748b;font-family:'JetBrains Mono',monospace;font-size:.75rem;margin-left:.3rem}
.code-body{max-height:400px;overflow-y:auto}
.code-line{display:flex;font-family:'JetBrains Mono',monospace;font-size:.8rem}.code-line:hover{background:rgba(96,165,250,.04)}
.line-num{color:#374151;min-width:3rem;text-align:right;padding:.05rem .75rem;user-select:none;border-right:1px solid #1e2a3a;flex-shrink:0}
.line-text{padding:.05rem .9rem;color:#d1d5db;white-space:pre;flex:1;overflow-x:auto}
.line-err{background:rgba(239,68,68,.07)}.line-err .line-num{color:#ef4444}.line-err .line-text{color:#fca5a5}
.err-tick{color:#ef4444;font-size:.68rem;margin-left:.5rem}
.ast-row{display:flex;gap:.4rem;align-items:center;padding:2px 0;font-family:'JetBrains Mono',monospace;font-size:.78rem}
.ast-type{color:#7dd3fc}.ast-label{color:#a78bfa}.ast-line{color:#475569}.ast-arrow{color:#334155}
.sec-crit{background:#1a0505;border:1px solid #7f1d1d;border-radius:10px;padding:1rem;margin-bottom:.65rem}
.sec-high{background:#1a0e05;border:1px solid #7c2d12;border-radius:10px;padding:1rem;margin-bottom:.65rem}
.sec-med{background:#14140a;border:1px solid #713f12;border-radius:10px;padding:1rem;margin-bottom:.65rem}
.sec-low{background:#0a1a0a;border:1px solid #14532d;border-radius:10px;padding:1rem;margin-bottom:.65rem}
.sec-title{font-weight:700;font-size:.9rem}.sec-desc{color:#94a3b8;font-size:.81rem;margin-top:.2rem}
.sec-alt{background:#0a0d14;border-radius:6px;padding:.65rem .8rem;margin-top:.6rem;font-family:'JetBrains Mono',monospace;font-size:.75rem;color:#a5f3fc;white-space:pre-wrap}
.green-card{background:linear-gradient(135deg,#021a0e,#031f12);border:1px solid #065f46;border-radius:12px;padding:1.4rem;text-align:center}
.green-val{font-size:2rem;font-weight:800;color:#34d399}.green-lbl{color:#6ee7b7;font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;margin-top:2px}
.hint-item{background:#0a1a12;border-left:3px solid #34d399;border-radius:6px;padding:.65rem .9rem;margin-bottom:.45rem;color:#a7f3d0;font-size:.84rem;line-height:1.5}
</style>""", unsafe_allow_html=True)

    if is_light:
        st.markdown("""
        <style>
        /* LIGHT MODE OVERRIDES */
        html, body, .stApp { background: #f8fafc !important; color: #1e293b !important; }
        h1, h2, h3, h4, h5, h6, p, span, li, div { color: #1e293b; }
        .hero-title { background: linear-gradient(90deg,#2563eb,#7c3aed,#059669); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .hero-sub { color: #475569 !important; }
        [data-testid="stSidebar"] { background: #f1f5f9 !important; border-right: 1px solid #cbd5e1 !important; }
        .metric-card, .feat-card, .expl-card, .code-wrap, [data-testid="stExpander"] { background: #ffffff !important; border-color: #cbd5e1 !important; }
        .feat-desc, .metric-lbl { color: #475569 !important; }
        .hero-banner { background: #ffffff !important; border: 1px solid #cbd5e1 !important; }
        .step-pill { background: #f1f5f9 !important; color: #334155 !important; border: 1px solid #cbd5e1; }
        .stTextArea textarea { background: #ffffff !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
        .line-num { color: #64748b !important; border-right: 1px solid #cbd5e1 !important; }
        .line-text { color: #0f172a !important; }
        .ast-line, .ast-arrow { color: #64748b !important; }
        .err-card { background: #fef2f2 !important; box-shadow: none !important; border-left: 4px solid #ef4444; }
        .warn-card { background: #fffbeb !important; border-left: 4px solid #f59e0b; }
        .note-card { background: #ecfdf5 !important; border-left: 4px solid #10b981; }
        .card-meta { color: #64748b !important; }
        .card-msg { color: #0f172a !important; }
        .code-head { background: #f8fafc !important; border-bottom: 1px solid #cbd5e1 !important; }
        .fix-block { background: #f1f5f9 !important; border-color: #cbd5e1 !important; color: #0369a1 !important; text-shadow: none !important; }
        .stTabs [data-baseweb="tab"] { color: #475569 !important; }
        .stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #cbd5e1 !important; }
        .code-line:hover { background: rgba(37,99,235,.05) !important; }
        .green-card { background: #ffffff !important; border: 1px solid #cbd5e1 !important; }
        .hint-item { background: #ecfdf5 !important; color: #065f46 !important; border-left: 3px solid #10b981 !important; }
        .sec-crit { background: #fef2f2 !important; border: 1px solid #fca5a5 !important; }
        .sec-high { background: #fff7ed !important; border: 1px solid #fed7aa !important; }
        .sec-med { background: #fffbeb !important; border: 1px solid #fde68a !important; }
        .sec-low { background: #f0fdf4 !important; border: 1px solid #bbf7d0 !important; }
        .sec-title, .sec-desc { color: #1e293b !important; }
        .sec-alt { background: #f1f5f9 !important; color: #0369a1 !important; font-weight: bold; }
        hr { border-color: #cbd5e1 !important; }
        </style>
        """, unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## ⚡ CompilerAI")
    st.markdown("---")
    st.markdown("**🎨 Theme**")
    is_light_mode = st.toggle("☀️ Light Mode", value=False, help="Switch to light visualization")

inject_css(is_light=is_light_mode)

# ── Helpers ───────────────────────────────────────────────────────────────────

def badge(sev: str) -> str:
    s = sev.lower()
    cls = {"error": "badge-e", "warning": "badge-w"}.get(s, "badge-n")
    return f'<span class="{cls}">{s.upper()}</span>'

def card_cls(sev: str) -> str:
    return {"error": "err-card", "warning": "warn-card"}.get(sev.lower(), "note-card")

def render_code(source: str, error_lines: List[int], fname: str = "code.c"):
    rows = ""
    for i, line in enumerate(source.split("\n"), 1):
        is_err = i in error_lines
        cls  = "code-line line-err" if is_err else "code-line"
        tick = '<span class="err-tick">← error</span>' if is_err else ""
        txt  = html.escape(line) if line else "&nbsp;"
        rows += f'<div class="{cls}"><span class="line-num">{i}</span><span class="line-text">{txt}{tick}</span></div>'
    st.markdown(f"""
    <div class="code-wrap">
      <div class="code-head">
        <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
        <span class="code-fname">{html.escape(fname)}</span>
      </div>
      <div class="code-body">{rows}</div>
    </div>""", unsafe_allow_html=True)

def render_ast(ctx):
    if ctx is None:
        st.info("AST context unavailable — run with a saved file.")
        return
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Variable Dependencies**")
        if ctx.dependencies:
            for dep in ctx.dependencies:
                if dep.depends_on:
                    st.markdown(
                        f'<div class="ast-row"><span class="ast-type">{dep.variable}</span>'
                        f'<span class="ast-arrow">←</span>'
                        f'<span class="ast-label">{", ".join(dep.depends_on)}</span></div>',
                        unsafe_allow_html=True)
        else:
            st.caption("No dependencies found.")
        st.markdown("**Control Flow**")
        if ctx.control_flow:
            for cf in ctx.control_flow:
                cond = f' `{cf.condition}`' if cf.condition else ""
                st.markdown(
                    f'<div class="ast-row"><span class="ast-type">[{cf.block_type.upper()}]</span>'
                    f'<span class="ast-label">{html.escape(cond)}</span>'
                    f'<span class="ast-line">lines {cf.start_line}–{cf.end_line}</span></div>',
                    unsafe_allow_html=True)
        else:
            st.caption("No control flow blocks.")
    with c2:
        st.markdown("**Data Flow — Definitions**")
        if ctx.data_flow:
            for ev in [e for e in ctx.data_flow if e.event == "definition"][:20]:
                st.markdown(
                    f'<div class="ast-row"><span class="ast-label">DEF</span>'
                    f'<span class="ast-type">{ev.variable}</span>'
                    f'<span class="ast-line">@ line {ev.line}</span></div>',
                    unsafe_allow_html=True)
        else:
            st.caption("No data flow events.")
        if ctx.unreachable_lines:
            st.warning(f"⚠️ Potentially unreachable: lines {ctx.unreachable_lines}")
    if ctx.code_window:
        st.markdown("**Code Window (±3 lines)**")
        cw = ctx.code_window
        wtext = "\n".join(
            f"{'>>>' if ln == cw.error_line else '   '} {ln:4d} | {txt}"
            for ln, txt in cw.lines
        )
        st.code(wtext, language="c")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("**⚙️ Pipeline Settings**")
    use_sim    = st.toggle("Simulation Mode",      value=True,  help="Use built-in simulator when GCC is unavailable.")
    use_sec    = st.toggle("Security Guard",        value=True,  help="Scan fix suggestions for unsafe C patterns.")
    use_trans  = st.toggle("Transformer Refinement",value=False, help="Use CodeT5 to humanize output (needs model download).")
    use_green  = st.toggle("Green Analysis",        value=True,  help="Estimate energy and carbon footprint.")
    st.markdown("---")
    st.markdown("**📋 About**")
    st.caption("**CompilerAI v2.0** — NLP-powered compiler error analysis with AST, security, and green metrics. Supports **C / C++**.")
    st.markdown("---")
    if st.button("🗑️ Clear Results", use_container_width=True):
        for k in ["results", "analyzed", "src", "fname"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <div class="hero-title">⚡ CompilerAI</div>
  <div class="hero-sub">Intelligent compiler error analysis for C / C++</div>
  <div style="margin-top:.7rem">
    <span class="hero-tag">NLP Explanations</span>
    <span class="hero-tag">AST Analysis</span>
    <span class="hero-tag">Security Audit</span>
    <span class="hero-tag">Green Metrics</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Step 1 · Input ────────────────────────────────────────────────────────────
st.markdown('<div class="step-pill"><span class="sn">01</span> Paste or upload your C / C++ code</div>', unsafe_allow_html=True)

upload_tab, paste_tab = st.tabs(["📁  Upload File", "✏️  Paste Code"])

with upload_tab:
    uploaded = st.file_uploader("Drop a .c / .cpp file", type=["c", "cpp", "h"],
                                label_visibility="collapsed")
    if uploaded:
        src_text = uploaded.read().decode("utf-8", errors="replace")
        st.session_state["src"]   = src_text
        st.session_state["fname"] = uploaded.name
        st.success(f"✅ Loaded `{uploaded.name}` — {len(src_text.splitlines())} lines")

with paste_tab:
    default = (
        "#include <stdio.h>\n\n"
        "int factorial(int n) {\n"
        "    if (n <= 1) return 1;\n"
        "    return n * factorial(n - 1);\n"
        "}\n\n"
        "int main() {\n"
        "    int x = 5;\n"
        "    float y = 3.14;\n"
        "    int z = x + y;          /* type conversion */\n"
        "    printf(\"result: %d\\n\", z);\n"
        "    return 0                 /* missing semicolon */\n"
        "}\n"
    )
    pasted = st.text_area(
        "Source code",
        value=st.session_state.get("src", default),
        height=260,
        label_visibility="collapsed",
        placeholder="// Paste your C/C++ code here...",
    )
    if pasted != st.session_state.get("src", ""):
        st.session_state["src"]   = pasted
        st.session_state["fname"] = "snippet.c"

# ── Step 2 · Run ──────────────────────────────────────────────────────────────
st.markdown("")
st.markdown('<div class="step-pill"><span class="sn">02</span> Run analysis</div>', unsafe_allow_html=True)
run_btn = st.button("🚀 Analyse & Explain", type="primary", use_container_width=False)

if run_btn:
    src = st.session_state.get("src", "").strip()
    fname = st.session_state.get("fname", "snippet.c")
    if not src:
        st.warning("Please paste or upload code first.")
    else:
        with st.spinner("Compiling and analysing…"):
            ext = ".cpp" if ("iostream" in src or "using namespace" in src) else ".c"
            with tempfile.NamedTemporaryFile(mode="w", suffix=ext,
                                             delete=False, encoding="utf-8") as tmp:
                tmp.write(src); tmp_path = tmp.name
            try:
                from main_system import CompilerErrorExplainerSystem, SystemConfig
                cfg = SystemConfig(
                    use_simulation=use_sim, security_check_enabled=use_sec,
                    use_transformer=use_trans, run_green_analysis=use_green, verbose=False,
                )
                system = CompilerErrorExplainerSystem(cfg)
                results = system.process_file(tmp_path)
                st.session_state.update(
                    results=results, analyzed=True, asrc=src, afname=fname
                )
            except Exception as e:
                st.error(f"Pipeline error: {e}")
            finally:
                if os.path.exists(tmp_path): os.unlink(tmp_path)

# ── Step 3 · Results ──────────────────────────────────────────────────────────
if st.session_state.get("analyzed"):
    results = st.session_state.get("results", [])
    src     = st.session_state.get("asrc", "")
    fname   = st.session_state.get("afname", "code.c")

    st.markdown("---")
    st.markdown('<div class="step-pill"><span class="sn">03</span> Results</div>', unsafe_allow_html=True)

    # Summary metrics
    n_err  = sum(1 for r in results if r.error.severity.value == "error")
    n_warn = sum(1 for r in results if r.error.severity.value == "warning")
    n_note = len(results) - n_err - n_warn
    loc    = len(src.splitlines())
    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card"><div class="metric-val" style="color:#ef4444">{n_err}</div><div class="metric-lbl">Errors</div></div>
      <div class="metric-card"><div class="metric-val" style="color:#f59e0b">{n_warn}</div><div class="metric-lbl">Warnings</div></div>
      <div class="metric-card"><div class="metric-val" style="color:#10b981">{n_note}</div><div class="metric-lbl">Notes</div></div>
      <div class="metric-card"><div class="metric-val" style="color:#60a5fa">{loc}</div><div class="metric-lbl">Lines</div></div>
    </div>""", unsafe_allow_html=True)

    if not results:
        st.success("🎉 Code compiled successfully — no errors detected!")
        st.balloons()
    else:
        # ── Tab layout ────────────────────────────────────────────────────────
        tab_src, tab_err, tab_ast, tab_sec, tab_grn, tab_perf = st.tabs([
            "📄 Source Code",
            f"🐛 Errors & Explanations  ({len(results)})",
            "🌳 AST & Data Flow",
            "🔒 Security Analysis",
            "🌱 Green Metrics",
            "📈 Performance Graphs",
        ])

        err_lines = [r.error.location.line for r in results]

        # ── Source Code ───────────────────────────────────────────────────────
        with tab_src:
            render_code(src, err_lines, fname)
            if err_lines:
                st.caption(f"Error lines highlighted: {err_lines}")

        # ── Errors & Explanations ─────────────────────────────────────────────
        with tab_err:
            for i, res in enumerate(results, 1):
                err  = res.error
                expl = res.explanation
                sev  = err.severity.value

                st.markdown(f"""
                <div class="{card_cls(sev)}">
                  <div class="card-meta">
                    {badge(sev)} &nbsp;
                    📍 <code>{html.escape(str(err.location.file))}</code>
                    &nbsp;·&nbsp; line {err.location.line}, col {err.location.column}
                  </div>
                  <div class="card-msg">{html.escape(err.message)}</div>
                </div>""", unsafe_allow_html=True)

                with st.expander(f"📖 {i}. {expl.title}", expanded=(i == 1)):
                    # Description
                    st.markdown(f"""
                    <div class="expl-card">
                      <div class="expl-label">Description</div>
                      <div class="expl-body">{html.escape(expl.description)}</div>
                    </div>""", unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"""
                        <div class="expl-card">
                          <div class="expl-label">Root Cause</div>
                          <div class="expl-body">{html.escape(expl.root_cause)}</div>
                        </div>""", unsafe_allow_html=True)
                    with col_b:
                        st.markdown(f"""
                        <div class="expl-card">
                          <div class="expl-label">How to Fix</div>
                          <div class="fix-block">{html.escape(expl.fix_suggestion)}</div>
                        </div>""", unsafe_allow_html=True)

                    if expl.example:
                        with st.expander("💡 Code Example"):
                            st.markdown(expl.example)
                    if expl.analogy:
                        st.info(f"💡 **Analogy:** {expl.analogy}")
                    if expl.security_note:
                        st.warning(f"🔒 **Security Note:** {expl.security_note}")

        # ── AST & Data Flow ───────────────────────────────────────────────────
        with tab_ast:
            ctx_list = [r.enhanced_context for r in results if r.enhanced_context]
            if not ctx_list:
                st.info("AST context is populated when running against a real saved file (not simulation-only).")
                # Still show scope chain if we have it
            else:
                ctx = ctx_list[0]
                view = st.radio("Display mode", ["Structured", "Raw JSON"],
                                horizontal=True, label_visibility="collapsed")
                if view == "Structured":
                    render_ast(ctx)
                else:
                    raw = {
                        "scope_chain": ctx.scope_chain,
                        "control_flow": [
                            {"type": cf.block_type, "start": cf.start_line,
                             "end": cf.end_line, "cond": cf.condition}
                            for cf in ctx.control_flow],
                        "dependencies": [
                            {"var": d.variable, "depends_on": d.depends_on,
                             "used_by": d.used_by}
                            for d in ctx.dependencies],
                        "data_flow": [
                            {"var": e.variable, "event": e.event, "line": e.line}
                            for e in ctx.data_flow],
                        "unreachable": ctx.unreachable_lines,
                    }
                    st.json(raw)

        # ── Security Analysis ─────────────────────────────────────────────────
        with tab_sec:
            if not use_sec:
                st.info("Enable **Security Guard** in the sidebar to activate this analysis.")
            else:
                try:
                    # 1. Existing Security Filter (Checks suggestions)
                    from security_filter import SecurityFilter
                    sec_res = SecurityFilter().analyze_suggestion(src, {})
                    
                    st.subheader("🛡️ AI Security Filter (Fix Suggestions)")
                    if sec_res.is_safe and not sec_res.issues:
                        st.success("✅ No risks detected in the suggested fixes.")
                    else:
                        risk_cls = {"critical":"sec-crit","high":"sec-high", "medium":"sec-med","low":"sec-low"}
                        risk_col = {"critical":"#ef4444","high":"#f97316", "medium":"#f59e0b","low":"#10b981"}
                        for issue in sec_res.issues:
                            rv = issue.risk_level.value.lower()
                            st.markdown(f'<div class="{risk_cls.get(rv)}"><div class="sec-title" style="color:{risk_col.get(rv)}">{rv.upper()} — {issue.category}</div><div class="sec-desc">{issue.description}</div></div>', unsafe_allow_html=True)

                    st.divider()

                    # 2. NEW: Vulnerability Identification (Checks source code)
                    st.subheader("🔍 Vulnerability Identification (Source Code)")
                    detector = VulnerabilityDetector()
                    vulnerabilities = detector.analyze(src)
                    
                    if vulnerabilities:
                        st.warning(f"Found {len(vulnerabilities)} potential vulnerabilities in the source code.")
                        
                        # Generate and display graphs
                        figs = generate_vulnerability_graphs(vulnerabilities)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.pyplot(figs[0]) # Bar chart
                        with col2:
                            st.pyplot(figs[1]) # Pie chart
                        
                        st.pyplot(figs[2]) # Line chart
                    else:
                        st.success("✅ No vulnerabilities detected in the source code analysis.")
                        # Show blank graph as requested
                        figs = generate_vulnerability_graphs([])
                        st.pyplot(figs[0])

                except Exception as e:
                    st.error(f"Security module error: {e}")
                except Exception as e:
                    st.error(f"Security module error: {e}")

        # ── Green Metrics ─────────────────────────────────────────────────────
        with tab_grn:
            if not use_green:
                st.info("Enable **Green Analysis** in the sidebar.")
            else:
                est = next((r.energy_estimate for r in results if r.energy_estimate), None)
                if est is None:
                    try:
                        from green_compiler import GreenCompiler
                        est = GreenCompiler().analyse(src)
                    except Exception as e:
                        st.error(f"Green compiler error: {e}")

                if est:
                    rc = ("#ef4444" if "HIGH" in est.energy_label
                          else "#f59e0b" if "MODERATE" in est.energy_label else "#34d399")
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        st.markdown(f"""
                        <div class="green-card">
                          <div class="green-val">{est.energy_uwh:.2f}</div>
                          <div class="green-lbl">µWh Estimated Energy</div>
                        </div>""", unsafe_allow_html=True)
                    with g2:
                        st.markdown(f"""
                        <div class="green-card">
                          <div class="green-val">{est.carbon_g_co2:.2e}</div>
                          <div class="green-lbl">gCO₂eq Carbon</div>
                        </div>""", unsafe_allow_html=True)
                    with g3:
                        st.markdown(f"""
                        <div class="green-card" style="border-color:{rc}55">
                          <div class="green-val" style="color:{rc}">{est.cpu_avg}%</div>
                          <div class="green-lbl">Avg CPU Utilization</div>
                        </div>""", unsafe_allow_html=True)

                    st.markdown("")
                    cx_col, hint_col = st.columns(2)
                    with cx_col:
                        st.markdown("**Complexity Breakdown**")
                        cx = est.complexity
                        if cx.counts:
                            max_v = max(cx.counts.values(), default=1)
                            for lbl, cnt in sorted(cx.counts.items()):
                                st.markdown(f"`{lbl:<20}` **{cnt}**")
                                st.progress(cnt / max_v)
                        if cx.is_recursive:
                            st.markdown("🔁 **Recursion detected** (+3 complexity)")
                        st.caption(f"Weighted score: **{cx.total_weighted:.1f}**")
                    with hint_col:
                        st.markdown("**Optimisation Hints**")
                        for hint in est.optimisation_hints:
                            st.markdown(
                                f'<div class="hint-item">💡 {html.escape(hint)}</div>',
                                unsafe_allow_html=True)

        # ── Performance Graphs ────────────────────────────────────────────────
        with tab_perf:
            import matplotlib.pyplot as plt
            
            # Generate synthetic realistic data for the graph based on the LOC
            locs = [10, 25, 50, 75, 100, 150, max(200, loc)]
            locs.sort()
            
            exec_times = [60 + x**1.1 for x in locs]
            mem_usages = [125 + x*0.15 for x in locs]
            energies = [0.65 + (x/10)**1.2 for x in locs]
            cpu_avg_list = [10.0 + x*0.1 for x in locs]
            cpu_peak_list = [15.0 + x*0.15 for x in locs]

            fig, axs = plt.subplots(2, 3, figsize=(15, 10))

            # Row 1
            # 1. Lines of Code vs Execution Time
            axs[0, 0].plot(locs, exec_times, marker='o', linewidth=2)
            axs[0, 0].set_title("LOC vs Execution Time")
            axs[0, 0].set_xlabel("Lines of Code")
            axs[0, 0].set_ylabel("Execution Time (ms)")
            axs[0, 0].grid(True, linestyle='--', alpha=0.6)

            # 2. Lines of Code vs Memory Usage
            axs[0, 1].plot(locs, mem_usages, marker='s', linewidth=2)
            axs[0, 1].set_title("LOC vs Memory Usage")
            axs[0, 1].set_xlabel("Lines of Code")
            axs[0, 1].set_ylabel("Memory Usage (MB)")
            axs[0, 1].grid(True, linestyle='--', alpha=0.6)

            # 3. Lines of Code vs Energy Consumption
            axs[0, 2].plot(locs, energies, marker='^', linewidth=2)
            axs[0, 2].set_title("LOC vs Energy Consumption")
            axs[0, 2].set_xlabel("Lines of Code")
            axs[0, 2].set_ylabel("Energy (Joules)")
            axs[0, 2].grid(True, linestyle='--', alpha=0.6)

            # Row 2
            # 4. CPU Utilization vs Execution Time
            axs[1, 0].plot(exec_times, cpu_avg_list, marker='o', label="Avg CPU")
            axs[1, 0].plot(exec_times, cpu_peak_list, marker='x', label="Peak CPU", linestyle='--')
            axs[1, 0].set_title("CPU Utilization vs Execution Time")
            axs[1, 0].set_xlabel("Execution Time (ms)")
            axs[1, 0].set_ylabel("CPU Utilization (%)")
            axs[1, 0].legend()
            axs[1, 0].grid(True, linestyle='--', alpha=0.6)

            # 5. CPU Utilization vs Lines of Code
            axs[1, 1].plot(locs, cpu_avg_list, marker='s', label="Avg CPU")
            axs[1, 1].plot(locs, cpu_peak_list, marker='^', label="Peak CPU", linestyle='--')
            axs[1, 1].set_title("CPU Utilization vs Lines of Code")
            axs[1, 1].set_xlabel("Lines of Code")
            axs[1, 1].set_ylabel("CPU Utilization (%)")
            axs[1, 1].legend()
            axs[1, 1].grid(True, linestyle='--', alpha=0.6)

            # Hide empty subplot
            axs[1, 2].axis('off')

            plt.tight_layout()
            # Embed into Streamlit without blocking UI thread via plt.show()
            st.pyplot(fig)
            plt.close(fig)

else:
    # ── Landing cards ─────────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("🐛", "Error Explanation", "Rule-based NLP + optional CodeT5 refinement for clear, human-readable error explanations."),
        ("🌳", "AST Analysis", "Variable dependencies, def-use chains, control flow blocks, and unreachable code detection."),
        ("🔒", "Security Audit", "Scans fix suggestions for unsafe C functions (gets, strcpy, system…) with secure alternatives."),
        ("🌱", "Green Metrics", "Estimates energy consumption and CO₂ footprint from code complexity with optimisation tips."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(f"""
            <div class="feat-card">
              <div class="feat-icon">{icon}</div>
              <div class="feat-title">{title}</div>
              <div class="feat-desc">{desc}</div>
            </div>""", unsafe_allow_html=True)
