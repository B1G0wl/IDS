#!/usr/bin/env python3
"""
visualize_ml_results.py
-----------------------
Visualizes the ML-based IDS performance and key features.

Usage:
    python3 visualize_ml_results.py flows_features.csv predictions.csv ml_model.pkl
"""

import sys
import time
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

def now():
    return time.strftime("%H:%M:%S")

if len(sys.argv) < 4:
    print("Usage: python3 visualize_ml_results.py flows_features.csv predictions.csv ml_model.pkl")
    sys.exit(1)

DATA_FILE = sys.argv[1]
PRED_FILE = sys.argv[2]
MODEL_FILE = sys.argv[3]

print(f"[{now()}] Loading files ...")
df = pd.read_csv(DATA_FILE)
preds = pd.read_csv(PRED_FILE)
model_bundle = joblib.load(MODEL_FILE)
model = model_bundle['model']
le = model_bundle['label_encoder']

print(f"[{now()}] Preparing data for visualization ...")
# Align labels
preds['actual_label'] = preds['actual_label'].astype(str)
preds['predicted_label'] = preds['predicted_label'].astype(str)

# === 1️⃣ FEATURE IMPORTANCE CHART ===
print(f"[{now()}] Plotting feature importance ...")
if hasattr(model, "feature_importances_"):
    feature_names = [c for c in df.columns if c != 'label']
    importances = model.feature_importances_

    fi = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values(by='Importance', ascending=False).head(15)

    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=fi, palette='viridis')
    plt.title("Top 15 Important Features for IDS Model")
    plt.tight_layout()
    plt.savefig("feature_importance.png")
    print(f"✅ Saved feature importance chart → feature_importance.png")
else:
    print("⚠️ Model does not support feature_importances_ (e.g., some XGBoost/NN variants).")

# === 2️⃣ CONFUSION MATRIX ===
print(f"[{now()}] Plotting confusion matrix ...")
labels = sorted(list(set(preds['actual_label']) | set(preds['predicted_label'])))
cm = confusion_matrix(preds['actual_label'], preds['predicted_label'], labels=labels)

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.title("Confusion Matrix")
plt.xlabel("Predicted Label")
plt.ylabel("Actual Label")
plt.tight_layout()
plt.savefig("confusion_matrix.png")
print(f"✅ Saved confusion matrix chart → confusion_matrix.png")

# === 3️⃣ TEXT SUMMARY ===
print(f"\n[{now()}] Classification Summary:")
print(classification_report(preds['actual_label'], preds['predicted_label'], digits=3))
print("\n✅ Visualization complete. Charts saved to current folder.")
