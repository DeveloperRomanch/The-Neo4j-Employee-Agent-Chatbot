CREATE CONSTRAINT employee_id IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT department_name IF NOT EXISTS FOR (d:Department) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT shipping_service_id IF NOT EXISTS FOR (s:ShippingService) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT store_id IF NOT EXISTS FOR (s:Store) REQUIRE s.id IS UNIQUE;

// 1. Create Departments
MERGE (rd:Department {name: "Research & Development"})
  SET rd.location = "Bengaluru", rd.budget = 1500000
MERGE (qa:Department {name: "Quality Assurance"})
  SET qa.location = "Pune", qa.budget = 800000
MERGE (sales:Department {name: "Sales & Marketing"})
  SET sales.location = "Mumbai", sales.budget = 1200000
MERGE (sc:Department {name: "Supply Chain"})
  SET sc.location = "Hyderabad", sc.budget = 950000
MERGE (hr:Department {name: "Human Resources"})
  SET hr.location = "Delhi", hr.budget = 400000;

// 2. Create VP/CSO Managers and Link to Departments
MERGE (m1:Employee {id: 201})
  SET m1.name = "Dr. Aditya Sharma", m1.title = "Chief Scientific Officer", m1.salary = 250000, m1.city = "Bengaluru"
WITH m1 MATCH (d:Department {name: "Research & Development"}) MERGE (m1)-[:WORKS_IN]->(d);

MERGE (m2:Employee {id: 202})
  SET m2.name = "Neha Patil", m2.title = "VP of Quality Assurance", m2.salary = 180000, m2.city = "Pune"
WITH m2 MATCH (d:Department {name: "Quality Assurance"}) MERGE (m2)-[:WORKS_IN]->(d);

MERGE (m3:Employee {id: 203})
  SET m3.name = "Rajesh Kapoor", m3.title = "VP of Sales", m3.salary = 210000, m3.city = "Mumbai"
WITH m3 MATCH (d:Department {name: "Sales & Marketing"}) MERGE (m3)-[:WORKS_IN]->(d);

MERGE (m4:Employee {id: 204})
  SET m4.name = "Amit Verma", m4.title = "VP of Supply Chain", m4.salary = 190000, m4.city = "Hyderabad"
WITH m4 MATCH (d:Department {name: "Supply Chain"}) MERGE (m4)-[:WORKS_IN]->(d);

MERGE (m5:Employee {id: 205})
  SET m5.name = "Priya Sen", m5.title = "Chief Human Resources Officer", m5.salary = 170000, m5.city = "Delhi"
WITH m5 MATCH (d:Department {name: "Human Resources"}) MERGE (m5)-[:WORKS_IN]->(d);

// 3. Populate Employees programmatically in range groups
// R&D Employees
UNWIND range(1, 40) AS i
MERGE (e:Employee {id: i})
  SET e.name = "Scientist " + i, e.title = "Research Scientist", e.salary = 80000 + (i * 1000), e.city = "Bengaluru"
WITH e
MATCH (d:Department {name: "Research & Development"}), (m:Employee {id: 201})
MERGE (e)-[:WORKS_IN]->(d)
MERGE (e)-[:REPORTS_TO]->(m);

// QA Employees
UNWIND range(41, 70) AS i
MERGE (e:Employee {id: i})
  SET e.name = "QA Analyst " + i, e.title = "Quality Analyst", e.salary = 50000 + (i * 500), e.city = "Pune"
WITH e
MATCH (d:Department {name: "Quality Assurance"}), (m:Employee {id: 202})
MERGE (e)-[:WORKS_IN]->(d)
MERGE (e)-[:REPORTS_TO]->(m);

// Sales Employees
UNWIND range(71, 110) AS i
MERGE (e:Employee {id: i})
  SET e.name = "Sales Exec " + i, e.title = "Sales Executive", e.salary = 60000 + (i * 400), e.city = "Mumbai"
WITH e
MATCH (d:Department {name: "Sales & Marketing"}), (m:Employee {id: 203})
MERGE (e)-[:WORKS_IN]->(d)
MERGE (e)-[:REPORTS_TO]->(m);

// Supply Chain Employees
UNWIND range(111, 140) AS i
MERGE (e:Employee {id: i})
  SET e.name = "Logistics Specialist " + i, e.title = "Logistics Coordinator", e.salary = 55000 + (i * 300), e.city = "Hyderabad"
