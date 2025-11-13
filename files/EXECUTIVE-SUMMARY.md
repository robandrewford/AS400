# Executive Summary: AS400 → GCP Migration

**Organization:** Costco Wholesale Corporation  
**Date:** November 14, 2025  
**Status:** Phase 6-7 In Progress (43% Complete)

---

## Migration Overview

Costco is executing an 18-month migration of 28 mission-critical applications from legacy IBM AS400 systems to Google Cloud Platform. The migration prioritizes business continuity, regulatory compliance, and zero-downtime cutover for customer-facing systems.

---

## Key Metrics

### Scale & Scope

- **Applications:** 28 (10 REFACTOR, 8 REHOST, 3 REPLATFORM, 5 RETAIN, 2 RETIRE)
- **Data Volume:** 20.3 TB current → 24.6 TB projected
- **Transaction Volume:** 45M daily POS transactions
- **Locations:** 850 warehouses globally
- **Legacy Code:** 145K SLOC (RPG, COBOL)

### Performance

- **Network Latency:** 4.2ms avg (Partner Interconnect)
- **API Response Time:** < 20ms p50 (microservices)
- **Throughput:** 4.68 Gbps sustained (93% of 5 Gbps capacity)
- **Availability Target:** 99.99% (52 min downtime/year)

### Cost

- **Total Budget:** $12.5M (18 months)
- **Spent to Date:** $5.38M (43%)
- **TCO Savings:** 30% ($3.5M/year by Year 3)
- **Projected Total:** $11.8M (5.6% under budget)

---

## Critical Decisions

### 1. Partner Interconnect vs Dedicated Interconnect

**Decision:** Partner Interconnect (5 Gbps via Equinix)  
**Rationale:**

- Cost savings: $73K over 3 years
- Faster provisioning: 4 weeks vs 8 weeks
- Adequate capacity: 5 Gbps > 3.85 Gbps peak requirement
- Vendor flexibility: Multi-cloud ready

### 2. PAYROLL019 Strategy

**Decision:** REFACTOR (custom Python solution)  
**Rejected:** Workday implementation  
**Rationale:**

- Cost: $850K (custom) vs $2.4M (Workday)
- Timeline: 6 months vs 18 months
- Control: Full customization for Costco's unique payroll rules
- Integration: Native GCP services (BigQuery, Cloud Functions)
- ROI: Break-even in 14 months vs 36 months

**Approval:** CFO signed off September 10, 2025

### 3. Zero-Downtime POS/Payment Cutover

**Decision:** Dual-write strategy with feature flags  
**Rationale:**

- Business requirement: Cannot shut down 850 warehouses
- Revenue at risk: $45M daily transactions
- Customer experience: No checkout disruption
- Technical approach: Write to AS400 + GCP simultaneously, gradual read-path switchover

**Risk Mitigation:** Instant rollback via API Gateway routing

### 4. Microservices Deployment Platform

**Decision:** Cloud Run over GKE  
**Rationale:**

- Operational simplicity: No Kubernetes cluster management
- Autoscaling: Built-in (1-500 instances)
- Cost: Pay-per-request (vs always-on GKE nodes)
- Team readiness: Lower learning curve
- Service count: < 20 services (GKE overkill)

### 5. Encryption Strategy

**Decision:** CMEK with Cloud KMS HSM for PCI data  
**Rationale:**

- PCI-DSS compliance: Requirement for cardholder data
- Key rotation: Automated 90-day rotation
- Audit trail: Immutable access logs
- Performance: Minimal latency impact (< 2ms)

---

## Phase Status

| Phase | Status | Completion | Key Deliverable |
|-------|--------|------------|-----------------|
| 0: Discovery | ✅ Complete | 100% | Application inventory, dependency graph |
| 1: Data Cleansing | ✅ Complete | 100% | PII/PCI remediation, schema mapping |
| 2: Integration Mapping | ✅ Complete | 100% | 347 integrations cataloged |
| 3: Strategy Selection | ✅ Complete | 100% | 7R framework application per app |
| 4: Security & IAM | ✅ Complete | 100% | VPC-SC perimeters, CMEK encryption |
| 5: Network Connectivity | ✅ Complete | 100% | Interconnect + HA VPN operational |
| 6: Data Migration | 🔄 In Progress | 71% | Wave 5 (POS/Payment) executing |
| 7: App Modernization | 🔄 In Progress | 60% | 5 microservices deployed |
| 8: DevOps Expansion | ⏳ Planned | 0% | CI/CD for all refactored apps |
| 9: Testing & Cutover | ⏳ Planned | 0% | UAT, performance testing |
| 10: Observability | ⏳ Planned | 0% | Monitoring dashboards, cost optimization |

**Overall Progress:** 43% complete, on schedule

---

## Compliance Status

### PCI-DSS (2 applications)

- **Status:** 90% ready
- **Applications:** PAYMENT007, POS003
- **Remaining:** ASV scans, penetration testing, QSA final audit
- **Timeline:** Q1 2026 audit scheduled
- **Risk:** LOW (HSM encryption deployed, quarterly scans ongoing)

### SOX (4 applications)

- **Status:** 95% ready
- **Applications:** ACCT010, AUDIT022, PAYROLL019, TIMECLK020
- **Remaining:** External auditor SOC 2 Type II report
- **Timeline:** Q2 2026 audit window
- **Risk:** LOW (segregation of duties enforced, immutable audit logs)

### GDPR (5 applications)

- **Status:** 85% ready
- **Applications:** MEMBER006, LOYALTY021, POS003, HR014, LEGAL027
- **Remaining:** DPA review of data processing agreements
- **Timeline:** Q1 2026 submission
- **Risk:** MEDIUM (right-to-be-forgotten implementation in progress)

