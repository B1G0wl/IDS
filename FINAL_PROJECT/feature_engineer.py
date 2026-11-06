#!/usr/bin/env python3
"""
feature_engineer.py
-------------------
Reads synth_flows.csv (flow-level dataset) and computes advanced IDS features.

Usage:
    python3 feature_engineer.py flows_synthetic.csv

Output:
    flows_features.csv
"""

import sys
import pandas as pd
import numpy as np
import time
from collections import defaultdict

def now():
    return time.strftime("%H:%M:%S")

if len(sys.argv) < 2:
    print("Usage: python3 feature_engineer.py synth_flows.csv")
    sys.exit(1)

INPUT_FILE = sys.argv[1]
OUTPUT_FILE = "flows_features.csv"

print(f"[{now()}] Reading {INPUT_FILE} ...")
try:
    df = pd.read_csv(INPUT_FILE)
except Exception as e:
    print(f"Error reading {INPUT_FILE}: {e}")
    sys.exit(1)

expected_cols = {'src','dst','duration','pkts','bytes','syn','label'}
if not expected_cols.issubset(set(df.columns)):
    print(f"Input CSV must have columns: {expected_cols}")
    sys.exit(1)

# Replace zero duration to avoid division errors
df['duration'] = df['duration'].replace(0, 1e-6)

print(f"[{now()}] Computing base flow features ...")
# Basic per-flow features
df['packet_rate'] = df['pkts'] / df['duration']
df['byte_rate'] = df['bytes'] / df['duration']
df['syn_ratio'] = df['syn'] / df['pkts'].replace(0, np.nan)
df['mean_pkt'] = df['bytes'] / df['pkts'].replace(0, np.nan)
df['std_pkt'] = df['mean_pkt'] * 0.2  # placeholder std estimate

# Fill NaNs
df = df.fillna(0)

print(f"[{now()}] Aggregating per-source statistics (advanced features) ...")
grouped = df.groupby('src').agg(
    total_flows_per_src=('dst','count'),
    distinct_dst_per_src=('dst', pd.Series.nunique),
    avg_bytes_per_src=('bytes','mean'),
    avg_pkts_per_src=('pkts','mean'),
    avg_duration_per_src=('duration','mean')
).reset_index()

# Merge back to main dataframe
df = df.merge(grouped, on='src', how='left')

print(f"[{now()}] Normalizing heavy-tailed columns ...")
# Apply log transformation to handle large ranges
for col in ['bytes', 'pkts', 'duration', 'packet_rate', 'byte_rate', 
            'avg_bytes_per_src', 'avg_pkts_per_src']:
    df[f'log_{col}'] = np.log1p(df[col])

print(f"[{now()}] Creating heuristic flags ...")
# Simple heuristics (for rule-based hints later)
df['is_long_flow'] = (df['duration'] > df['duration'].median()).astype(int)
df['is_high_rate'] = (df['packet_rate'] > df['packet_rate'].quantile(0.75)).astype(int)
df['is_many_dsts'] = (df['distinct_dst_per_src'] > df['distinct_dst_per_src'].quantile(0.75)).astype(int)

print(f"[{now()}] Filling missing values and preparing final feature set ...")
df = df.fillna(0)

# Feature order: base + engineered + label
cols_to_keep = [
    'src','dst','duration','pkts','bytes','syn',
    'packet_rate','byte_rate','syn_ratio','mean_pkt','std_pkt',
    'total_flows_per_src','distinct_dst_per_src',
    'avg_bytes_per_src','avg_pkts_per_src','avg_duration_per_src',
    'log_bytes','log_pkts','log_duration','log_packet_rate','log_byte_rate',
    'is_long_flow','is_high_rate','is_many_dsts','label'
]

df_final = df[cols_to_keep]

print(f"[{now()}] Writing engineered features to {OUTPUT_FILE} ...")
df_final.to_csv(OUTPUT_FILE, index=False)
print(f"[{now()}] Done. Wrote {len(df_final)} rows and {len(df_final.columns)} columns.")
print(f"Output file: {OUTPUT_FILE}")
print(f"Columns generated: {list(df_final.columns)}")

print("\n[Summary by label]")
print(df_final['label'].value_counts())
