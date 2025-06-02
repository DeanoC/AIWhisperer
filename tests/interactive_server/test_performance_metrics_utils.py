import time
import csv
import os
from collections import defaultdict

class MetricsCollector:
    def __init__(self, csv_path="performance_metrics.csv"):
        self.csv_path = csv_path
        self.records = []
        self.start_times = {}
        self.errors = defaultdict(int)
        self.memory = []

    def start_timer(self, key):
        self.start_times[key] = time.perf_counter()

    def stop_timer(self, key):
        if key in self.start_times:
            elapsed = time.perf_counter() - self.start_times[key]
            self.records.append({"event": key, "latency": elapsed})
            del self.start_times[key]
            return elapsed
        return None

    def record_error(self, error_type):
        self.errors[error_type] += 1

    def record_memory(self, current, peak):
        self.memory.append({"current": current, "peak": peak})

    def save(self):
        # Save latency records
        if self.records:
            fieldnames = ["event", "latency"]
            write_header = not os.path.exists(self.csv_path)
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                for rec in self.records:
                    writer.writerow(rec)
        # Save error summary
        if self.errors:
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["error_type", "count"])
                for k, v in self.errors.items():
                    writer.writerow([k, v])
        # Save memory usage
        if self.memory:
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["memory_current", "memory_peak"])
                for m in self.memory:
                    writer.writerow([m["current"], m["peak"]])

    def reset(self):
        self.records.clear()
        self.start_times.clear()
        self.errors.clear()
        self.memory.clear()
