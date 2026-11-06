#!/usr/bin/env python3
"""
Verbose flow-level synthetic CSV generator for ML training.
Prints progress so you know counts as it generates many rows.
"""
import csv, random, sys, time

OUT_CSV = "flows_synthetic.csv"
N_normal = 2000   # reduce sizes for quick testing
N_dos = 50
N_probe = 50
N_u2r = 10

def print_status(msg):
    print(msg)
    sys.stdout.flush()

def sample_normal_flow():
    duration = random.expovariate(1/2.0) + 0.01
    pkts = max(1, int(random.gauss(10,5)))
    bytes_ = pkts * max(40, int(random.gauss(500,200)))
    syn = random.randint(0,2)
    return duration, pkts, bytes_, syn

def sample_dos_flow():
    duration = random.uniform(0.5, 20)
    pkts = int(random.uniform(1000, 10000))
    bytes_ = pkts * int(random.uniform(40,200))
    syn = int(pkts * random.uniform(0.6, 0.99))
    return duration, pkts, bytes_, syn

def sample_probe_flow():
    duration = random.uniform(1, 60)
    pkts = int(random.uniform(20, 500))
    bytes_ = pkts * int(random.uniform(40, 200))
    syn = int(pkts * random.uniform(0.4, 0.9))
    return duration, pkts, bytes_, syn

def sample_u2r_flow():
    duration = random.uniform(0.1, 30)
    pkts = int(random.uniform(1, 50))
    bytes_ = pkts * int(random.uniform(50, 1500))
    syn = random.randint(0,2)
    return duration, pkts, bytes_, syn

def main():
    print_status("Starting synthetic flow CSV generation.")
    total = N_normal + N_dos + N_probe + N_u2r
    print_status(f"Rows to create: {total} (normal={N_normal}, DoS={N_dos}, Probe={N_probe}, U2R={N_u2r})")
    created = 0
    start_time = time.time()

    with open(OUT_CSV,"w",newline='') as f:
        w = csv.writer(f)
        w.writerow(["src","dst","duration","pkts","bytes","syn","label"])
        # normal
        for i in range(N_normal):
            dur, pk, by, sy = sample_normal_flow()
            w.writerow([f"10.0.0.{random.randint(1,50)}", f"10.0.0.{random.randint(51,150)}", f"{dur:.3f}", pk, by, sy, "normal"])
            created += 1
            if created % 500 == 0:
                print_status(f"Created {created}/{total} rows...")

        for i in range(N_dos):
            dur, pk, by, sy = sample_dos_flow()
            w.writerow([f"172.16.0.{random.randint(1,50)}", "10.0.0.10", f"{dur:.3f}", pk, by, sy, "DoS"])
            created += 1

        for i in range(N_probe):
            dur, pk, by, sy = sample_probe_flow()
            w.writerow([f"192.168.1.{random.randint(2,150)}", "10.0.0.20", f"{dur:.3f}", pk, by, sy, "Probe"])
            created += 1

        for i in range(N_u2r):
            dur, pk, by, sy = sample_u2r_flow()
            w.writerow([f"10.1.0.{random.randint(2,100)}", "10.0.0.7", f"{dur:.3f}", pk, by, sy, "U2R"])
            created += 1

    elapsed = time.time() - start_time
    print_status(f"Wrote {OUT_CSV} rows={created} elapsed={elapsed:.2f}s. Done.")

if __name__ == "__main__":
    main()
