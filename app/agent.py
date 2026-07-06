from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_google_genai import ChatGoogleGenerativeAI

# .env file se keys load karne ke liye
load_dotenv()

@dataclass(frozen=True)
class AgentResult:
    answer: str
    cypher: str

# 1. Neo4j Database connection setup
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password123")
)

# 2. Dimaag (Gemini LLM) initialize karna
# Hum gemini-1.5-flash use kar rahe hain jo fast aur accurate hai. 
# Temperature=0 taaki yeh sahi aur deterministic Cypher queries banaye.
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", 
                            temperature=0,
                            api_key=os.getenv("GOOGLE_API_KEY"))

# 3. Automatic Text-to-Cypher chain create karna
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    return_intermediate_steps=True,
    allow_dangerous_requests=True  # Database operations allow karne ke liye zaroori hai
)

def run_agent(question: str) -> AgentResult:
    """
    Yeh function aapke Streamlit UI se connect hoga.
    Purani rule-based logic ab poori tarah AI-driven ho gayi hai!
    """
    try:
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