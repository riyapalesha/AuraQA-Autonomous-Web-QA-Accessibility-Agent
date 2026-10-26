import sys
import os

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import time
from core.agent import AuraQAAgent
from config import Config

st.set_page_config(
    page_title="AuraQA | Web QA & Accessibility Auditor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "url_input" not in st.session_state:
    st.session_state["url_input"] = "https://riya-palesha.vercel.app/"

# Custom Styling: Light Blue Accent & Translucent Download Buttons
st.markdown("""
<style>
    /* Clean, highly readable text */
    h1, h2, h3, h4 { color: #111827 !important; font-weight: 700; }
    p, span, label, div { color: #1f2937; }
    
    /* Match exact colors of Streamlit's st.info (Summary Evaluation box) */
    div[data-testid="stFormSubmitButton"] > button,
    button[data-testid="stBaseButton-primaryFormSubmit"],
    button[kind="primaryFormSubmit"],
    .stFormSubmitButton > button,
    div[data-testid="stDownloadButton"] > button,
    div[data-testid="stDownloadButton"] > button[kind="primary"],
    button[kind="primary"],
    button[data-testid="stBaseButton-primary"] {
        background-color: rgba(28, 131, 225, 0.12) !important; /* Exact st.info soft blue tint */
        border: 1px solid rgba(28, 131, 225, 0.35) !important;
        color: #0369a1 !important; /* Crisp oceanic text */
        font-weight: 700 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover,
    button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    .stFormSubmitButton > button:hover,
    div[data-testid="stDownloadButton"] > button:hover,
    button[kind="primary"]:hover {
        background-color: rgba(28, 131, 225, 0.25) !important; /* Slightly deeper on hover */
        border-color: rgba(28, 131, 225, 0.6) !important;
        color: #0c4a6e !important;
    }

    /* 3. Hide Sidebar Scrollbar & Push Content Upwards */
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 1.2rem !important;
        padding-bottom: 1rem !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
        overflow-y: hidden !important;
        overflow-x: hidden !important;
    }
    [data-testid="stSidebarHeader"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0px !important;
        height: auto !important;
    }
    [data-testid="stSidebar"] hr {
        margin-top: 12px !important;
        margin-bottom: 12px !important;
    }
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        margin-top: 0px !important;
        padding-top: 0px !important;
    }
    [data-testid="stSidebar"] {
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar, 
    [data-testid="stSidebarContent"]::-webkit-scrollbar {
        display: none !important;
        width: 0px !important;
        background: transparent !important;
    }

    /* Simple Metric Boxes */
    .metric-box {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value { font-size: 2rem; font-weight: 800; margin: 0; }
    .metric-title { font-size: 0.85rem; color: #4b5563; font-weight: 600; text-transform: uppercase; margin-top: 4px; }
    
    /* Clean Issue Cards */
    .issue-item {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .badge-p0 { background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .badge-p1 { background-color: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .badge-p2 { background-color: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Audit Controls")
    headful_mode = st.toggle("👁️ Show Browser Live (Headful)", value=False, help="Launch visible Chromium window on your screen to watch the audit in real-time.")
    
    st.divider()
    st.subheader("Demo Presets")
    st.caption("Click to load preset into audit input:")
    
    if st.button("👤 Riya Palesha Portfolio", use_container_width=True):
        st.session_state["url_input"] = "https://riya-palesha.vercel.app/"
        st.rerun()
        
    if st.button("📰 Hacker News (news.ycombinator.com)", use_container_width=True, help="Live site with missing SVG alt text, color contrast issues, and unlabeled inputs."):
        st.session_state["url_input"] = "https://news.ycombinator.com"
        st.rerun()
        
    if st.button("🛒 SauceDemo (saucedemo.com)", use_container_width=True, help="Industry-standard QA site with input label and contrast defects."):
        st.session_state["url_input"] = "https://www.saucedemo.com"
        st.rerun()
        
    st.divider()
    st.caption("Standards: WCAG 2.1 AA • Apple Human Interface Guidelines")

# Main Page
st.title("🔍 AuraQA: Web QA & Accessibility Auditor")
st.write("Audits live websites for accessibility violations (WCAG 2.1 AA), dead links, broken buttons, and usability defects.")

# Input Form
with st.form("audit_form"):
    col_url, col_submit = st.columns([4, 1])
    with col_url:
        target_url = st.text_input(
            "Website URL to Audit:",
            key="url_input",
            placeholder="https://example.com"
        )
    with col_submit:
        st.write("")  # Vertical alignment spacer
        st.write("")
        submit = st.form_submit_button("🚀 Run Audit", type="primary", use_container_width=True)

if submit and target_url:
    status_box = st.status("🔍 Running Audit...", expanded=True)
    with status_box:
        st.write("1. Launching browser & loading page...")
        st.write("2. Scanning full DOM tree with axe-core (WCAG 2.1 AA)...")
        st.write("3. Probing interactive elements, dead links, and buttons...")
        st.write("4. Evaluating findings and synthesizing code fixes...")
        
        agent = AuraQAAgent(headless=not headful_mode)
        try:
            result = agent.audit_url(target_url)
            status_box.update(label="✅ Audit Completed Successfully!", state="complete", expanded=False)
            st.session_state.audit_result = result
        except Exception as e:
            status_box.update(label="❌ Audit Failed", state="error", expanded=True)
            st.session_state.audit_result = None
            st.error(f"⚠️ {str(e)}")
            st.stop()

# Display Results
if "audit_result" in st.session_state:
    res = st.session_state.audit_result
    st.divider()
    
    st.subheader(f"Results for: {res.page_title}")
    st.caption(f"Scanned URL: {res.url} • Duration: {res.duration_seconds}s")

    # Metrics Summary Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        score_color = "#15803d" if res.a11y_score >= 80 else ("#b45309" if res.a11y_score >= 60 else "#b91c1c")
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-value" style="color: {score_color};">{res.a11y_score}/100</p>
            <p class="metric-title">Accessibility Score</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-value" style="color: #b91c1c;">{res.p0_count}</p>
            <p class="metric-title">Critical Blockers (P0)</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-value" style="color: #b45309;">{res.p1_count}</p>
            <p class="metric-title">Major Defects (P1)</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-value" style="color: #0284c7;">{res.total_issues}</p>
            <p class="metric-title">Total Issues Found</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.info(f"📋 **Summary Evaluation:** {res.hig_summary.splitlines()[0]}")

    # Tabs
    tab_issues, tab_screenshot, tab_report = st.tabs(["📋 Issues List & Fixes", "📸 Page Screenshot", "📄 Standalone Report"])

    with tab_issues:
        if res.issues:
            # Filter options
            severities = ["All Severities", "P0 - Critical", "P1 - Major", "P2 - Minor"]
            selected_sev = st.selectbox("Filter by Severity:", severities)

            filtered_issues = res.issues
            if selected_sev != "All Severities":
                filtered_issues = [i for i in res.issues if selected_sev in i.severity.value]

            st.write(f"Showing **{len(filtered_issues)}** issue(s):")

            for issue in filtered_issues:
                badge_class = "badge-p0" if "P0" in issue.severity.value else ("badge-p1" if "P1" in issue.severity.value else "badge-p2")
                
                with st.container():
                    st.markdown(f"""
                    <div class="issue-item">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span class="{badge_class}">{issue.severity.value}</span>
                            <small style="color:#6b7280; font-family:monospace;">{issue.id}</small>
                        </div>
                        <h4 style="margin: 4px 0 8px 0; color:#111827;">{issue.title}</h4>
                        <p style="margin: 0 0 8px 0; color:#374151; font-size:0.95rem;">{issue.description}</p>
                        <p style="margin: 0; color:#6b7280; font-size:0.85rem;"><strong>Impact:</strong> {issue.impact}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander(f"View Fix & Selector for {issue.id}"):
                        if issue.selector and issue.selector != "N/A":
                            st.text(f"Selector / Target: {issue.selector}")
                        if issue.html_snippet:
                            st.code(issue.html_snippet, language="html")
                        st.markdown("**Recommended Solution:**")
                        st.code(issue.recommended_fix, language="text")
        else:
            st.success("🎉 No issues detected! The page passed all audits.")

    with tab_screenshot:
        if res.screenshot_path and os.path.exists(res.screenshot_path):
            st.image(res.screenshot_path, caption=f"Full-page snapshot of {res.url}", use_container_width=True)
        else:
            st.write("No screenshot captured.")

    with tab_report:
        st.subheader("Export Audit Reports")
        st.write("Download the comprehensive audit results formatted for engineering reviews or compliance archives.")

        report_files_pdf = [f for f in os.listdir(Config.REPORTS_DIR) if f.endswith(".pdf")]
        report_files_html = [f for f in os.listdir(Config.REPORTS_DIR) if f.endswith(".html")]

        col_pdf, col_html = st.columns(2)
        with col_pdf:
            if report_files_pdf:
                latest_pdf = sorted(report_files_pdf)[-1]
                pdf_path = os.path.join(Config.REPORTS_DIR, latest_pdf)
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
                st.download_button(
                    "📄 Download PDF Report",
                    data=pdf_data,
                    file_name=latest_pdf,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                st.caption(f"File: `{latest_pdf}`")

        with col_html:
            if report_files_html:
                latest_html = sorted(report_files_html)[-1]
                html_path = os.path.join(Config.REPORTS_DIR, latest_html)
                with open(html_path, "r", encoding="utf-8") as f:
                    html_data = f.read()
                st.download_button(
                    "🌐 Download HTML Report",
                    data=html_data,
                    file_name=latest_html,
                    mime="text/html",
                    use_container_width=True
                )
                st.caption(f"File: `{latest_html}`")
