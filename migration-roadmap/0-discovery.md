Purpose: Establish validated baseline inventory of AS400 estate with quantified technical debt, business criticality scoring, and migration complexity assessment.
Pre-conditions

 AS400_Inventory_Detailed.csv (synthetic, 25 applications)
 Change window calendar defined
 Session concurrency profile documented
 Batch job dependency graph mapped
 Working assumptions confidence-scored

Tasks
Task 0.1: Application Portfolio Rationalization
Owner: Migration Architect + Business Stakeholder Panel
Duration: 3 weeks
Acceptance Criteria:

Each application assigned strategy: RETIRE | RETAIN | REHOST | REPLATFORM | REFACTOR
Business criticality score (1-5) validated by owner
Technical debt index calculated (code age × SLOC × dependency count)

Execution: #scripts/0.1_portfolio_analysis.py

Task 0.2: Dependency Graph Topological Sort
Owner: Data Architect
Duration: 2 weeks
Acceptance Criteria:

Directed acyclic graph (DAG) validated (no circular dependencies)
Migration wave grouping proposed (waves must respect dependencies)
Critical path identified (longest dependency chain)

Execution: #scripts/0.2_dependency_analysis.py

Task 0.3: Data Volume & Growth Profiling
Owner: Data Engineer
Duration: 2 weeks
Acceptance Criteria:

Historical growth rate calculated per application (12-month trend)
Storage forecast for 24 months post-migration
Hot/warm/cold data classification (access frequency)

Execution: #scripts/0.3_data_growth_analysis.py

Task 0.4: Code Complexity & Maintainability Index
Owner: Technical Architect
Duration: 3 weeks
Acceptance Criteria:

Cyclomatic complexity estimated per application (McCabe metric proxy)
Maintainability Index (MI) calculated: MI = 171 - 5.2×ln(HV) - 0.23×CC - 16.2×ln(LOC)
High-risk modules flagged (MI < 20)

Execution: #scripts/0.4_code_complexity.py


Task 0.5: Security & Compliance Baseline Audit
Owner: Security Architect + Compliance Officer
Duration: 4 weeks
Acceptance Criteria:

PCI-DSS scope identified (PAYMENT007, POS003)
SOX compliance apps tagged (ACCT010, PAYROLL019, AUDIT022)
Data classification per app (PII, PHI, PCI, Public)
Current AS400 security model documented (user profiles, authorization lists, exit programs)

Execution: # scripts/0.5_security_audit.py

Task 0.6: Network & Integration Topology Mapping
Owner: Network Architect
Duration: 2 weeks
Acceptance Criteria:

Current AS400 LPAR/partition layout documented
External integration points cataloged (EDI, payment gateways, carrier APIs)
Bandwidth requirements per application calculated
Hybrid connectivity options assessed (Dedicated Interconnect vs Partner Interconnect vs VPN)

Execution: # Current AS400 Network Topology