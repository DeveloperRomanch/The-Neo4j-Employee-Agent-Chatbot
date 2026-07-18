from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    username: str
    password: str
    database: str


def load_settings() -> Neo4jSettings:
    return Neo4jSettings(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password123"),
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
    )


class EmployeeGraph:
    def __init__(self, settings: Neo4jSettings):
        self.settings = settings
        self.driver = GraphDatabase.driver(
            settings.uri,
            auth=(settings.username, settings.password),
        )

    def close(self) -> None:
        self.driver.close()

    def verify_connectivity(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def query(self, cypher: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.driver.session(database=self.settings.database) as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def seed(self) -> None:
        seed_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "neo4j", "seed.cypher")
        with open(seed_file_path, "r") as f:
            cypher_content = f.read()
        
        # Split by semicolon, filtering out comments and empty statements
        statements = []
        for stmt in cypher_content.split(";"):
            lines = []
            for line in stmt.split("\n"):
                stripped = line.strip()
                if stripped and not stripped.startswith("//"):
                    lines.append(line)
            clean_stmt = "\n".join(lines).strip()
            if clean_stmt:
                statements.append(clean_stmt)
                
        with self.driver.session(database=self.settings.database) as session:
            for statement in statements:
                session.run(statement)
