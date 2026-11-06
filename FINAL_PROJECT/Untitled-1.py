
"""
ids_dashboard_server.py — IDS Dashboard Server with History + Delete

Usage:
    python ids_dashboard_server.py flows_features.csv ml_model.pkl
"""

import sys, os, time, math, base64, json, warnings
from collections import defaultdict, deque
from datetime import datetime

import pandas as pd
import numpy as np
import joblib
from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from flask_socketio import SocketIO

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# ----------------------------------------------------------------------
# ARGUMENTS
# ----------------------------------------------------------------------
if len(sys.argv) < 3:
    print("Usage: python ids_dashboard_server.py <flows_features.csv> <ml_model.pkl>")
    sys.exit(1)

DATA_FILE, MODEL_FILE = sys.argv[1], sys.argv[2]

print(f"[+] Loading features from {DATA_FILE}")
sample_df = pd.read_csv(DATA_FILE, nrows=5)
feature_columns = [c for c in sample_df.columns if c != 'label']

print(f"[+] Loading model {MODEL_FILE}")
bundle = joblib.load(MODEL_FILE)
model = bundle['model']
scaler = bundle['scaler']
label_encoder = bundle['label_encoder']

# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------
def now_ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def hash_ip_to_int(ip):
    return int(abs(hash(str(ip))) % (10**6))

def payload_to_bytes(p):
    if p is None:
        return b''
    if isinstance(p, (bytes, bytearray)):
        return bytes(p)
    if isinstance(p, str):
        try:
            b = base64.b64decode(p, validate=True)
            if len(b) > 0:
                return b
        except Exception:
            pass
        return p.encode('utf-8', errors='ignore')
    return str(p).encode('utf-8', errors='ignore')

def entropy_bytes(b):
    if not b:
        return 0.0
    freq = {}
    for x in b:
        freq[x] = freq.get(x, 0) + 1
    L = len(b)
    ent = 0.0
    for v in freq.values():
        p = v / L
        ent -= p * math.log2(p)
    return ent

# ----------------------------------------------------------------------
# APP + STATE
# ----------------------------------------------------------------------
app = Flask(__name__, static_folder=None)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

MAX_HISTORY = 2000
recent_events = deque(maxlen=MAX_HISTORY)
HISTORY_FILE = "flow_history.jsonl"

# Load existing history from disk
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            try:
                flow = json.loads(line.strip())
                recent_events.appendleft(flow)
            except:
                pass
    print(f"[+] Loaded {len(recent_events)} old flow events.")

# ----------------------------------------------------------------------
# SOURCE STATS
# ----------------------------------------------------------------------
class SrcStats:
    def __init__(self):
        self.count = 0
        self.total_bytes = 0
        self.total_pkts = 0
        self.dst_set = set()
        self.total_duration = 0.0
    def add(self, dst, bytes_, pkts, duration):
        self.count += 1
        self.total_bytes += bytes_
        self.total_pkts += pkts
        self.dst_set.add(dst)
        self.total_duration += duration
    def to_dict(self):
        if self.count == 0:
            return dict(total_flows_per_src=0, distinct_dst_per_src=0,
                        avg_bytes_per_src=0.0, avg_pkts_per_src=0.0,
                        avg_duration_per_src=0.0)
        return dict(
            total_flows_per_src=self.count,
            distinct_dst_per_src=len(self.dst_set),
            avg_bytes_per_src=self.total_bytes / self.count,
            avg_pkts_per_src=self.total_pkts / self.count,
            avg_duration_per_src=self.total_duration / self.count
        )

src_stats = defaultdict(SrcStats)

# ----------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------
@app.route('/')
def root():
    return "✅ IDS server running! Go to /dashboard"
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pages/<page>')
def serve_static_page(page):  # <-- renamed function
    """Serve HTML fragments from static/pages"""
    return send_from_directory('static/pages', page)


@app.route('/dashboard')
def serve_dashboard():
    path = os.path.join(os.getcwd(), 'static')
    index_path = os.path.join(path, 'index.html')
    if not os.path.exists(index_path):
        return "Dashboard not found (place files in ./static/)", 500
    return send_from_directory(path, 'index.html')

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<page>')
def serve_page(page):
    """Serve static HTML pages like analysis.html, training.html, etc."""
    if not page.endswith('.html'):
        page += '.html'

    path = os.path.join(os.getcwd(), 'static')
    target_file = os.path.join(path, page)

    if os.path.exists(target_file):
        return send_from_directory(path, page)
    else:
        abort(404)


@app.route('/static/<path:filename>')
def static_files(filename):
    path = os.path.join(os.getcwd(), 'static')
    return send_from_directory(path, filename)

