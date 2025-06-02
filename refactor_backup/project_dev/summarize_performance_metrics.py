import csv
import glob
import os
from statistics import mean, median, stdev, quantiles

METRICS_FILES = [
    "memory_usage_metrics.csv",
    "long_running_session_metrics.csv",
    "ai_service_timeout_metrics.csv",
]

REPORT_PATH = "project_dev/performance_metrics_report.md"


def summarize_csv(path):
    events = []
    latencies = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "latency" in row and row["latency"]:
                try:
                    lat = float(row["latency"])
                    latencies.append(lat)
                    events.append(row["event"])
                except Exception:
                    continue
    if not latencies:
        return None
    stats = {
        "count": len(latencies),
        "mean": mean(latencies),
        "median": median(latencies),
        "min": min(latencies),
        "max": max(latencies),
        "p95": quantiles(latencies, n=100)[94] if len(latencies) >= 20 else None,
        "stdev": stdev(latencies) if len(latencies) > 1 else 0.0,
        "events": events,
    }
    return stats

def main():
    report_lines = ["# Performance Metrics Summary\n"]
    for fname in METRICS_FILES:
        if not os.path.exists(fname):
            continue
        stats = summarize_csv(fname)
        if not stats:
            continue
        report_lines.append(f"## {fname}\n")
        report_lines.append(f"- Samples: {stats['count']}")
        report_lines.append(f"- Mean latency: {stats['mean']*1000:.2f} ms")
        report_lines.append(f"- Median latency: {stats['median']*1000:.2f} ms")
        report_lines.append(f"- Min: {stats['min']*1000:.2f} ms, Max: {stats['max']*1000:.2f} ms")
        if stats['p95']:
            report_lines.append(f"- 95th percentile: {stats['p95']*1000:.2f} ms")
        report_lines.append(f"- Stddev: {stats['stdev']*1000:.2f} ms\n")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Performance metrics summary written to {REPORT_PATH}")

if __name__ == "__main__":
    main()
