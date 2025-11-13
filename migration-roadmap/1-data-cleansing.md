1-data-cleansing.md
Purpose: Establish data quality baseline, implement profiling and cleansing pipelines, define master data management strategy for GCP migration.
Pre-conditions

 0-discovery.md complete (25 applications inventoried)
 Compliance scope defined (PCI: 2 apps, SOX: 4 apps, PII: 5 apps)
 Data volume baseline: 20.3 TB current, 24.6 TB projected
 DB2/400 object catalog: 332 physical files, 1,064 logical files

Tasks
Task 1.1: DB2/400 Schema Extraction & Reverse Engineering
Owner: Database Architect
Duration: 2 weeks
Acceptance Criteria:

DDL extracted for all 332 physical files (PF) and 1,064 logical files (LF)
Join logical files converted to SQL VIEW syntax
Referential integrity constraints documented (PRIMARY KEY, FOREIGN KEY, CHECK)
DDS field-level metadata captured (COLHDG, TEXT, EDTCDE, EDTWRD)

Execution: # scripts/1.1_schema_extraction.py

Task 1.2: Data Quality Profiling & Anomaly Detection
Owner: Data Quality Engineer
Duration: 3 weeks
Acceptance Criteria:

Completeness score per column (% non-null)
Uniqueness validation (duplicate detection in PK/UK columns)
Domain integrity checks (pattern matching, range validation)
Referential integrity violations quantified (orphaned FK records)
Temporal anomalies flagged (future dates, year 1900 defaults, timestamp drift)

Execution: # scripts/1.2_data_quality_profiling.py


Task 1.3: Master Data Management (MDM) Strategy
Owner: Data Architect + Business Data Stewards
Duration: 4 weeks
Acceptance Criteria:

Golden record definition for: Item, Vendor, Member, Warehouse, Location
Data stewardship roles assigned (create/update/approve authority)
Survivorship rules documented (which source wins on conflict)
Match/merge algorithm defined (fuzzy matching thresholds)

Execution: # scripts/1.3_mdm_strategy.md


Task 1.4: Data Cleansing Pipeline (Apache Beam on Dataflow)
Owner: Data Engineer
Duration: 4 weeks
Acceptance Criteria:

Reusable Beam transforms for: NULL handling, date normalization, string trimming, encoding conversion
Validation rules implemented as Dataflow side inputs (configurable without code changes)
Bad records routed to Dead Letter Queue (DLQ) in GCS for manual review
Cleansing metrics published to Cloud Monitoring

Execution: # scripts/1.4_data_cleansing_pipeline.py (Apache Beam on Dataflow)

Task 1.5: Data Archival & Retention Policy
Owner: Compliance Officer + Storage Architect
Duration: 2 weeks
Acceptance Criteria:

Retention schedule per table (hot/warm/cold/archive tiers)
Legal hold process documented (litigation, audit, breach response)
GCS lifecycle policies configured (auto-transition to Coldline/Archive)
Secure deletion process for GDPR/CCPA right-to-be-forgotten

Execution: # scripts/1.5_retention_policy.py


Task 1.5: Data Archival & Retention Policy
Owner: Compliance Officer + Storage Architect
Duration: 2 weeks
Acceptance Criteria:

Retention schedule per table (hot/warm/cold/archive tiers)
Legal hold process documented (litigation, audit, breach response)
GCS lifecycle policies configured (auto-transition to Coldline/Archive)
Secure deletion process for GDPR/CCPA right-to-be-forgotten

Execution: # scripts/1.5_retention_policy.py