@app.route('/history', methods=['GET'])
def history():
    """Return all stored flow events."""
    return jsonify(list(recent_events))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear all saved flow records."""
    recent_events.clear()
    try:
        open(HISTORY_FILE, "w").close()  # truncate file
        print("[🧹] History cleared.")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

@app.route('/delete_flow', methods=['POST'])
def delete_flow():
    """Delete one flow by timestamp+src+dst."""
    data = request.get_json()
    uid = data.get("uid")
    if not uid:
        return {"error": "Missing uid"}, 400

    kept = []
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            try:
                flow = json.loads(line)
                this_uid = f"{flow.get('ts')}|{flow.get('src')}|{flow.get('dst')}"
                if this_uid != uid:
                    kept.append(flow)
            except:
                pass

    with open(HISTORY_FILE, "w") as f:
        for k in kept:
            f.write(json.dumps(k) + "\n")

    # Also remove from memory
    global recent_events
    recent_events = deque([x for x in kept], maxlen=MAX_HISTORY)
    print(f"[🗑️] Deleted flow: {uid}")
    return {"ok": True, "deleted": uid}

@app.route('/ingest', methods=['POST'])
def ingest():
    """Receive flow data and classify it."""
    try:
        flow = request.get_json(force=True)
        src = str(flow.get('src', '0.0.0.0'))
        dst = str(flow.get('dst', '0.0.0.0'))
        pkts = int(flow.get('pkts', 0))
        bytes_ = int(flow.get('bytes', 0))
        duration = float(flow.get('duration', 0.0))
        syn = int(flow.get('syn', 0))

        payload_b = payload_to_bytes(flow.get('payload', ''))
        payload_entropy = entropy_bytes(payload_b)
        payload_len = len(payload_b)

        packet_rate = pkts / (duration if duration > 0 else 1e-6)
        byte_rate = bytes_ / (duration if duration > 0 else 1e-6)
        mean_pkt = bytes_ / pkts if pkts > 0 else 0.0
        syn_ratio = syn / pkts if pkts > 0 else 0.0

        src_stats[src].add(dst, bytes_, pkts, duration)
        agg = src_stats[src].to_dict()

        row = {}
        for col in feature_columns:
            if col == 'src': row['src'] = hash_ip_to_int(src)
            elif col == 'dst': row['dst'] = hash_ip_to_int(dst)
            elif col == 'duration': row['duration'] = duration
            elif col == 'pkts': row['pkts'] = pkts
            elif col == 'bytes': row['bytes'] = bytes_
            elif col == 'syn': row['syn'] = syn
            elif col == 'packet_rate': row['packet_rate'] = packet_rate
            elif col == 'byte_rate': row['byte_rate'] = byte_rate
            elif col == 'syn_ratio': row['syn_ratio'] = syn_ratio
            elif col == 'mean_pkt': row['mean_pkt'] = mean_pkt
            elif col == 'std_pkt': row['std_pkt'] = mean_pkt * 0.2
            elif col in agg: row[col] = agg[col]
            elif col.startswith('log_'):
                base = col[4:]; row[col] = math.log1p(row.get(base, 0.0))
            elif col == 'is_long_flow': row[col] = 1 if duration > 1.0 else 0
            elif col == 'is_high_rate': row[col] = 1 if packet_rate > 100 else 0
            elif col == 'is_many_dsts': row[col] = 1 if agg['distinct_dst_per_src'] > 5 else 0
            else: row[col] = 0.0

        X_scaled = scaler.transform(pd.DataFrame([row]))
        pred_idx = model.predict(X_scaled)
        pred_label = label_encoder.inverse_transform(pred_idx)[0]
        prob = float(np.max(model.predict_proba(X_scaled))) if hasattr(model, 'predict_proba') else 0.0

        event = dict(
            ts=now_ts(),
            src=src,
            dst=dst,
            pkts=pkts,
            bytes=bytes_,
            payload_bytes=payload_len,
            payload_entropy=payload_entropy,
            predicted_label=pred_label,
            prob=prob
        )

        recent_events.appendleft(event)
        socketio.emit("new_flow", event)

        # Save to file
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")

        print(f"[+] FLOW src={src} dst={dst} → {pred_label} ({prob:.2f})")

        return jsonify({"status": "ok", "predicted_label": pred_label, "prob": prob})

    except Exception as e:
        print("[ERROR] ingest:", e)
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------
if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 5000
    print(f"[+] IDS server started on {HOST}:{PORT}")
    socketio.run(app, host=HOST, port=PORT)
