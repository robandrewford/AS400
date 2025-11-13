# scripts/0.1_portfolio_analysis.py
import pandas as pd
import hashlib
from datetime import datetime

def calculate_technical_debt_index(row):
    """
    TDI = (months_since_modified / 12) × (SLOC / 10000) × (dependency_count^1.5) × language_penalty
    """
    modified = datetime.strptime(row['Last_Modified_Date'], '%Y-%m-%d')
    age_years = (datetime(2025, 11, 12) - modified).days / 365.25
    
    dependency_count = len(row['Dependencies'].split(','))
    
    language_penalty = {
        'RPG_III': 2.5,  # Legacy, pre-ILE
        'RPG_IV': 1.8,   # Modern but niche
        'COBOL_400': 2.0,
        'CL': 1.5        # Scripting, easier to replace
    }
    
    tdi = (age_years) * (row['SLOC'] / 10000) * (dependency_count ** 1.5) * language_penalty[row['Source_Language']]
    return round(tdi, 2)

def assign_migration_strategy(row):
    """
    Decision matrix:
    - Critical + High TDI + Daily → REFACTOR (microservices)
    - Critical + Low TDI + Daily → REPLATFORM (containerize)
    - Non-critical + Weekly/Monthly → REHOST (lift-shift to Compute Engine)
    - Low usage + Old code → RETIRE (replace with SaaS)
    """
    is_critical = row['Critical_Business_Function'] == 'Y'
    tdi = row['Technical_Debt_Index']
    usage = row['Usage_Frequency']
    
    if not is_critical and usage in ['monthly', 'weekly'] and tdi > 15:
        return 'RETIRE'
    elif is_critical and tdi > 20 and usage == 'daily':
        return 'REFACTOR'
    elif is_critical and tdi <= 20 and usage == 'daily':
        return 'REPLATFORM'
    else:
        return 'REHOST'

# Load inventory
df = pd.read_csv('/mnt/user-data/uploads/AS400_Inventory_Detailed.csv')

# Calculate TDI
df['Technical_Debt_Index'] = df.apply(calculate_technical_debt_index, axis=1)

# Assign strategies
df['Migration_Strategy'] = df.apply(assign_migration_strategy, axis=1)

# Business criticality scoring (1=low, 5=critical)
df['Business_Criticality_Score'] = df.apply(
    lambda x: 5 if x['Critical_Business_Function'] == 'Y' and x['Usage_Frequency'] == 'daily' 
              else 4 if x['Critical_Business_Function'] == 'Y' 
              else 3 if x['Usage_Frequency'] == 'daily' 
              else 2, 
    axis=1
)

# Output
output = df[['App_ID', 'App_Name', 'Technical_Debt_Index', 'Business_Criticality_Score', 'Migration_Strategy']]
print(output.to_markdown(index=False))

# Checksum for validation
checksum = hashlib.sha256(output.to_csv(index=False).encode()).hexdigest()
print(f"\n[CHECKSUM: {checksum[:16]}]")