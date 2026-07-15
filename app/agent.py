from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_google_genai import ChatGoogleGenerativeAI

from graph import Neo4jSettings

# .env file se keys load karne ke liye
load_dotenv()

@dataclass(frozen=True)
class AgentResult:
    answer: str
    cypher: str

# 2. Dimaag (Gemini LLM) initialize karna
# Hum gemini-1.5-flash use kar rahe hain jo fast aur accurate hai. 
# Temperature=0 taaki yeh sahi aur deterministic Cypher queries banaye.
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", 
                            temperature=0,
                            api_key=os.getenv("GOOGLE_API_KEY"))

_cached_settings: Neo4jSettings | None = None
_cached_chain: GraphCypherQAChain | None = None

def get_agent_chain(settings: Neo4jSettings) -> GraphCypherQAChain:
    global _cached_settings, _cached_chain
    if _cached_chain is None or _cached_settings != settings:
        # Purane driver ko close karna if possible, memory/connection leak se bachne ke liyeq
        if _cached_chain is not None:
            try:
                _cached_chain.graph._driver.close()
            except Exception:
                pass
        
        graph = Neo4jGraph(
            url=settings.uri,
            username=settings.username,
            password=settings.password,
            database=settings.database
        )
        _cached_chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,
            enhanced_schema=False
        )
        _cached_settings = settings
    return _cached_chain


def run_agent(question: str, settings: Neo4jSettings) -> AgentResult:
    """
    Yeh function aapke Streamlit UI se connect hoga.
    Purani rule-based logic ab poori tarah AI-driven ho gayi hai!
    """
    try:
        chain = get_agent_chain(settings)
        # LLM se schema ke basis par query chalwana
        response = chain.invoke({"query": question})

        answer = response.get("result", "Mujhe iska jawab nahi mila.")
        
        # Intermediate steps se generated Cypher query nikalna taaki UI par dikha sakein
        steps = response.get("intermediate_steps", [])
        cypher_query = ""
        for step in steps:
            if isinstance(step, dict) and "query" in step:
                cypher_query = step["query"]
                break
                
        return AgentResult(answer=answer, cypher=cypher_query)
        
    except Exception as e:
        return AgentResult(
            answer=f"Sorry, query generate karne mein issue aaya: {str(e)}", 
            cypher=""
        )