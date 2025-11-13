# scripts/0.2_dependency_analysis.py

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

df = pd.read_csv('/mnt/user-data/uploads/AS400_Inventory_Detailed.csv')

# Build dependency graph
G = nx.DiGraph()

for _, row in df.iterrows():
    app_id = row['App_ID']
    G.add_node(app_id, **row.to_dict())
    
    deps = row['Dependencies']
    if deps and deps != '*ALL*':
        for dep in deps.split(','):
            G.add_edge(dep.strip(), app_id)

# Check for cycles
try:
    cycles = list(nx.simple_cycles(G))
    if cycles:
        print(f"[ERROR] Circular dependencies detected: {cycles}")
        exit(1)
    else:
        print("[OK] No circular dependencies")
except:
    pass

# Topological sort (migration order)
try:
    topo_order = list(nx.topological_sort(G))
    print("\n[Migration Order (dependencies first)]:")
    for i, app in enumerate(topo_order, 1):
        print(f"{i:2d}. {app}")
except:
    print("[ERROR] Graph contains cycles, cannot determine order")

# Critical path (longest chain)
longest_path = nx.dag_longest_path(G)
print(f"\n[Critical Path]: {' -> '.join(longest_path)}")
print(f"[Critical Path Length]: {len(longest_path)} applications")

# Wave assignment (group independent apps)
waves = []
remaining = set(G.nodes())

wave_num = 1
while remaining:
    wave = []
    for node in list(remaining):
        predecessors = set(G.predecessors(node))
        if predecessors.issubset(set(G.nodes()) - remaining):
            wave.append(node)
    
    if not wave:
        print(f"[ERROR] Cannot form wave {wave_num}, dependency issue")
        break
    
    waves.append((wave_num, wave))
    remaining -= set(wave)
    wave_num += 1

print(f"\n[Migration Waves]: {len(waves)} waves identified")
for wave_num, apps in waves:
    print(f"Wave {wave_num}: {', '.join(apps)}")

# **Expected Critical Path:**

# VENDOR009 -> PURCH005 -> INV002 -> ALLOCATION025 -> WMS001 -> SHIP004 -> CARRIER008 -> EDI024
# (8 applications, must migrate sequentially)