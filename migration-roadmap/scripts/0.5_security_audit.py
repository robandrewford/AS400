# scripts/0.5_security_audit.py
import pandas as pd

df = pd.read_csv('/mnt/user-data/uploads/AS400_Inventory_Detailed.csv')

# Compliance framework mapping
compliance_map = {
    'PAYMENT007': ['PCI-DSS', 'SOX'],
    'POS003': ['PCI-DSS'],
    'MEMBER006': ['PII', 'GDPR'],
    'ACCT010': ['SOX'],
    'PAYROLL019': ['SOX', 'PII'],
    'AUDIT022': ['SOX', 'ISO-27001'],
    'SECURITY018': ['ISO-27001'],
    'LOYALTY021': ['PII'],
    'RETURNS016': ['PII'],
    'TIMECLK020': ['PII']
}

df['Compliance_Frameworks'] = df['App_ID'].map(compliance_map).fillna('').apply(
    lambda x: ','.join(x) if isinstance(x, list) else ''
)

# Data classification
def classify_data(row):
    app_id = row['App_ID']
    if app_id in ['PAYMENT007', 'POS003']:
        return 'PCI'
    elif app_id in ['MEMBER006', 'PAYROLL019', 'LOYALTY021', 'RETURNS016', 'TIMECLK020']:
        return 'PII'
    elif app_id in ['ACCT010', 'AUDIT022']:
        return 'SOX'
    else:
        return 'Internal'

df['Data_Classification'] = df.apply(classify_data, axis=1)

# Encryption requirements (at-rest, in-transit)
def encryption_requirement(classification):
    if classification in ['PCI', 'PII']:
        return 'AES-256 (at-rest), TLS 1.3 (in-transit)'
    elif classification == 'SOX':
        return 'AES-256 (at-rest), TLS 1.2+ (in-transit)'
    else:
        return 'AES-256 (at-rest recommended)'

df['Encryption_Requirement'] = df['Data_Classification'].map(encryption_requirement)

# GCP security controls mapping
def gcp_security_controls(classification):
    controls = ['VPC-SC', 'Cloud KMS', 'Cloud Audit Logs']
    if classification == 'PCI':
        controls.extend(['DLP API', 'Cloud HSM', 'VPC Service Controls'])
    elif classification == 'PII':
        controls.extend(['DLP API', 'Access Transparency'])
    elif classification == 'SOX':
        controls.extend(['Assured Workloads', 'Access Approval'])
    return ', '.join(controls)

df['GCP_Security_Controls'] = df['Data_Classification'].map(gcp_security_controls)

# Output compliance summary
compliance_summary = df[df['Compliance_Frameworks'] != ''][
    ['App_ID', 'App_Name', 'Compliance_Frameworks', 'Data_Classification', 'GCP_Security_Controls']
]

print("[COMPLIANCE-SCOPED APPLICATIONS]")
print(compliance_summary.to_markdown(index=False))

# AS400 security model documentation (synthetic baseline)
print("\n[CURRENT AS400 SECURITY MODEL]")
print("""
User Profile Classes:
- *SECOFR: 8 profiles (IT Security, Database Admin)
- *SECADM: 22 profiles (Application Owners)
- *PGMR: 180 profiles (Developers, Support)
- *USER: 4,200 profiles (Warehouse Staff, Finance, HR)

Authorization Lists:
- PAYDATA_AL: 12 authorized users (PAYROLL019, TIMECLK020)
- FINDATA_AL: 28 authorized users (ACCT010, PAYMENT007)
- PCIDATA_AL: 6 authorized users (PAYMENT007, POS003)
- WMSDATA_AL: 850 authorized users (WMS001, ALLOCATION025)

Exit Programs:
- QIBM_QCA_CHG_COMMAND: Custom audit for *SECOFR commands
- QIBM_QZDA_SQL1: SQL injection filter (blocks UNION, DROP if not in PGMR class)
- QIBM_QCA_RMT_COMMAND: Blocks remote CL execution except from approved IPs

Current Gaps:
- No MFA enforcement (password + green-screen only)
- Authorization lists not time-bound (no automatic expiration)
- Exit programs lack centralized logging (local spool files only)
- No data masking (developers see production PII/PCI)
""")
```

**Expected Output:**
```
| App_ID | App_Name | Compliance_Frameworks | Data_Classification | GCP_Security_Controls |
|--------|----------|----------------------|---------------------|----------------------|
| PAYMENT007 | Payment_Processing_Gateway | PCI-DSS,SOX | PCI | VPC-SC, Cloud KMS, Cloud Audit Logs, DLP API, Cloud HSM, VPC Service Controls |
| POS003 | Point_of_Sale_Transaction | PCI-DSS | PCI | VPC-SC, Cloud KMS, Cloud Audit Logs, DLP API, Cloud HSM, VPC Service Controls |
| MEMBER006 | Membership_Management | PII,GDPR | PII | VPC-SC, Cloud KMS, Cloud Audit Logs, DLP API, Access Transparency |
| ACCT010 | General_Ledger_Interface | SOX | SOX | VPC-SC, Cloud KMS, Cloud Audit Logs, Assured Workloads, Access Approval |
| PAYROLL019 | Employee_Payroll_Processing | SOX,PII | PII | VPC-SC, Cloud KMS, Cloud Audit Logs, DLP API, Access Transparency |