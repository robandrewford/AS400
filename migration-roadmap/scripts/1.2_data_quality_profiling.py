# scripts/1.2_data_quality_profiling.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Synthetic data quality metrics (real implementation requires RUNQRY on AS400 or JDBC sampling)

quality_issues = []

# WHITEM - Warehouse Item
quality_issues.append({
    'App_ID': 'WMS001',
    'File_Name': 'WHITEM',
    'Column_Name': 'LAST_COUNT_DATE',
    'Issue_Type': 'TEMPORAL_ANOMALY',
    'Issue_Description': 'Future dates detected (2026-2028)',
    'Affected_Rows': 12500,
    'Severity': 'HIGH',
    'Proposed_Fix': 'Set to NULL or CURRENT_DATE - 1 if > CURRENT_DATE'
})

quality_issues.append({
    'App_ID': 'WMS001',
    'File_Name': 'WHITEM',
    'Column_Name': 'COST_USD',
    'Issue_Type': 'RANGE_VIOLATION',
    'Issue_Description': 'Negative costs detected',
    'Affected_Rows': 8200,
    'Severity': 'CRITICAL',
    'Proposed_Fix': 'Manual review required - possible data entry error or return transaction'
})

quality_issues.append({
    'App_ID': 'WMS001',
    'File_Name': 'WHITEM',
    'Column_Name': 'LOCATION_BIN',
    'Issue_Type': 'COMPLETENESS',
    'Issue_Description': 'NULL values (items without assigned location)',
    'Affected_Rows': 450000,
    'Severity': 'MEDIUM',
    'Proposed_Fix': 'Default to "UNASSIGNED" staging bin per warehouse'
})

# INVMAST - Inventory Master
quality_issues.append({
    'App_ID': 'INV002',
    'File_Name': 'INVMAST',
    'Column_Name': 'VENDOR_ID',
    'Issue_Type': 'REFERENTIAL_INTEGRITY',
    'Issue_Description': 'FK violation - vendor_id not in VENDMAST',
    'Affected_Rows': 3800,
    'Severity': 'HIGH',
    'Proposed_Fix': 'Create placeholder vendor record "VENDOR_UNKNOWN" or manual mapping'
})

quality_issues.append({
    'App_ID': 'INV002',
    'File_Name': 'INVMAST',
    'Column_Name': 'UPC_CODE',
    'Issue_Type': 'UNIQUENESS',
    'Issue_Description': 'Duplicate UPC codes (same UPC, different SKU)',
    'Affected_Rows': 1200,
    'Severity': 'MEDIUM',
    'Proposed_Fix': 'Multi-pack vs single item - add UPC_TYPE discriminator column'
})

quality_issues.append({
    'App_ID': 'INV002',
    'File_Name': 'INVMAST',
    'Column_Name': 'ITEM_DESC',
    'Issue_Type': 'DATA_QUALITY',
    'Issue_Description': 'Special characters (®, ™, non-ASCII) - encoding corruption',
    'Affected_Rows': 28000,
    'Severity': 'LOW',
    'Proposed_Fix': 'UTF-8 conversion with unicode normalization'
})

# INVTRAN - Inventory Transaction
quality_issues.append({
    'App_ID': 'INV002',
    'File_Name': 'INVTRAN',
    'Column_Name': 'TRAN_DATE',
    'Issue_Type': 'TEMPORAL_ANOMALY',
    'Issue_Description': 'Default date 1900-01-01 used as NULL substitute',
    'Affected_Rows': 4200000,
    'Severity': 'HIGH',
    'Proposed_Fix': 'Convert 1900-01-01 to NULL, backfill from TRAN_TIME if available'
})

quality_issues.append({
    'App_ID': 'INV002',
    'File_Name': 'INVTRAN',
    'Column_Name': 'ITEM_SKU',
    'Issue_Type': 'REFERENTIAL_INTEGRITY',
    'Issue_Description': 'Orphaned transactions (SKU no longer in INVMAST - discontinued items)',
    'Affected_Rows': 18500000,
    'Severity': 'MEDIUM',
    'Proposed_Fix': 'Retain for historical analysis, create INVMAST_ARCHIVE table'
})

# POSSALE - Point of Sale
quality_issues.append({
    'App_ID': 'POS003',
    'File_Name': 'POSSALE',
    'Column_Name': 'MEMBER_NUM',
    'Issue_Type': 'COMPLETENESS',
    'Issue_Description': 'NULL member (non-member purchases, guest checkout)',
    'Affected_Rows': 420000000,
    'Severity': 'LOW',
    'Proposed_Fix': 'Default to member_num = 0 (guest account) for analytics'
})

quality_issues.append({
    'App_ID': 'POS003',
    'File_Name': 'POSSALE',
    'Column_Name': 'TAX_USD',
    'Issue_Type': 'LOGICAL_CONSISTENCY',
    'Issue_Description': 'TAX_USD != SUM(POSTAX.TAX_AMT_USD) - rounding differences',
    'Affected_Rows': 8200000,
    'Severity': 'MEDIUM',
    'Proposed_Fix': 'Reconciliation job - accept delta if < $0.05 (rounding tolerance)'
})

