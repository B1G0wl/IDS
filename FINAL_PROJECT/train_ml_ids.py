#!/usr/bin/env python3
"""
train_ml_ids.py
---------------
Trains a Machine Learning Intrusion Detection System using engineered flow features.

Usage:
    python3 train_ml_ids.py flows_features.csv

Output:
    - ml_model.pkl          (trained model)
    - predictions.csv       (actual vs predicted labels)
    - Console metrics (accuracy, precision, recall, F1, confusion matrix)
"""

import sys
import pandas as pd
import numpy as np
import time
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

def now():
    return time.strftime("%H:%M:%S")

if len(sys.argv) < 2:
    print("Usage: python3 train_ml_ids.py flows_features.csv")
    sys.exit(1)

INPUT_FILE = sys.argv[1]
MODEL_FILE = "ml_model.pkl"
OUTPUT_PRED = "predictions.csv"

print(f"[{now()}] Reading dataset {INPUT_FILE} ...")
try:
    df = pd.read_csv(INPUT_FILE)
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

if 'label' not in df.columns:
    print("Dataset must have a 'label' column.")
    sys.exit(1)

print(f"[{now()}] Preprocessing dataset ...")
# Encode categorical columns if needed
for col in ['src', 'dst']:
    df[col] = df[col].astype(str)
    df[col] = df[col].apply(lambda x: int(abs(hash(x))) % (10 ** 6))  # hash to numeric

# Separate features and labels
X = df.drop(columns=['label'])
y = df['label']

# Label encode y if categorical
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split dataset
print(f"[{now()}] Splitting data (80% train / 20% test) ...")
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"[{now()}] Training Random Forest model ...")
rf = RandomForestClassifier(
    n_estimators=150,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)
rf.fit(X_train, y_train)

print(f"[{now()}] Evaluating model ...")
y_pred = rf.predict(X_test)

acc = accuracy_score(y_test, y_pred)
print(f"\n[Accuracy] {acc:.4f}")

print("\n[Classification Report]")
print(classification_report(y_test, y_pred, target_names=le.classes_))

print("\n[Confusion Matrix]")
print(confusion_matrix(y_test, y_pred))

print(f"[{now()}] Saving model to {MODEL_FILE} ...")
joblib.dump({'model': rf, 'scaler': scaler, 'label_encoder': le}, MODEL_FILE)

print(f"[{now()}] Generating predictions file {OUTPUT_PRED} ...")
pred_df = pd.DataFrame({
    'actual_label': le.inverse_transform(y_test),
    'predicted_label': le.inverse_transform(y_pred)
})
pred_df.to_csv(OUTPUT_PRED, index=False)

print(f"[{now()}] Done. Model and predictions saved successfully.")
