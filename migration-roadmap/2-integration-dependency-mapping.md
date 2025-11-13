# 2-integration-dependency-mapping.md

Purpose: Map all integration points (APIs, batch files, message queues, database links), quantify inter-application dependencies, establish API modernization roadmap for AS400 RPG/COBOL programs.
Pre-conditions

 0-discovery.md complete (25 applications, dependency graph, network topology)
 1-data-cleansing.md complete (schema extraction, data quality baseline)
 PAYMENT007 PCI remediation escalated to InfoSec (blocking issue acknowledged)
 Network bandwidth requirements: 3.85 Gbps peak (Partner Interconnect sized)

## Tasks

### Task 2.1: Integration Point Catalog & Classification

Owner: Integration Architect
Duration: 3 weeks
Acceptance Criteria:

Every network call from Task 0.6 traced to endpoint (internal/external, protocol, auth method)
Batch file exchanges documented (format, frequency, size, transfer method)
Message queue topology mapped (MQ Series channels, topic/queue names)
Database links identified (DRDA, ODBC, native DB2/400 connections)

Execution: # scripts/2.1_integration_catalog.py

### Task 2.2: API Extraction from RPG/COBOL Programs

Owner: Application Modernization Architect
Duration: 6 weeks
Acceptance Criteria:

RPG EXPORT procedures identified (candidates for REST API wrapping)
COBOL CALL interfaces documented (parameter lists, return codes)
Business logic complexity assessed (can be extracted vs. tightly coupled to AS400 runtime)
API specification generated (OpenAPI 3.0 for top 10 high-volume interfaces)

Execution: # scripts/2.2_api_extraction_analysis.py

### Task 2.3: Dependency Matrix & Critical Path Analysis

Owner: Technical Program Manager
Duration: 2 weeks
Acceptance Criteria:

NxN dependency matrix generated (app-to-app, app-to-integration, integration-to-external)
Critical path identified (longest chain of dependencies blocking migration)
Circular dependencies flagged (requires simultaneous cutover or feature toggle)
Wave grouping optimized (minimize cross-wave dependencies)

Execution: # scripts/2.3_dependency_matrix.py

### Task 2.4: IBM MQ to Pub/Sub Migration Strategy

Owner: Messaging Architect
Duration: 4 weeks
Acceptance Criteria:

MQ queue/topic inventory with subscriber mappings
Dual-publish strategy documented (MQ + Pub/Sub during cutover)
Message format compatibility ensured (MQ headers → Pub/Sub attributes)
Pub/Sub delivery guarantees validated (exactly-once vs. at-least-once)
Rollback procedure defined (revert to MQ if Pub/Sub fails)

Execution: scripts/2.4_ibm-mq_pub-sub_migration.md