---

## Critical Findings

### Security findings

1. **PCI Violation Discovered (Phase 1):** 2.4M plaintext credit cards in PYMTRAN table
   - **Action Taken:** Immediate encryption, incident reported to QSA
   - **Status:** Resolved, no customer impact, QSA satisfied with remediation

2. **SOD Violation Detected (Phase 4):** 3 users with conflicting roles (payroll + approval)
   - **Action Taken:** IAM policies corrected, automated violation detection deployed
   - **Status:** Resolved

### Performance findings

1. **BigQuery Query Latency (Phase 6):** Inventory balance queries 150ms (target: < 50ms)
   - **Action Taken:** Materialized views created, Redis caching layer added
   - **Status:** Optimized to 18ms

2. **Network Failover Time (Phase 5):** Initial tests showed 85-second failover (target: < 60s)
   - **Action Taken:** BFD fast detection enabled, BGP timers tuned
   - **Status:** Optimized to 47 seconds

### Application findings

1. **Allocation LP Solver Complexity (Phase 7):** ALLOCEXE001 has 9.8 complexity score
   - **Risk:** 45-day refactor timeline may extend to 60 days
   - **Mitigation:** Dedicated senior developer assigned, OR-Tools consultant engaged
   - **Status:** 20% complete, on track

---

## Business Impact

### Achieved Benefits

1. **Release Velocity:** 15-minute deployment cycle (vs 2-week AS400 release)
2. **API Economy:** 12 new APIs exposed for 3rd-party integrations
3. **Scalability:** Autoscale to 2x Black Friday peak (tested 100K req/sec)
4. **Disaster Recovery:** RPO < 1 minute, RTO < 5 minutes (vs 24-hour AS400)

### Projected Benefits (Year 3)

1. **Cost Savings:** 30% TCO reduction ($3.5M annually)
2. **Revenue Enablement:** $15M from new digital channels (e-commerce API integrations)
3. **Operational Efficiency:** 60% reduction in manual processes (automation)
4. **Innovation Speed:** 5x increase in feature release frequency

---

## Risk Register (Top 5)

| Risk | Impact | Probability | Status |
|------|--------|-------------|--------|
| **R-001: POS/Payment cutover failure** | CRITICAL | Low | Mitigated (dual-write + instant rollback) |
| **R-002: CDC replication lag > 5 min** | HIGH | Medium | Mitigated (5 Gbps Interconnect, monitoring) |
| **R-003: PCI non-compliance finding** | CRITICAL | Low | Mitigated (QSA involved, HSM encryption) |
| **R-006: PAYROLL ACH file error** | HIGH | Low | Mitigated (NACHA validation, dual approval) |
| **R-010: Cost overrun > $12.5M** | MEDIUM | Medium | Monitoring (weekly FinOps review) |

**Overall Risk Level:** MEDIUM (well-controlled)

---

## Timeline & Milestones

### Completed Milestones

- ✅ **Jun 2025:** Discovery complete, 28 apps inventoried
- ✅ **Aug 2025:** Data quality baseline established
- ✅ **Sep 2025:** PAYROLL019 refactor approved ($850K budget)
- ✅ **Oct 2025:** VPC-SC perimeters deployed (PCI, SOX zones)
- ✅ **Nov 2025:** Partner Interconnect operational (4.68 Gbps validated)

### Upcoming Milestones

- 🎯 **Dec 2025:** Wave 5 (POS/Payment) dual-write cutover - **CRITICAL**
- 🎯 **Jan 2026:** Payment Gateway microservice complete
- 🎯 **Feb 2026:** All data migration waves complete
- 🎯 **Mar 2026:** UAT with 150 business users
- 🎯 **Apr 2026:** Production cutover complete (all 28 apps)
- 🎯 **Nov 2026:** AS400 decommissioned, project closure

---

## Recommendations

### Immediate (This Week)

1. **Execute Wave 5 cutover** - Deploy dual-write for POS/Payment (850 warehouses)
2. **Accelerate Payment Gateway** - 40% remaining, critical path dependency
3. **Schedule QSA audit** - Q1 2026 PCI-DSS annual assessment

### Short-Term (1-3 Months)

1. **Complete Waves 6-7** - Finance and Reporting data migration
2. **Begin Phase 8** - Expand CI/CD to all 10 refactored applications
3. **Load testing** - Black Friday simulation (2x normal load)

### Medium-Term (3-6 Months)

1. **UAT execution** - 150 business users, 28 applications
2. **Cutover rehearsals** - 3 full dry runs before production
3. **Cost optimization** - Committed use discounts, rightsizing

### Long-Term (6+ Months)

1. **AS400 decommissioning** - License reclamation, archive to GCS
2. **Center of Excellence** - GCP best practices, internal training
3. **Continuous improvement** - FinOps, performance tuning, new features

---

## Conclusion

The AS400 → GCP migration is 43% complete and on track for November 2026 completion. All critical path items are progressing well, with Wave 5 (POS/Payment) dual-write cutover as the next major milestone.

**Key Success Factors:**

1. Early stakeholder engagement (CFO approved PAYROLL019 custom build)
2. Rigorous security posture (PCI/SOX/GDPR compliance embedded from Day 1)
3. Zero-downtime strategy for customer-facing systems
4. Strong partnership with Google Cloud (TAM + PSO support)

**Project Health:** 🟢 GREEN (on schedule, under budget, risks mitigated)

---

**Prepared by:** Migration Program Office  
**Date:** November 14, 2025  
**Next Review:** December 1, 2025 (Post-Wave 5 Cutover)

---

*For detailed technical specifications, see individual phase documents in the migration-roadmap folder.*
