CREATE CONSTRAINT employee_id IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT department_name IF NOT EXISTS FOR (d:Department) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE;

MERGE (engineering:Department {name: "Engineering"})
  SET engineering.location = "Bengaluru", engineering.budget = 780000
MERGE (data:Department {name: "Data"})
  SET data.location = "Hyderabad", data.budget = 520000
MERGE (people:Department {name: "People"})
  SET people.location = "Mumbai", people.budget = 310000
MERGE (sales:Department {name: "Sales"})
  SET sales.location = "Delhi", sales.budget = 460000;

UNWIND [
  {id: 1, name: "Aarav Mehta", title: "Engineering Manager", salary: 135000, city: "Bengaluru", dept: "Engineering", manager: null, skills: ["Neo4j", "Python", "Leadership"]},
  {id: 2, name: "Maya Kapoor", title: "Backend Engineer", salary: 98000, city: "Pune", dept: "Engineering", manager: 1, skills: ["Python", "APIs", "Cypher"]},
  {id: 3, name: "Dev Patel", title: "Frontend Engineer", salary: 92000, city: "Bengaluru", dept: "Engineering", manager: 1, skills: ["React", "TypeScript", "UX"]},
  {id: 4, name: "Isha Rao", title: "Data Scientist", salary: 112000, city: "Hyderabad", dept: "Data", manager: 8, skills: ["Python", "ML", "Cypher"]},
  {id: 5, name: "Kabir Singh", title: "People Partner", salary: 85000, city: "Mumbai", dept: "People", manager: 9, skills: ["Hiring", "Coaching"]},
  {id: 6, name: "Naina Iyer", title: "Account Executive", salary: 104000, city: "Delhi", dept: "Sales", manager: 10, skills: ["Negotiation", "CRM"]},
  {id: 7, name: "Rohan Das", title: "Platform Engineer", salary: 121000, city: "Bengaluru", dept: "Engineering", manager: 1, skills: ["Kubernetes", "Neo4j", "Python"]},
  {id: 8, name: "Sara Thomas", title: "Head of Data", salary: 142000, city: "Hyderabad", dept: "Data", manager: null, skills: ["Analytics", "Leadership"]},
  {id: 9, name: "Priya Nair", title: "Head of People", salary: 118000, city: "Mumbai", dept: "People", manager: null, skills: ["Leadership", "Hiring"]},
  {id: 10, name: "Vikram Shah", title: "Sales Director", salary: 130000, city: "Delhi", dept: "Sales", manager: null, skills: ["Leadership", "Forecasting"]}
] AS row
MERGE (employee:Employee {id: row.id})
  SET employee.name = row.name,
      employee.title = row.title,
      employee.salary = row.salary,
      employee.city = row.city
WITH employee, row
MATCH (department:Department {name: row.dept})
MERGE (employee)-[:WORKS_IN]->(department)
WITH employee, row
FOREACH (managerId IN CASE WHEN row.manager IS NULL THEN [] ELSE [row.manager] END |
  MERGE (manager:Employee {id: managerId})
  MERGE (employee)-[:REPORTS_TO]->(manager)
)
WITH employee, row
FOREACH (skillName IN row.skills |
  MERGE (skill:Skill {name: skillName})
  MERGE (employee)-[:HAS_SKILL]->(skill)
);

MATCH (maya:Employee {name: "Maya Kapoor"}), (dev:Employee {name: "Dev Patel"})
MERGE (maya)-[:COLLABORATES_WITH {project: "Employee Knowledge Graph"}]->(dev)
MERGE (dev)-[:COLLABORATES_WITH {project: "Employee Knowledge Graph"}]->(maya);
