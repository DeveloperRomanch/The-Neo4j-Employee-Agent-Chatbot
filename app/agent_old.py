from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentResult:
    answer: str
    cypher: str


def answer_from_records(question: str, records: list[dict]) -> str:
    q = normalize(question)
    limit = extract_limit(q)

    if limit and is_salary_ranking(q):
        if not records:
            return f"I could not find the top {limit} salary records."
        lines = [f"{row['name']} ({row['salary']:,})" for row in records]
        return f"Top {len(records)} highest paid employees: " + "; ".join(lines) + "."

    if "total" in q and "salary" in q:
        total = records[0].get("totalSalary", 0) if records else 0
        return f"The total salary of all employees is {total:,}."

    if "average" in q and "salary" in q:
        average = records[0].get("averageSalary", 0) if records else 0
        return f"The average salary is {average:,.0f}."

    if "highest" in q and "salary" in q:
        if not records:
            return "I could not find a highest salary record."
        row = records[0]
        return f"The highest paid employee is {row['name']} with a salary of {row['salary']:,}."

    if "manager" in q or "reports" in q or "reporting" in q:
        if not records:
            return "I could not find reporting relationships for that question."
        lines = [f"{row['employee']} reports to {row['manager']}" for row in records]
        return "Reporting relationships: " + "; ".join(lines) + "."

    if "skill" in q:
        if not records:
            return "I could not find employees with that skill."
        names = ", ".join(row["name"] for row in records)
        return f"Employees matching that skill question: {names}."

    if "department" in q or "works in" in q or "engineering" in q or "data" in q or "sales" in q or "people" in q:
        if not records:
            return "I could not find employees for that department."
        names = ", ".join(row["name"] for row in records)
        return f"Employees found: {names}."

    if "show" in q or "list" in q or "employee" in q:
        if not records:
            return "I could not find employee records."
        names = ", ".join(f"{row['name']} ({row['title']})" for row in records)
        return f"Here are the employees: {names}."

    return "I ran the graph query and returned the matching records."


def build_cypher(question: str) -> str:
    q = normalize(question)
    limit = extract_limit(q)

    if limit and is_salary_ranking(q):
        return (
            "MATCH (e:Employee) "
            "RETURN e.name AS name, e.title AS title, e.salary AS salary "
            f"ORDER BY e.salary DESC LIMIT {limit}"
        )

    if "total" in q and "salary" in q:
        return "MATCH (e:Employee) RETURN sum(e.salary) AS totalSalary"

    if "average" in q and "salary" in q:
        return "MATCH (e:Employee) RETURN avg(e.salary) AS averageSalary"

    if "highest" in q and "salary" in q:
        return "MATCH (e:Employee) RETURN e.name AS name, e.salary AS salary ORDER BY e.salary DESC LIMIT 1"

    if "manager" in q or "reports" in q or "reporting" in q:
        return (
            "MATCH (e:Employee)-[:REPORTS_TO]->(m:Employee) "
            "RETURN e.name AS employee, m.name AS manager ORDER BY manager, employee"
        )

    skill = extract_after(q, "skill")
    if skill:
        return (
            "MATCH (e:Employee)-[:HAS_SKILL]->(s:Skill) "
            f"WHERE toLower(s.name) CONTAINS {quote(skill)} "
            "RETURN e.name AS name, e.title AS title, s.name AS skill ORDER BY name"
        )

    department = find_department(q)
    if department:
        return (
            "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) "
            f"WHERE toLower(d.name) = {quote(department)} "
            "RETURN e.name AS name, e.title AS title, e.salary AS salary, d.name AS department ORDER BY name"
        )

    if "department" in q:
        return (
            "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) "
            "RETURN d.name AS department, collect(e.name) AS employees, count(e) AS employeeCount ORDER BY department"
        )

    return (
        "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) "
        "RETURN e.name AS name, e.title AS title, e.salary AS salary, e.city AS city, d.name AS department "
        "ORDER BY e.name"
    )


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def extract_after(text: str, keyword: str) -> str | None:
    match = re.search(rf"{keyword}\s+([a-z0-9+#.\- ]+)", text)
    if not match:
        return None
    value = match.group(1).strip(" ?.")
    return value or None


def find_department(text: str) -> str | None:
    for department in ("engineering", "data", "people", "sales"):
        if department in text:
            return department
    return None


def extract_limit(text: str) -> int | None:
    match = re.search(r"\b(?:top|first)\s+(\d+)\b", text)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\s+(?:highest|top|best)\b", text)
    if match:
        return int(match.group(1))
    return None


def is_salary_ranking(text: str) -> bool:
    return any(word in text for word in ("salary", "paid", "earn", "highest", "top"))
