from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()

@dataclass(frozen=True)
class AgentResult:
    answer: str
    cypher: str
    intermediate_steps: list = None


# Better system prompt to reduce hallucination
CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Cypher query generator.
You must ONLY return a valid Cypher query. No explanations, no markdown, no extra text.

Schema:
{schema}

Question: {question}

Rules:
- Use only the nodes and relationships in the schema.
- Return only the Cypher query.
- Always use proper labels and relationship types.
- For counting use `count(e)`.
- For highest salary use `ORDER BY e.salary DESC LIMIT 1`.
"""

cypher_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",        # Better than lite for reasoning
    temperature=0.0,                 # Very important for Cypher
    api_key=os.getenv("GOOGLE_API_KEY")
)

_cached_graph = None
_cached_chain = None


def get_agent_chain(settings):
    global _cached_graph, _cached_chain

    if _cached_chain is None:
        graph = Neo4jGraph(
            url=settings.uri,
            username=settings.username,
            password=settings.password,
            database=settings.database,
            refresh_schema=True
        )
        
        _cached_chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,
            cypher_prompt=cypher_prompt,          # Custom prompt
            enhanced_schema=True,                 # Better schema understanding
        )
        _cached_graph = graph

    return _cached_chain


def run_agent(question: str, settings) -> AgentResult:
    try:
        chain = get_agent_chain(settings)
        response = chain.invoke({"query": question})

        answer = response.get("result", "Sorry, I couldn't find an answer.")
        intermediate = response.get("intermediate_steps", [])

        # Extract Cypher query safely
        cypher_query = ""
        for step in intermediate:
            if isinstance(step, dict) and "query" in step:
                cypher_query = step["query"]
                break

        return AgentResult(
            answer=answer,
            cypher=cypher_query,
            intermediate_steps=intermediate
        )

    except Exception as e:
        return AgentResult(
            answer=f"Error: {str(e)}",
            cypher="",
            intermediate_steps=[]
        )