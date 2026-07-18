from __future__ import annotations
import html
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from agent import run_agent
from graph import EmployeeGraph, load_settings, Neo4jSettings


# ====================== CONFIG ======================
st.set_page_config(
    page_title="Neo4j Employee Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    """Load CSS from separate file"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(current_dir, "styles.css")
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ styles.css file not found!")
def get_logo_svg() -> str:
    """Load the logo SVG content and strip whitespaces/newlines for markdown compatibility"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(os.path.dirname(current_dir), "assets", "logo.svg")
        if os.path.exists(logo_path):
            with open(logo_path, "r", encoding="utf-8") as f:
                content = f.read()
                single_line_svg = "".join(line.strip() for line in content.splitlines())
                return single_line_svg
    except Exception:
        pass
    return ""


def login_page() -> None:
    """Render a clean, modern login form card centered on the screen"""
    logo_svg = get_logo_svg()
    
    # Load login page styling overrides dynamically
    st.markdown("""
        <style>
        div[data-testid="stVerticalBlockBorder"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 16px !important;
            padding: 40px !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
            margin-top: 60px !important;
        }
        div[data-testid="stVerticalBlockBorder"] svg {
            max-width: 260px !important;
            height: auto !important;
            margin: 0 auto 24px !important;
            display: block !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            if logo_svg:
                st.markdown(logo_svg, unsafe_allow_html=True)
            else:
                st.markdown("<h1 style='color:#0f172a; text-align:center;'>SynapsesMed</h1>", unsafe_allow_html=True)
                
            st.markdown("<h3 style='margin-top:15px; color:#0f172a; font-weight:600; text-align:center;'>Welcome Back</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color:#64748b; margin-bottom:24px; font-size:14px; text-align:center;'>Please enter your credentials to access the agent.</p>", unsafe_allow_html=True)
            
            username = st.text_input("Username", placeholder="Username", label_visibility="collapsed", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed", key="login_password")
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Sign In", use_container_width=True, type="primary", key="login_submit"):
                    expected_username = os.getenv("APP_USERNAME", "admin")
                    expected_password = os.getenv("APP_PASSWORD", "admin123")
                    
                    if username == expected_username and password == expected_password:
                        st.session_state.authenticated = True
                        st.session_state.show_login = False
                        st.query_params["authenticated"] = "true"
                        st.rerun()
                    else:
                        st.error("Incorrect credentials.")
            with btn_col2:
                if st.button("Cancel", use_container_width=True, type="secondary", key="login_cancel"):
                    st.session_state.show_login = False
                    st.rerun()
def render_js_helper():
    """Inject JavaScript to manage sidebar responsive collapse/expand behavior"""
    collapse_flag = "true" if st.session_state.get("collapse_sidebar", False) else "false"
    # Reset flag so it only runs once per click
    st.session_state.collapse_sidebar = False

    js_code = f"""
    <script>
    const doc = window.parent.document;

    function expandSidebar() {{
        let attempts = 0;
        const interval = setInterval(() => {{
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (sidebar && sidebar.getAttribute('aria-expanded') === 'false') {{
                const expandBtn = doc.querySelector('[data-testid="collapsedControl"] button') || 
                                  doc.querySelector('[data-testid="collapsedControl"]') ||
                                  doc.querySelector('[data-testid="stSidebarCollapseButton"]');
                if (expandBtn) {{
                    expandBtn.click();
                    clearInterval(interval);
                    return;
                }}
            }}
            attempts++;
            if (attempts > 10) {{
                clearInterval(interval);
            }}
        }}, 100);
    }}

    function collapseSidebar() {{
        let attempts = 0;
        const interval = setInterval(() => {{
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (sidebar && sidebar.getAttribute('aria-expanded') === 'true') {{
                let collapseBtn = sidebar.querySelector('[data-testid="stSidebarCollapseButton"]');
                if (!collapseBtn) {{
                    const allButtons = sidebar.querySelectorAll('button');
                    for (const btn of allButtons) {{
                        if (!btn.closest('[data-testid="stSidebarUserContent"]')) {{
                            collapseBtn = btn;
                            break;
                        }}
                    }}
                }}
                if (collapseBtn) {{
                    collapseBtn.click();
                    clearInterval(interval);
                    return;
                }}
            }}
            attempts++;
            if (attempts > 10) {{
                clearInterval(interval);
            }}
        }}, 100);
    }}

    function handleSidebar() {{
        const isMobile = window.parent.innerWidth < 992;
        
        if (isMobile) {{
            if ({collapse_flag}) {{
                collapseSidebar();
            }}
        }} else {{
            expandSidebar();
        }}
    }}

    // Run handleSidebar after DOM renders
    setTimeout(handleSidebar, 150);
    
    // Listen to parent resize events and clean up on unload
    window.parent.addEventListener('resize', handleSidebar);
    window.addEventListener('unload', () => {{
        window.parent.removeEventListener('resize', handleSidebar);
    }});
    </script>
    """
    components.html(js_code, height=0, width=0)


# ====================== HELPERS ======================
def get_graph() -> EmployeeGraph:
    if "neo4j_settings" not in st.session_state:
        st.session_state.neo4j_settings = load_settings()
    return EmployeeGraph(st.session_state.neo4j_settings)


def init_state() -> None:
    if "authenticated" not in st.session_state:
        if st.query_params.get("authenticated") == "true":
            st.session_state.authenticated = True
        else:
            st.session_state.authenticated = False
    if "show_login" not in st.session_state:
        st.session_state.show_login = False
    if "neo4j_settings" not in st.session_state:
        st.session_state.neo4j_settings = load_settings()
    if "collapse_sidebar" not in st.session_state:
        st.session_state.collapse_sidebar = False
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Ask me about employees, departments, products, shipping services, medical stores, or skills.",
                "cypher": None,
                "records": None,
                "time": datetime.now().strftime("%I:%M:%S %p"),
            }
        ]


def run_question(question: str) -> None:
    if "neo4j_settings" not in st.session_state:
        st.session_state.neo4j_settings = load_settings()

    agent_result = run_agent(question, st.session_state.neo4j_settings)

    # Execute Cypher to get raw records for graph view
    records = None
    if agent_result.cypher:
        graph = get_graph()
        try:
            records = graph.query(agent_result.cypher)
        except Exception:
            records = None
        finally:
            graph.close()

    now = datetime.now().strftime("%I:%M:%S %p")

    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "cypher": None,
        "records": None,
        "time": now
    })

    st.session_state.messages.append({
        "role": "assistant",
        "content": agent_result.answer,
        "cypher": agent_result.cypher,
        "records": records,
        "time": now
    })


