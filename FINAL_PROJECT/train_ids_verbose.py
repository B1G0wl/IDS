#!/usr/bin/env python3
"""
train_ids_verbose.py

- Expects a CSV file: flows_labeled.csv or flows_synthetic.csv (default tries flows_labeled.csv then flows_synthetic.csv).
- CSV must contain: columns like ['src','dst','sport','dport','duration','pkts','bytes','syn','ack','fin','rst','payload_entropy', 'label']
  If some features are missing they will be synthesized or filled.
- Trains:
    (A) RandomForestClassifier for multiclass (normal/DoS/Probe/U2R) -- good baseline.
    (B) IsolationForest trained on 'normal' flows for U2R anomaly detection (optional).
- Outputs: rf_model.pkl, scaler.pkl, iso_model.pkl (if built).
- Prints classification report, confusion matrix and feature importances.
"""
import os, sys, time, csv, math
import numpy as np
import pandas as pd

def print_status(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

# -------- parameters (tweak) ----------
INPUT_FILES = ["flows_labeled.csv", "flows_synthetic.csv"]
OUT_RF = "rf_ids_model.pkl"
OUT_SCALER = "scaler.pkl"
OUT_ISO = "iso_model.pkl"
RANDOM_STATE = 42
TEST_SIZE = 0.25
BUILD_ISO_FOR_U2R = True
# features we will try to use (will adapt if missing)
REQ_FEATURES = [
    "duration","pkts","bytes","syn","ack","fin","rst","payload_entropy","packet_rate","byte_rate","mean_pkt","std_pkt"
]
# --------------------------------------

print_status("Starting training script.")

# find input file
input_file = None
for f in INPUT_FILES:
    if os.path.exists(f):
        input_file = f
        break

if not input_file:
    print_status("ERROR: No input CSV found. Please provide one of: " + ", ".join(INPUT_FILES))
    sys.exit(1)

print_status(f"Using input file: {input_file}")

# load
print_status("Loading CSV into pandas...")
df = pd.read_csv(input_file)
print_status(f"Loaded {len(df)} rows, columns: {list(df.columns)[:10]}...")

# Basic feature engineering: ensure required numeric features exist (create fallbacks)
print_status("Ensuring numeric features exist and creating fallback features if needed...")

# helper to safe column creation
def ensure_col(col, fallback_val=0.0):
    if col not in df.columns:
        print_status(f"  - Column '{col}' missing. Creating fallback with value {fallback_val}.")
        df[col] = fallback_val

# duration/ pkts / bytes
ensure_col("duration", 0.01)
ensure_col("pkts", 1)
ensure_col("bytes", 0)
ensure_col("syn", 0)
ensure_col("ack", 0)
ensure_col("fin", 0)
ensure_col("rst", 0)
# optional payload entropy
ensure_col("payload_entropy", 0.0)
# mean/std pkt sizes (create approximations if not present)
if "mean_pkt" not in df.columns:
    print_status("  - mean_pkt missing. Creating mean_pkt = bytes/pkts (safe).")
    df["mean_pkt"] = df["bytes"].replace(0,1) / df["pkts"].replace(0,1)
if "std_pkt" not in df.columns:
    print_status("  - std_pkt missing. Setting std_pkt = mean_pkt*0.5 (approx).")
    df["std_pkt"] = df["mean_pkt"] * 0.5

# packet_rate / byte_rate
if "packet_rate" not in df.columns:
    print_status("  - packet_rate missing. Creating packet_rate = pkts/duration (safe).")
    df["packet_rate"] = df["pkts"] / df["duration"].replace(0, 0.001)
if "byte_rate" not in df.columns:
    print_status("  - byte_rate missing. Creating byte_rate = bytes/duration (safe).")
    df["byte_rate"] = df["bytes"] / df["duration"].replace(0, 0.001)

# Fill NaNs
df.fillna(0, inplace=True)

# Labels: ensure 'label' exists
if "label" not in df.columns:
    print_status("ERROR: 'label' column not found in CSV. Aborting.")
    sys.exit(1)

# show label distribution
print_status("Label distribution:")
print(df['label'].value_counts().to_string())

# Define features to use (intersection of REQ_FEATURES and present columns)
features = [c for c in REQ_FEATURES if c in df.columns]
# also include packet_rate and byte_rate if present
for c in ["packet_rate","byte_rate","mean_pkt","std_pkt"]:
    if c in df.columns and c not in features:
        features.append(c)
print_status("Using features: " + ", ".join(features))

# Encode labels for RF (multiclass). We'll keep text labels for reporting.
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

X = df[features].values
y = df['label'].values

# If dataset has time column, consider a time-based split to avoid leakage; otherwise stratify
if 'start' in df.columns or 'timestamp' in df.columns or 'time' in df.columns:
    # prefer a time-based split if present
    time_col = 'start' if 'start' in df.columns else ('timestamp' if 'timestamp' in df.columns else 'time')
    print_status(f"Time column '{time_col}' detected — performing time-based split (train earlier, test later).")
    df_sorted = df.sort_values(time_col)
    cutoff_idx = int(len(df_sorted)*(1.0-TEST_SIZE))
    train_df = df_sorted.iloc[:cutoff_idx]
    test_df = df_sorted.iloc[cutoff_idx:]
    X_train = train_df[features].values
    y_train = train_df['label'].values
    X_test = test_df[features].values
    y_test = test_df['label'].values
else:
    print_status("Performing stratified random train/test split.")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y)

