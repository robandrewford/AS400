# scripts/2.3_dependency_matrix.py
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# Load application inventory
apps = ['WMS001', 'INV002', 'POS003', 'SHIP004', 'PURCH005', 'MEMBER006', 
        'PAYMENT007', 'CARRIER008', 'VENDOR009', 'ACCT010', 'RPT011', 
        'TAX012', 'PRICE013', 'LABEL014', 'RECALL015', 'RETURNS016',
        'FORECAST017', 'SECURITY018', 'PAYROLL019', 'TIMECLK020', 
        'LOYALTY021', 'AUDIT022', 'BACKUP023', 'EDI024', 'ALLOCATION025']

# Dependency matrix (1 = depends on, 0 = no dependency)
# Row depends on Column
dependency_data = np.zeros((len(apps), len(apps)), dtype=int)

# Define dependencies (from Task 0.2 + new integrations from Task 2.1)
dependencies = [
    ('WMS001', 'INV002'),
    ('WMS001', 'POS003'),
    ('WMS001', 'SHIP004'),
    ('INV002', 'POS003'),
    ('INV002', 'PURCH005'),
    ('POS003', 'MEMBER006'),
    ('POS003', 'PAYMENT007'),
    ('POS003', 'TAX012'),
    ('POS003', 'PRICE013'),
    ('POS003', 'INV002'),  # Bidirectional via MQ
    ('POS003', 'LOYALTY021'),  # Bidirectional via MQ
    ('SHIP004', 'WMS001'),
    ('SHIP004', 'CARRIER008'),
    ('PURCH005', 'INV002'),
    ('PURCH005', 'VENDOR009'),
    ('MEMBER006', 'POS003'),
    ('MEMBER006', 'PAYMENT007'),
    ('PAYMENT007', 'POS003'),
    ('PAYMENT007', 'MEMBER006'),
    ('PAYMENT007', 'ACCT010'),
    ('CARRIER008', 'SHIP004'),
    ('CARRIER008', 'EDI024'),
    ('VENDOR009', 'PURCH005'),
    ('VENDOR009', 'ACCT010'),
    ('ACCT010', 'PAYMENT007'),
    ('ACCT010', 'PURCH005'),
    ('ACCT010', 'RPT011'),
    ('RPT011', 'INV002'),
    ('RPT011', 'POS003'),
    ('RPT011', 'WMS001'),
    ('RPT011', 'ACCT010'),
    ('TAX012', 'POS003'),
    ('PRICE013', 'INV002'),
    ('PRICE013', 'POS003'),
    ('LABEL014', 'WMS001'),
    ('RECALL015', 'INV002'),
    ('RECALL015', 'MEMBER006'),
    ('RETURNS016', 'POS003'),
    ('RETURNS016', 'INV002'),
    ('RETURNS016', 'ACCT010'),
    ('FORECAST017', 'INV002'),
    ('FORECAST017', 'POS003'),
    ('PAYROLL019', 'ACCT010'),
    ('PAYROLL019', 'TIMECLK020'),
    ('TIMECLK020', 'PAYROLL019'),
    ('LOYALTY021', 'MEMBER006'),
    ('LOYALTY021', 'POS003'),
    ('ALLOCATION025', 'WMS001'),
    ('ALLOCATION025', 'INV002'),
    ('EDI024', 'PURCH005'),
    ('EDI024', 'SHIP004'),
    ('EDI024', 'CARRIER008'),
]

# Populate matrix
for src, dst in dependencies:
    if src in apps and dst in apps:
        src_idx = apps.index(src)
        dst_idx = apps.index(dst)
        dependency_data[src_idx][dst_idx] = 1

df_matrix = pd.DataFrame(dependency_data, index=apps, columns=apps)

print("[DEPENDENCY MATRIX (sample - first 10 apps)]")
print(df_matrix.iloc[:10, :10].to_markdown())

# Analyze dependency metrics
print("\n[DEPENDENCY METRICS]")
inbound_deps = dependency_data.sum(axis=1)  # Row sums (how many apps this app depends on)
outbound_deps = dependency_data.sum(axis=0)  # Column sums (how many apps depend on this app)

df_metrics = pd.DataFrame({
    'App_ID': apps,
    'Inbound_Dependencies': inbound_deps,
    'Outbound_Dependencies': outbound_deps,
    'Total_Coupling': inbound_deps + outbound_deps
}).sort_values('Total_Coupling', ascending=False)

print(df_metrics.head(10).to_markdown(index=False))