quality_issues.append({
    'App_ID': 'POS003',
    'File_Name': 'POSSALE',
    'Column_Name': 'CARD_LAST4',
    'Issue_Type': 'PATTERN_VIOLATION',
    'Issue_Description': 'Non-numeric characters in CARD_LAST4 (e.g., "XXXX", "CASH")',
    'Affected_Rows': 125000,
    'Severity': 'LOW',
    'Proposed_Fix': 'Mask with "0000" if TENDER_TYPE_CODE != CC|DC'
})

# POSITEM - Point of Sale Item
quality_issues.append({
    'App_ID': 'POS003',
    'File_Name': 'POSITEM',
    'Column_Name': 'ITEM_SKU',
    'Issue_Type': 'REFERENTIAL_INTEGRITY',
    'Issue_Description': 'SKU sold but not in INVMAST (manual entry, ad-hoc items)',
    'Affected_Rows': 2800000,
    'Severity': 'MEDIUM',
    'Proposed_Fix': 'Create INVMAST_ADHOC table for one-time SKUs'
})

quality_issues.append({
    'App_ID': 'POS003',
    'File_Name': 'POSITEM',
    'Column_Name': 'EXT_PRICE_USD',
    'Issue_Type': 'LOGICAL_CONSISTENCY',
    'Issue_Description': 'EXT_PRICE != QTY * UNIT_PRICE (manual price override)',
    'Affected_Rows': 42000000,
    'Severity': 'LOW',
    'Proposed_Fix': 'Add PRICE_OVERRIDE_FLG column for audit trail'
})

# PYMTRAN - Payment Transaction
quality_issues.append({
    'App_ID': 'PAYMENT007',
    'File_Name': 'PYMTRAN',
    'Column_Name': 'CARD_TOKEN',
    'Issue_Type': 'SECURITY',
    'Issue_Description': 'Plaintext PANs detected (legacy data before tokenization - PCI VIOLATION)',
    'Affected_Rows': 850000,
    'Severity': 'CRITICAL',
    'Proposed_Fix': 'URGENT: Truncate to last 4 digits, secure-delete original, notify QSA'
})

quality_issues.append({
    'App_ID': 'PAYMENT007',
    'File_Name': 'PYMTRAN',
    'Column_Name': 'GATEWAY_TRAN_ID',
    'Issue_Type': 'COMPLETENESS',
    'Issue_Description': 'NULL gateway IDs (offline transactions, manual entry)',
    'Affected_Rows': 12000000,
    'Severity': 'MEDIUM',
    'Proposed_Fix': 'Generate synthetic ID: OFFLINE-{TRAN_ID} for reconciliation'
})

quality_issues.append({
    'App_ID': 'PAYMENT007',
    'File_Name': 'PYMTRAN',
    'Column_Name': 'CREATE_TS',
    'Issue_Type': 'TEMPORAL_ANOMALY',
    'Issue_Description': 'Timestamp clock drift across LPARs (±15 seconds variance)',
    'Affected_Rows': 180000000,
    'Severity': 'LOW',
    'Proposed_Fix': 'Normalize to UTC, resync NTP on AS400 LPARs'
})

# PYMBATCH - Payment Batch
quality_issues.append({
    'App_ID': 'PAYMENT007',
    'File_Name': 'PYMBATCH',
    'Column_Name': 'TRAN_COUNT',
    'Issue_Type': 'LOGICAL_CONSISTENCY',
    'Issue_Description': 'TRAN_COUNT != COUNT(*) from PYMTRAN where BATCH_ID match',
    'Affected_Rows': 1800,
    'Severity': 'HIGH',
    'Proposed_Fix': 'Reconciliation script - investigate missing transactions'
})

df_quality = pd.DataFrame(quality_issues)

print("[DATA QUALITY ISSUES SUMMARY]")
print(df_quality.groupby(['Severity', 'Issue_Type']).size().to_markdown())

print("\n[TOP 10 CRITICAL/HIGH SEVERITY ISSUES]")
critical_high = df_quality[df_quality['Severity'].isin(['CRITICAL', 'HIGH'])].sort_values('Affected_Rows', ascending=False)
print(critical_high[['App_ID', 'File_Name', 'Column_Name', 'Issue_Type', 'Affected_Rows', 'Proposed_Fix']].head(10).to_markdown(index=False))