print_status(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}")

# Scale features
print_status("Scaling features with StandardScaler...")
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

# Train RandomForest (multiclass)
print_status("Training RandomForestClassifier (this may take a moment)...")
rf = RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=RANDOM_STATE, n_jobs=-1)
rf.fit(X_train_s, y_train)
print_status("RandomForest training complete.")

# Evaluate
print_status("Predicting on test set...")
y_pred = rf.predict(X_test_s)
print_status("Classification report:")
print(classification_report(y_test, y_pred, digits=4))
print_status("Confusion matrix:")
cm = confusion_matrix(y_test, y_pred, labels=rf.classes_)
print("labels:", list(rf.classes_))
print(cm)

# Feature importances
try:
    importances = rf.feature_importances_
    fi = sorted(zip(features, importances), key=lambda x: x[1], reverse=True)
    print_status("Top feature importances (feature:importance):")
    for f,imp in fi[:20]:
        print(f"  {f}: {imp:.4f}")
except Exception as e:
    print_status("Could not compute feature importances: " + str(e))

# Save model & scaler
print_status("Saving model and scaler to disk...")
import joblib
joblib.dump((rf, features), OUT_RF)
joblib.dump(scaler, OUT_SCALER)
print_status(f"Wrote {OUT_RF} and {OUT_SCALER}")

# Optional: build IsolationForest for anomaly detection on 'normal' only (for U2R)
if BUILD_ISO_FOR_U2R:
    try:
        print_status("Building IsolationForest for anomaly detection (train on 'normal' only)...")
        from sklearn.ensemble import IsolationForest
        normal_mask = (df['label'] == 'normal') | (df['label'] == 'benign')  # accept synonyms
        normal_df = df[normal_mask]
        if len(normal_df) < 20:
            print_status("Not enough normal samples to train IsolationForest (need ~20+). Skipping.")
        else:
            X_norm = normal_df[features].values
            X_norm_s = scaler.transform(X_norm)  # use same scaler
            iso = IsolationForest(contamination=0.001, behaviour='new', random_state=RANDOM_STATE)
            iso.fit(X_norm_s)
            joblib.dump(iso, OUT_ISO)
            print_status(f"Wrote isolation forest to {OUT_ISO}")
            # score test set and show anomaly fraction
            test_scores = iso.decision_function(X_test_s)
            test_pred = iso.predict(X_test_s)  # -1 anomaly, 1 normal
            n_anom = (test_pred == -1).sum()
            print_status(f"IsolationForest flagged {n_anom}/{len(test_pred)} test rows as anomalies (-1).")
    except Exception as e:
        print_status("IsolationForest stage failed: " + str(e))

print_status("All done. Next suggestions:")
print_status(" - Inspect false positives/negatives from classification_report to tune thresholds/features.")
print_status(" - Try XGBoost or LightGBM for better accuracy, or use SMOTE/class weights for imbalance.")
print_status(" - For U2R, consider host logs or training anomaly detectors on payload features.")
