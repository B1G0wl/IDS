import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

def hash_ip_to_int(ip):
    """Convert an IP string to a reproducible integer"""
    return int(abs(hash(str(ip))) % (10**6))

# ----------------------------------------------------------------------
# Load your features CSV
# ----------------------------------------------------------------------
try:
    df = pd.read_csv("flows_features.csv")
except Exception:
    df = pd.DataFrame()

# ----------------------------------------------------------------------
# If empty or missing 'label', create dummy data
# ----------------------------------------------------------------------
if df.shape[0] == 0 or "label" not in df.columns:
    print("[i] Creating dummy dataset since flows_features.csv was empty or missing 'label'")
    df = pd.DataFrame({
        "src": ["10.0.0."+str(i) for i in range(10)],
        "dst": ["192.168.0."+str(i) for i in range(10)],
        "pkts": np.random.randint(1, 100, 10),
        "bytes": np.random.randint(100, 5000, 10),
        "duration": np.random.rand(10),
        "syn": np.random.randint(0, 3, 10),
        "packet_rate": np.random.rand(10)*50,
        "byte_rate": np.random.rand(10)*5000,
        "mean_pkt": np.random.rand(10)*100,
        "syn_ratio": np.random.rand(10),
        "label": np.random.choice(["benign","attack"], 10)
    })

# ----------------------------------------------------------------------
# Convert IP columns to integers
# ----------------------------------------------------------------------
if "src" in df.columns:
    df["src"] = df["src"].apply(hash_ip_to_int)
if "dst" in df.columns:
    df["dst"] = df["dst"].apply(hash_ip_to_int)

# ----------------------------------------------------------------------
# Prepare features and labels
# ----------------------------------------------------------------------
X = df.drop(columns=["label"])
y = df["label"]

scaler = StandardScaler().fit(X)
X_scaled = scaler.transform(X)
le = LabelEncoder().fit(y)

model = DecisionTreeClassifier().fit(X_scaled, le.transform(y))

bundle = {"model": model, "scaler": scaler, "label_encoder": le}
joblib.dump(bundle, "ml_model.pkl")

print("✅ Model retrained successfully with sklearn 1.7.2 and saved as ml_model.pkl")