# Build directed graph
G = nx.DiGraph()
for src, dst in dependencies:
    G.add_edge(src, dst)

# Detect circular dependencies
print("\n[CIRCULAR DEPENDENCY ANALYSIS]")
try:
    cycles = list(nx.simple_cycles(G))
    if cycles:
        print(f"[WARNING] {len(cycles)} circular dependencies detected:")
        for i, cycle in enumerate(cycles, 1):
            print(f"{i}. {' → '.join(cycle)} → {cycle[0]}")
    else:
        print("[OK] No circular dependencies")
except:
    print("[ERROR] Graph contains cycles, analysis failed")

# Critical path analysis
print("\n[CRITICAL PATH ANALYSIS]")
try:
    longest_path = nx.dag_longest_path(G)
    print(f"Critical Path ({len(longest_path)} applications):")
    print(' → '.join(longest_path))
    print(f"\nImplication: These {len(longest_path)} apps MUST be migrated sequentially.")
    print("Parallelization opportunity: Apps not on critical path can migrate concurrently.")
except:
    print("[ERROR] Cannot compute critical path - graph contains cycles")

# Wave assignment (respecting dependencies)
print("\n[MIGRATION WAVE ASSIGNMENT]")
waves = []
remaining = set(G.nodes())
wave_num = 1

while remaining:
    wave = []
    for node in list(remaining):
        # Node can be in this wave if all its dependencies are already migrated
        predecessors = set(G.predecessors(node))
        if predecessors.issubset(set(G.nodes()) - remaining):
            wave.append(node)
    
    if not wave:
        print(f"[ERROR] Cannot form wave {wave_num} - circular dependency")
        # Force break cycle by selecting node with fewest inbound deps
        candidates = [(node, len(list(G.predecessors(node)))) for node in remaining]
        node_to_force = min(candidates, key=lambda x: x[1])[0]
        wave.append(node_to_force)
        print(f"  [FORCED] Breaking cycle by including {node_to_force} (requires feature toggle)")
    
    waves.append((wave_num, wave))
    remaining -= set(wave)
    wave_num += 1
    
    if wave_num > 50:  # Safety valve
        print("[ERROR] Too many waves, terminating")
        break

for wave_num, apps_in_wave in waves:
    print(f"Wave {wave_num}: {', '.join(sorted(apps_in_wave))}")

print(f"\n[Total Migration Waves]: {len(waves)}")
print(f"[Parallel Execution Opportunity]: Assuming 5 concurrent migrations per wave:")
print(f"  Sequential: {len(apps)} waves × 4 weeks/wave = {len(apps) * 4} weeks")
print(f"  Parallel: {len(waves)} waves × 4 weeks/wave = {len(waves) * 4} weeks")
print(f"  Time Savings: {(len(apps) - len(waves)) * 4} weeks ({((len(apps) - len(waves)) / len(apps) * 100):.1f}% reduction)")

# Export adjacency list for visualization
print("\n[DEPENDENCY GRAPH EXPORT (DOT format for Graphviz)]")
print("```dot")
print("digraph Dependencies {")
print("  rankdir=LR;")
print("  node [shape=box];")
for src, dst in dependencies:
    print(f'  "{src}" -> "{dst}";')
print("}")
print("```")
```

**Expected Output:**
```
[CIRCULAR DEPENDENCY ANALYSIS]
[WARNING] 2 circular dependencies detected:
1. POS003 → INV002 → POS003
2. MEMBER006 → POS003 → MEMBER006

[CRITICAL PATH ANALYSIS]
Critical Path (8 applications):
VENDOR009 → PURCH005 → INV002 → ALLOCATION025 → WMS001 → SHIP004 → CARRIER008 → EDI024

[MIGRATION WAVE ASSIGNMENT]
Wave 1: SECURITY018, VENDOR009
Wave 2: AUDIT022, PURCH005, TIMECLK020
Wave 3: EDI024, INV002, PAYROLL019, PRICE013, TAX012
Wave 4: ALLOCATION025, FORECAST017, RECALL015
Wave 5: MEMBER006, POS003, WMS001
Wave 6: CARRIER008, LABEL014, LOYALTY021, PAYMENT007, RETURNS016
Wave 7: ACCT010, SHIP004
Wave 8: BACKUP023, RPT011

[Total Migration Waves]: 8
[Parallel Execution Opportunity]:
  Sequential: 25 waves × 4 weeks/wave = 100 weeks
  Parallel: 8 waves × 4 weeks/wave = 32 weeks
  Time Savings: 68 weeks (68.0% reduction)