#!/usr/bin/env python3
"""
Verbose probe (port-scan) PCAP generator that prints progress.
"""
from scapy.all import IP, TCP, Ether, wrpcap
import random, time, sys

OUT_PCAP = "probe_scan.pcap"
OUT_CSV = "probe_flows.csv"

src_ip = "10.0.0.50"
dst_ip = "10.0.0.20"
start_ts = 0.0
# choose small list for quick test; change to range(1,1024) for a bigger scan
ports_to_scan = list(range(1, 256))
sleep_between = (0.001, 0.02)  # min/max spacing in seconds

def print_status(msg):
    print(msg)
    sys.stdout.flush()

try:
    from tqdm import trange
    use_tqdm = True
except Exception:
    use_tqdm = False

def main():
    print_status("Starting probe/port-scan generator.")
    total = len(ports_to_scan)
    print_status(f"Ports to scan: {total}. Generating SYN probe per port.")

    pkts = []
    ts = start_ts

    iterator = range(total)
    if use_tqdm:
        iterator = trange(total, desc="Scanning ports")

    for i in iterator:
        port = ports_to_scan[i]
        ts += random.uniform(*sleep_between)
        sport = random.randint(1024, 65535)
        p = Ether()/IP(src=src_ip, dst=dst_ip)/TCP(sport=sport, dport=port, flags="S")
        p.time = ts
        pkts.append(p)
        if (i+1) % 50 == 0 and not use_tqdm:
            print_status(f"Created {i+1}/{total} probe packets...")

    print_status(f"Generated {len(pkts)} probe packets. Writing {OUT_PCAP} ...")
    wrpcap(OUT_PCAP, pkts)
    print_status(f"Wrote {OUT_PCAP}")

    # write small CSV
    with open(OUT_CSV, "w", newline='') as f:
        import csv
        w = csv.writer(f)
        w.writerow(["src","dst","ports_scanned","start","end","pkts","label"])
        start = pkts[0].time if pkts else 0.0
        end = pkts[-1].time if pkts else 0.0
        w.writerow([src_ip, dst_ip, len(ports_to_scan), f"{start:.6f}", f"{end:.6f}", len(pkts), "Probe"])
    print_status(f"Wrote {OUT_CSV}. Done.")

if __name__ == "__main__":
    main()