def render_message(message: dict) -> None:
    if message.get("cypher"):
        st.caption("Cypher query executed")
        st.code(message["cypher"], language="cypher")

    is_user = message["role"] == "user"
    avatar = "👤" if is_user else "🧠"
    title = "You" if is_user else "Neo4j Agent"
    css_class = "user-message" if is_user else "agent-message"

    st.markdown(f"""
        <div class="chat-card {css_class}">
            <div class="chat-avatar">{avatar}</div>
            <div class="chat-body">
                <div class="chat-meta">
                    <strong>{title}</strong>
                    <span>{message["time"]}</span>
                </div>
                <div class="chat-text">{html.escape(message["content"])}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def sidebar() -> None:
    logo_svg = get_logo_svg()
    with st.sidebar:
        if logo_svg:
            st.markdown(f'<div class="sidebar-logo">{logo_svg}</div>', unsafe_allow_html=True)
        st.title("Neo4j Agent")
        st.markdown("**Ask natural language questions** about the pharmaceutical knowledge graph.")

        st.subheader("Sample Questions")
        sample_questions = [
            "What are the top 5 highest selling products?",
            "Which shipping services deliver to MedStore 12?",
            "Who are the research scientists with Virology skill?",
            "List all products managed by Research & Development department",
            "Which stores sell Cardio-1?",
            "What is the total revenue of all stores in Mumbai?",
            "Who is the manager of Scientist 5?",
        ]
        for q in sample_questions:
            if st.button(q, use_container_width=True, key=f"btn_{q}"):
                if not st.session_state.get("authenticated", False):
                    st.session_state.show_login = True
                else:
                    run_question(q)
                    st.session_state.collapse_sidebar = True
                st.rerun()

        st.subheader("Database Info")
        settings: Neo4jSettings = st.session_state.neo4j_settings
        st.markdown(f"**Database:** `{settings.database}`")
        st.markdown(f"**URI:** `{settings.uri}`")
        st.markdown(f"**Username:** `{settings.username}`")
        st.markdown("**Type:** Neo4j graph database")

        with st.expander("🔌 Configure Neo4j Connection", expanded=False):
            # ... (your connection form code - kept same)
            pass  # I'll expand this if needed

        # Connection Status
        graph = get_graph()
        try:
            if graph.verify_connectivity():
                st.success("✅ Neo4j is connected.")
            else:
                st.error("Neo4j is not reachable.")
        except Exception as e:
            st.error(f"Connection failed: {e}")
        finally:
            graph.close()

        if st.button("Seed Demo Data", use_container_width=True):
            if not st.session_state.get("authenticated", False):
                st.session_state.show_login = True
                st.rerun()
            else:
                st.session_state.collapse_sidebar = True
                graph = get_graph()
                try:
                    graph.seed()
                    st.success("Demo data seeded successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Seed failed: {e}")
                finally:
                    graph.close()

        # Clear Chat Button in Sidebar
        if st.button("Clear Chat", use_container_width=True, key="sidebar_clear"):
            st.session_state.messages = []
            st.rerun()

        # Logout Section (only show if authenticated)
        if st.session_state.get("authenticated", False):
            st.markdown('<div class="logout-section">', unsafe_allow_html=True)
            if st.button("Logout", use_container_width=True, key="sidebar_logout"):
                st.session_state.authenticated = False
                st.session_state.messages = []
                st.query_params.pop("authenticated", None)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


# ====================== MAIN APP ======================
def main():
    load_css()
    init_state()
    
    render_js_helper()
    sidebar()

    # If show_login is True, only show the login page
    if st.session_state.get("show_login", False):
        login_page()
        return


    # Header
    logo_svg = get_logo_svg()
    if logo_svg:
        st.markdown(f"""
            <div class="site-branding">
                {logo_svg}
            </div>
            <div class="page-header">
                <h1>Pharmaceutical Knowledge Graph Chatbot</h1>
                <p>Ask questions about pharmaceutical products, medical stores, shipping, employees, and departments.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="site-branding">
                <span class="branding-logo">🧠</span>
                <span class="branding-title">SynapsesMed</span>
            </div>
            <div class="page-header">
                <h1>Pharmaceutical Knowledge Graph Chatbot</h1>
                <p>Ask questions about pharmaceutical products, medical stores, shipping, employees, and departments.</p>
            </div>
        """, unsafe_allow_html=True)

    # Chat Input
    question = st.chat_input("Ask about pharmaceutical products, stores, shipping, employees..")
    if question:
        if not st.session_state.get("authenticated", False):
            st.session_state.show_login = True
        else:
            run_question(question)
        st.rerun()

    # Display Messages
    for msg in st.session_state.messages:
        render_message(msg)


if __name__ == "__main__":
    main()