WITH e
MATCH (d:Department {name: "Supply Chain"}), (m:Employee {id: 204})
MERGE (e)-[:WORKS_IN]->(d)
MERGE (e)-[:REPORTS_TO]->(m);

// HR Employees
UNWIND range(141, 150) AS i
MERGE (e:Employee {id: i})
  SET e.name = "HR Associate " + i, e.title = "HR Partner", e.salary = 45000 + (i * 200), e.city = "Delhi"
WITH e
MATCH (d:Department {name: "Human Resources"}), (m:Employee {id: 205})
MERGE (e)-[:WORKS_IN]->(d)
MERGE (e)-[:REPORTS_TO]->(m);

// 4. Create Products
UNWIND [
  {type: "Antibiotic", prefix: "Amox"},
  {type: "Vaccine", prefix: "Covax"},
  {type: "Painkiller", prefix: "Nuro"},
  {type: "Cardiovascular", prefix: "Cardio"},
  {type: "Antiviral", prefix: "Viropax"}
] AS prodType
UNWIND range(1, 10) AS num
MERGE (p:Product {id: num + (CASE prodType.type 
                              WHEN "Antibiotic" THEN 300 
                              WHEN "Vaccine" THEN 310 
                              WHEN "Painkiller" THEN 320 
                              WHEN "Cardiovascular" THEN 330 
                              ELSE 340 END)})
  SET p.name = prodType.prefix + "-" + num, 
      p.type = prodType.type,
      p.price = 50 + (num * 15), 
      p.stock = 1000 + (num * 250)
WITH p
MATCH (d:Department {name: "Research & Development"})
MERGE (d)-[:MANAGES]->(p);

// 5. Create Shipping Services
UNWIND range(1, 10) AS i
MERGE (s:ShippingService {id: i + 400})
  SET s.name = "Logistics Partner " + i, 
      s.type = (CASE WHEN i % 2 = 0 THEN "Express" ELSE "Standard" END),
      s.cost = 150 + (i * 20);

// Connect Products to Shipping Services (SHIPPED_BY)
MATCH (p:Product), (s:ShippingService)
WHERE (p.id + s.id) % 5 = 0
MERGE (p)-[:SHIPPED_BY]->(s);

// 6. Create Medical Stores
UNWIND range(1, 60) AS i
MERGE (st:Store {id: i + 500})
  SET st.name = "MedStore " + i, 
      st.city = (CASE i % 4 WHEN 0 THEN "Bengaluru" WHEN 1 THEN "Mumbai" WHEN 2 THEN "Hyderabad" ELSE "Delhi" END),
      st.revenue = 50000 + (i * 12500);

// Connect Shipping Services to Stores (DELIVERS_TO)
MATCH (s:ShippingService), (st:Store)
WHERE (s.id + st.id) % 6 = 0
MERGE (s)-[:DELIVERS_TO]->(st);

// Connect Stores to Products (SELLS)
MATCH (st:Store), (p:Product)
WHERE (st.id + p.id) % 12 = 0
MERGE (st)-[:SELLS]->(p);

// 7. Create Skills and connect Employees
UNWIND ["Virology", "Pharmacology", "Formulation", "Clinical Trials", "Bioinformatics", "Data Analysis", "Supply Chain Optimization", "Regulatory Compliance", "B2B Sales", "Cold Chain Logistics"] AS skillName
MERGE (s:Skill {name: skillName});

// Connect Scientists to Skills
MATCH (e:Employee {title: "Research Scientist"}), (s:Skill)
WHERE s.name IN ["Virology", "Pharmacology", "Formulation", "Clinical Trials", "Bioinformatics"]
AND (e.id + size(s.name)) % 3 = 0
MERGE (e)-[:HAS_SKILL]->(s);

// Connect Logistics Coordinators to Skills
MATCH (e:Employee {title: "Logistics Coordinator"}), (s:Skill)
WHERE s.name IN ["Supply Chain Optimization", "Cold Chain Logistics"]
MERGE (e)-[:HAS_SKILL]->(s);

// Connect Sales Executives to Skills
MATCH (e:Employee {title: "Sales Executive"}), (s:Skill)
WHERE s.name IN ["B2B Sales", "Data Analysis"]
MERGE (e)-[:HAS_SKILL]->(s);
