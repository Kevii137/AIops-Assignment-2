"""
validate_shard.py -- AIOps Module 3 Assignment, Question 3.
Entry point for each pod of the Kubernetes Indexed Job. Reads JOB_COMPLETION_INDEX
(set automatically by Kubernetes for Indexed Jobs) to pick exactly one shard, validates
every row, and prints a RESULT_JSON line to stdout so results can be collected via the
Kubernetes API afterwards (no shared volume -- see write-up for why).
"""
import csv
import json
import os
import re
import socket
import time

REQUIRED_FIELDS = ["user_id", "email", "signup_date"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def row_is_invalid(row):
    for field in REQUIRED_FIELDS:
        if not row.get(field, "").strip():
            return True
    if not EMAIL_RE.match(row["email"]):
        return True
    return False


def main():
    completion_index = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
    shard_dir = os.environ.get("SHARD_DIR", "/app/data")
    shard_path = os.path.join(shard_dir, f"shard_{completion_index}.csv")

    pod_name = os.environ.get("POD_NAME", socket.gethostname())
    node_name = os.environ.get("NODE_NAME", "unknown")

    total_rows = 0
    invalid_rows = 0
    with open(shard_path, newline="") as f:
        for row in csv.DictReader(f):
            total_rows += 1
            if row_is_invalid(row):
                invalid_rows += 1
            time.sleep(0.15)  # simulate per-row validation work (regex/DB/API lookups in a real pipeline)

    result = {
        "completion_index": completion_index,
        "shard_file": os.path.basename(shard_path),
        "total_rows": total_rows,
        "invalid_rows": invalid_rows,
        "pod_name": pod_name,
        "node_name": node_name,
    }
    print(f"[worker {completion_index}] pod={pod_name} node={node_name} "
          f"shard={shard_path} total={total_rows} invalid={invalid_rows}", flush=True)
    print("RESULT_JSON:" + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