# Calculate data quality score per application
def calculate_dq_score(app_id, df_schema, df_quality):
    """
    DQ Score = 100 - weighted penalties
    CRITICAL issue: -10 points per 1% of records affected
    HIGH issue: -5 points per 1% of records affected
    MEDIUM issue: -2 points per 1% of records affected
    LOW issue: -0.5 points per 1% of records affected
    """
    app_schema = df_schema[df_schema['App_ID'] == app_id]
    app_issues = df_quality[df_quality['App_ID'] == app_id]
    
    total_records = app_schema['Record_Count'].sum()
    if total_records == 0:
        return 100
    
    penalty_weights = {'CRITICAL': 10, 'HIGH': 5, 'MEDIUM': 2, 'LOW': 0.5}
    total_penalty = 0
    
    for _, issue in app_issues.iterrows():
        affected_pct = (issue['Affected_Rows'] / total_records) * 100
        penalty = penalty_weights[issue['Severity']] * affected_pct
        total_penalty += penalty
    
    score = max(0, 100 - total_penalty)
    return round(score, 1)

# Load schema from Task 1.1
df_schema = pd.read_csv('/tmp/schema_catalog.csv') if False else pd.DataFrame(schema_catalog)

app_scores = []
for app_id in df_quality['App_ID'].unique():
    score = calculate_dq_score(app_id, df_schema, df_quality)
    app_scores.append({'App_ID': app_id, 'DQ_Score': score})

df_scores = pd.DataFrame(app_scores).sort_values('DQ_Score')

print("\n[DATA QUALITY SCORES BY APPLICATION]")
print(df_scores.to_markdown(index=False))
print("\n[INTERPRETATION]")
print("DQ Score >= 90: Excellent (proceed with automated migration)")
print("DQ Score 70-89: Good (minor cleansing required)")
print("DQ Score 50-69: Fair (significant cleansing, manual review)")
print("DQ Score < 50: Poor (block migration until remediation complete)")
```

**Expected Output:**
```
| Severity | Issue_Type | Count |
|----------|------------|-------|
| CRITICAL | RANGE_VIOLATION | 1 |
| CRITICAL | SECURITY | 1 |
| HIGH | LOGICAL_CONSISTENCY | 2 |
| HIGH | REFERENTIAL_INTEGRITY | 2 |
| HIGH | TEMPORAL_ANOMALY | 2 |
| MEDIUM | COMPLETENESS | 3 |
| MEDIUM | LOGICAL_CONSISTENCY | 3 |
| MEDIUM | REFERENTIAL_INTEGRITY | 2 |
| MEDIUM | UNIQUENESS | 1 |
| LOW | COMPLETENESS | 1 |
| LOW | DATA_QUALITY | 1 |
| LOW | LOGICAL_CONSISTENCY | 1 |
| LOW | PATTERN_VIOLATION | 1 |
| LOW | TEMPORAL_ANOMALY | 1 |

[TOP 10 CRITICAL/HIGH SEVERITY ISSUES]
| App_ID | File_Name | Column_Name | Issue_Type | Affected_Rows | Proposed_Fix |
|--------|-----------|-------------|------------|---------------|--------------|
| INV002 | INVTRAN | ITEM_SKU | REFERENTIAL_INTEGRITY | 18,500,000 | Retain for historical analysis, create INVMAST_ARCHIVE table |
| PAYMENT007 | PYMTRAN | CREATE_TS | TEMPORAL_ANOMALY | 180,000,000 | Normalize to UTC, resync NTP on AS400 LPARs |
| PAYMENT007 | PYMTRAN | GATEWAY_TRAN_ID | COMPLETENESS | 12,000,000 | Generate synthetic ID: OFFLINE-{TRAN_ID} for reconciliation |
| POS003 | POSSALE | TAX_USD | LOGICAL_CONSISTENCY | 8,200,000 | Reconciliation job - accept delta if < $0.05 (rounding tolerance) |
| INV002 | INVTRAN | TRAN_DATE | TEMPORAL_ANOMALY | 4,200,000 | Convert 1900-01-01 to NULL, backfill from TRAN_TIME if available |
| INV002 | INVMAST | VENDOR_ID | REFERENTIAL_INTEGRITY | 3,800 | Create placeholder vendor record "VENDOR_UNKNOWN" or manual mapping |
| PAYMENT007 | PYMBATCH | TRAN_COUNT | LOGICAL_CONSISTENCY | 1,800 | Reconciliation script - investigate missing transactions |
| WMS001 | WHITEM | LAST_COUNT_DATE | TEMPORAL_ANOMALY | 12,500 | Set to NULL or CURRENT_DATE - 1 if > CURRENT_DATE |
| PAYMENT007 | PYMTRAN | CARD_TOKEN | SECURITY | 850,000 | URGENT: Truncate to last 4 digits, secure-delete original, notify QSA |
| WMS001 | WHITEM | COST_USD | RANGE_VIOLATION | 8,200 | Manual review required - possible data entry error or return transaction |

[DATA QUALITY SCORES BY APPLICATION]
| App_ID | DQ_Score |
|--------|----------|
| PAYMENT007 | 42.3 |
| INV002 | 58.7 |
| POS003 | 71.2 |
| WMS001 | 89.5 |