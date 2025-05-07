import json
import sys
from datetime import datetime
from collections import defaultdict

def format_ts(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def load_logs(path):
    jobs = defaultdict(list)
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                jobid = entry.get("jobid")
                if jobid is not None:
                    jobs[jobid].append(entry)
            except json.JSONDecodeError:
                continue
    return jobs

def analyze_job(jobid, entries):
    entries = sorted(entries, key=lambda x: x["nowtm"])
    start = entries[0]["nowtm"]
    end = entries[-1]["nowtm"]
    total_sec = end - start

    max_files = 0
    last_bytes = 0

    for e in entries:
        bs = e.get("bsProgs", [{}])[0]
        max_files = max(max_files, bs.get("nfiles", 0))
        levels = bs.get("levels", [])
        if levels and "sofar_bytes" in levels[0]:
            last_bytes = max(last_bytes, levels[0]["sofar_bytes"])

    total_gb = last_bytes / 1024**3
    avg_MBps = (total_gb * 1024) / total_sec if total_sec > 0 else 0

    return {
        "jobid": jobid,
        "start": format_ts(start),
        "end": format_ts(end),
        "duration_sec": total_sec,
        "duration_min": total_sec / 60,
        "files": max_files,
        "data_gb": total_gb,
        "raw_bytes": last_bytes,
        "avg_MBps": avg_MBps
    }

def print_summary_table(jobs):
    print("\n📊 Job History Summary:\n")
    print(f"{'Job':<5} {'Start Time':<20} {'Duration(min)':>13} {'Files':>8} {'Data(GB)':>10} {'Avg MB/s':>10}")
    print("-" * 70)
    for jobid in sorted(jobs):
        summary = analyze_job(jobid, jobs[jobid])
        print(f"{summary['jobid']:<5} {summary['start']:<20} {summary['duration_min']:>13.1f} "
              f"{summary['files']:>8} {summary['data_gb']:>10.2f} {summary['avg_MBps']:>10.2f}")

def print_detailed_summary(jobs):
    print("\n📊 Per-Job Detailed Summaries:\n")
    for jobid in sorted(jobs):
        s = analyze_job(jobid, jobs[jobid])
        print(f"📊 Job Summary: Job ID {s['jobid']}")
        print(f"   📅 Start: {s['start']}")
        print(f"   📅 End:   {s['end']}")
        print(f"   ⏱️  Total time: {s['duration_sec']:.2f} sec ({s['duration_min']:.1f} min)")
        print(f"   💾 Total data: {s['data_gb']:.2f} GB")
        print(f"   🧮 Raw bytes:  {s['raw_bytes']}")
        print(f"   🚀 Avg throughput: {s['avg_MBps']:.3f} MB/s\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: python summarize_single_log.py <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]
    jobs = load_logs(log_file)
    if not jobs:
        print("❌ No job entries found.")
        return

    print_summary_table(jobs)
    print_detailed_summary(jobs)

if __name__ == "__main__":
    main()
