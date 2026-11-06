#!/usr/bin/env python3
"""
Verbose SYN-flood PCAP generator (writes PCAP locally, does NOT send packets).
Shows progress so you know it's running.
"""
from scapy.all import IP, TCP, Ether, Raw, wrpcap
import random, time, csv, sys, math

# --- Parameters (tweak for quick tests) ---
OUT_PCAP = "dos_syn_flood.pcap"
OUT_CSV = "dos_flows.csv"
duration = 5.0            # seconds of attack (set small to test)
pkts_per_sec = 500        # target avg pkts/sec (lower for quick test)
src_ip = "10.0.0.100"
dst_ip = "10.0.0.10"
dst_port = 80

# Progress helpers
def print_status(msg):
    print(msg)
    sys.stdout.flush()

# optional: try using tqdm if available
try:
    from tqdm import trange
    use_tqdm = True
except Exception:
    use_tqdm = False

def exp_interarrival(rate):
    # exponential inter-arrival (seconds) with safe lower bound
    return max(0.0001, random.expovariate(rate))

def main():
    print_status("Starting SYN-flood PCAP generator (verbose).")
    total_packets_est = int(max(1, duration * pkts_per_sec))
    print_status(f"Target duration={duration}s, target pkts/sec={pkts_per_sec}, estimated pkts={total_packets_est}")

    pkts = []
    ts = 0.0
    last_report = time.time()
    report_interval = 1.0  # seconds

    iterator = range(total_packets_est)
    if use_tqdm:
        iterator = trange(total_packets_est, desc="Generating pkts")

    for i in iterator:
        dt = exp_interarrival(pkts_per_sec)
        ts += dt
        sport = random.randint(1024, 65535)
        seq = random.randint(0, 0xFFFFFFFF)
        ip = IP(src=src_ip, dst=dst_ip)
        tcp = TCP(sport=sport, dport=dst_port, flags="S", seq=seq, window=1024)
        payload = Raw(load=b"")  # SYNs usually don't carry payload
        p = Ether()/ip/tcp/payload
        p.time = ts
        pkts.append(p)

        # periodic textual progress (in case tqdm not present)
        if not use_tqdm:
            now = time.time()
            if now - last_report >= report_interval:
                print_status(f"Generated {i+1}/{total_packets_est} packets (elapsed loop time {now-last_report:.1f}s).")
                last_report = now

    print_status(f"Finished generating {len(pkts)} packets. Writing pcap to {OUT_PCAP} ...")
    try:
        wrpcap(OUT_PCAP, pkts)
    except Exception as e:
        print_status("ERROR writing pcap: " + str(e))
        raise

    print_status("Writing summary CSV ...")
    try:
        with open(OUT_CSV, "w", newline='') as f:
            w = csv.writer(f)
            w.writerow(["src","dst","sport","dport","proto","start","end","pkts","bytes","label"])
            start_ts = pkts[0].time if pkts else 0.0
            end_ts = pkts[-1].time if pkts else 0.0
            total_bytes = sum(len(bytes(p)) for p in pkts)
            w.writerow([src_ip, dst_ip, "-", dst_port, "TCP", f"{start_ts:.6f}", f"{end_ts:.6f}", len(pkts), total_bytes, "DoS"])
    except Exception as e:
        print_status("ERROR writing CSV: " + str(e))
        raise

    print_status(f"Wrote {OUT_PCAP} packets={len(pkts)} bytes={total_bytes} and {OUT_CSV}")
    print_status("Done.")

if __name__ == "__main__":
    main()
