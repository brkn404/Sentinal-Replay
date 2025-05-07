import json
import sys
from datetime import datetime
from pathlib import Path

def parse_job_log(file_path, jobid_filter=None):
    with open(file_path, 'r') as f:
        lines = [json.loads(line.strip()) for line in f if line.strip()]
    if jobid_filter is not None:
        lines = [entry for entry in lines if entry.get("jobid") == jobid_filter]
    return sorted(lines, key=lambda x: x["nowtm"])

def format_timestamp(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def analyze_job(logs):
    previous = None
    results = []

    for entry in logs:
        jobid = entry["jobid"]
        nowtm = entry["nowtm"]

        total_bytes = 0
        total_files = 0
        total_dirs = 0

        for bs in entry.get("bsProgs", []):
            total_files += bs.get("nfiles", 0)
            total_dirs += bs.get("ndirs", 0)
            levels = bs.get("levels", [])
            if levels and "sofar_bytes" in levels[0]:
                total_bytes += levels[0]["sofar_bytes"]

        if total_bytes == 0:
            continue

        if previous:
            delta_time = nowtm - previous["nowtm"]
            delta_data = total_bytes - previous["data"]
            throughput = delta_data / delta_time / 1024**2 if delta_time > 0 else 0
        else:
            delta_time = 0
            throughput = 0

        results.append({
            "timestamp": format_timestamp(nowtm),
            "jobid": jobid,
            "elapsed_sec": delta_time,
            "files": total_files,
            "dirs": total_dirs,
            "sofar_gb": total_bytes / 1024**3,
            "raw_bytes": total_bytes,
            "throughput_MBps": throughput
        })

        previous = {
            "nowtm": nowtm,
            "data": total_bytes
        }

    return results

def summarize(results):
    if not results:
        print("❌ No entries found for the specified job ID.")
        return

    start_time = results[0]["timestamp"]
    end_time = results[-1]["timestamp"]
    total_time = sum(r["elapsed_sec"] for r in results[1:])
    total_bytes = results[-1]["raw_bytes"]
    total_gb = total_bytes / 1024**3
    avg_throughput = total_bytes / total_time / 1024**2 if total_time > 0 else 0

    print(f"\n📊 Job Summary:")
    print(f"   📅 Start: {start_time}")
    print(f"   📅 End:   {end_time}")
    print(f"   ⏱️  Total time: {total_time:.2f} sec ({total_time / 60:.1f} min)")
    print(f"   💾 Total data: {total_gb:.2f} GB")
    print(f"   🧮 Raw bytes:  {total_bytes}")
    print(f"   🚀 Avg throughput: {avg_throughput:.3f} MB/s")

def print_results(results):
    print("\n📈 Progress:")
    for r in results:
        print(f"{r['timestamp']} | Job {r['jobid']:>3} | Files: {r['files']:<5} | Dirs: {r['dirs']:<5} "
              f"| Data: {r['sofar_gb']:.3f} GB | Δt: {r['elapsed_sec']:>4} s | "
              f"Speed: {r['throughput_MBps']:>8.3f} MB/s")

def main():
    if len(sys.argv) < 3:
        print("Usage: python track_backup_job.py <job_log_file> <jobid>")
        sys.exit(1)

    log_file = sys.argv[1]
    try:
        jobid = int(sys.argv[2])
    except ValueError:
        print("❌ Job ID must be an integer.")
        sys.exit(1)

    if not Path(log_file).exists():
        print(f"❌ File not found: {log_file}")
        sys.exit(1)

    logs = parse_job_log(log_file, jobid)
    results = analyze_job(logs)
    print_results(results)
    summarize(results)

if __name__ == "__main__":
    main()
