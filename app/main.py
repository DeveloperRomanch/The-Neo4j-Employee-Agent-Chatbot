from __future__ import annotations

import html
from datetime import datetime

import pandas as pd
import streamlit as st

from agent import run_agent
from graph import EmployeeGraph, load_settings


st.set_page_config(
    page_title="Neo4j Employee Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_CSS = """
<style>
section[data-testid="stSidebar"] {
  border-right: 1px solid #E5E7EB;
}

.brand-icon,
.header-icon {
  align-items: center;
  background: linear-gradient(135deg, #7C3AED, #22C55E);
  border-radius: 8px;
  color: white;
  display: inline-flex;
  font-size: 28px;
  height: 56px;
  justify-content: center;
  margin-bottom: 12px;
  width: 56px;
}

.page-header {
  align-items: center;
  display: flex;
  gap: 22px;
  margin: 28px 0 26px;
}

.page-header h1 {
  font-size: 34px;
  line-height: 1.1;
  margin: 0 0 8px;
}

.page-header p {
  color: #64748B;
  font-size: 16px;
  margin: 0;
}

.chat-card {
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  display: flex;
  gap: 18px;
  margin: 14px 0;
  padding: 22px;
}

.user-message {
  background: #FAF7FF;
}

.agent-message {
  background: #F0FDF4;
}

.chat-avatar {
  align-items: center;
  border-radius: 8px;
  display: flex;
  flex: 0 0 46px;
  font-size: 24px;
  height: 46px;
  justify-content: center;
}

.user-message .chat-avatar {
  background: #EDE9FE;
}

.agent-message .chat-avatar {
  background: #DCFCE7;
}

.chat-body {
  flex: 1;
  min-width: 0;
}

.chat-meta {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.chat-meta strong {
  color: #6D28D9;
}

.agent-message .chat-meta strong {
  color: #16A34A;
}

.chat-meta span {
  color: #94A3B8;
  font-size: 13px;
}

.chat-text {
  color: #111827;
  font-size: 16px;
}

button[kind="secondary"] {
  border-radius: 8px;
}

div[data-testid="stCodeBlock"] {
  border-radius: 8px;
}
</style>
"""


def get_graph() -> EmployeeGraph:
    return EmployeeGraph(load_settings())


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Ask me about employees, departments, salaries, managers, or skills.",
                "cypher": None,
                "records": None,
                "time": datetime.now().strftime("%I:%M:%S %p"),
            }
        ]


def run_question(question: str) -> None:
    """
    Is function ko humne purani rule-based chain se hata kar
    naye LangChain + Gemini agent se fully connect kar diya hai.
    """
    # 1. Naye agent ko call karke natural language ka text answer aur cypher query ek sath lena
    agent_result = run_agent(question)
    answer = agent_result.answer
    cypher = agent_result.cypher

    records = None
    
    # 2. Agar Gemini ne koi valid Cypher query return ki hai, toh use hum graph par execute karenge
    # Taaki UI mein 'View graph records' ka raw data expander perfectly chalta rahe.
    if cypher:
        graph = get_graph()
        try:
            records = graph.query(cypher)
        except Exception:
            # Agar query execution fail bhi ho jaye, toh front-end crash nahi hoga
            records = None
        finally:
            graph.close()

    now = datetime.now().strftime("%I:%M:%S %p")
    st.session_state.messages.append(
        {"role": "user", "content": question, "cypher": None, "records": None, "time": now}
    )
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "cypher": cypher if cypher else None, "records": records if records else None, "time": now}
    )


def render_message(message: dict) -> None:
    role = message["role"]
    is_user = role == "user"
    avatar = "👤" if is_user else "🧠"
    title = "You" if is_user else "Neo4j Agent"
    css_class = "user-message" if is_user else "agent-message"

    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )

    if message.get("cypher"):
        st.caption("Cypher query executed")
        st.code(message["cypher"], language="cypher")

    if message.get("records"):
        with st.expander("View graph records", expanded=False):
            st.dataframe(pd.DataFrame(message["records"]), use_container_width=True)


def sidebar() -> None:
    with st.sidebar:
        st.markdown("<div class='brand-icon'>⌘</div>", unsafe_allow_html=True)
        st.title("Neo4j Agent")
        st.markdown("Ask natural language questions about an employee graph database.")

        st.subheader("Sample Questions")
        questions = [
            "Show all employees",
            "What is the total salary of all employees?",
            "Who has the highest salary?",
            "List all employees in Engineering department",
            "Show reporting relationships",
            "Who has skill Neo4j?",
            "What is the average salary?",
        ]
        for question in questions:
            if st.button(question, use_container_width=True):
                run_question(question)
                st.rerun()

        st.subheader("Database Info")
        settings = load_settings()
        st.markdown(f"**Database:** `{settings.database}`")
        st.markdown(f"**URI:** `{settings.uri}`")
        st.markdown("**Type:** Neo4j graph database")
        st.markdown("**Model:** Employee → Department, Skill, Manager")

        graph = get_graph()
        try:
            if graph.verify_connectivity():
                st.success("Neo4j is connected.")
            else:
                st.error("Neo4j is not reachable. Start it with `docker compose up -d`.")
        except Exception as exc:
            st.error(f"Neo4j connection failed: {exc}")
        finally:
            graph.close()

        if st.button("Seed Demo Data", use_container_width=True):
            graph = get_graph()
            try:
                graph.seed()
                st.success("Demo graph data seeded.")
            except Exception as exc:
                st.error(f"Seed failed: {exc}")
            finally:
                graph.close()


def main() -> None:
    init_state()
    st.markdown(APP_CSS, unsafe_allow_html=True)
    sidebar()

    st.markdown(
        """
        <div class="page-header">
          <div class="header-icon">🧠</div>
          <div>
            <h1>Neo4j Employee Agent Chatbot</h1>
            <p>Ask questions about employees, departments, salaries, managers, and skills.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns([1, 0.18])
    with top_right:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    question = st.chat_input("Ask about employees, departments, salaries..")
    if question:
        run_question(question)
        st.rerun()
        
    for message in st.session_state.messages:
        render_message(message)


if __name__ == "__main__":
    main()