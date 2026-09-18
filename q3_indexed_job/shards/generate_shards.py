"""
generate_shards.py -- AIOps Module 3 Assignment, Question 3.
Generates 8 deterministic, synthetic CSV shards of user signup records. Each shard has
a known, seeded number of deliberately invalid rows (malformed email or a missing
required field), so each Indexed Job pod's reported invalid-row count can be checked
against ground truth.
"""
import csv
import os
import random

N_SHARDS = 8
ROWS_PER_SHARD = 50
REQUIRED_FIELDS = ["user_id", "email", "signup_date"]

FIRST_NAMES = ["alice", "bob", "carol", "dave", "erin", "frank", "grace", "heidi"]
DOMAINS = ["example.com", "mail.co", "test.org", "corp.net"]
MALFORMED_EMAILS = ["not-an-email", "missing-at.com", "user@", "@nodomain.com", "user@@double.com"]


def make_row(row_id, shard_index, rng, invalid_kind=None):
    user_id = f"u-{shard_index}-{row_id:04d}"
    name = rng.choice(FIRST_NAMES)
    domain = rng.choice(DOMAINS)
    email = f"{name}{row_id}@{domain}"
    signup_date = f"2026-01-{(row_id % 28) + 1:02d}"

    if invalid_kind == "bad_email":
        email = rng.choice(MALFORMED_EMAILS)
    elif invalid_kind == "missing_field":
        field_to_drop = rng.choice(REQUIRED_FIELDS)
        row = {"user_id": user_id, "email": email, "signup_date": signup_date}
        row[field_to_drop] = ""
        return row

    return {"user_id": user_id, "email": email, "signup_date": signup_date}


def generate_shard(shard_index, out_dir):
    # Seed derived from a fixed base seed + shard index -> deterministic but distinct per shard.
    rng = random.Random(1000 + shard_index)
    n_invalid = rng.randint(3, 8)  # known ground-truth invalid count for this shard
    invalid_rows_idx = set(rng.sample(range(ROWS_PER_SHARD), n_invalid))

    rows = []
    for i in range(ROWS_PER_SHARD):
        if i in invalid_rows_idx:
            kind = rng.choice(["bad_email", "missing_field"])
            rows.append(make_row(i, shard_index, rng, invalid_kind=kind))
        else:
            rows.append(make_row(i, shard_index, rng))

    path = os.path.join(out_dir, f"shard_{shard_index}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return path, n_invalid


def main():
    out_dir = os.environ.get("SHARD_DIR", "data")
    os.makedirs(out_dir, exist_ok=True)
    ground_truth = {}
    for shard_index in range(N_SHARDS):
        path, n_invalid = generate_shard(shard_index, out_dir)
        ground_truth[shard_index] = n_invalid
        print(f"Wrote {path} ({ROWS_PER_SHARD} rows, {n_invalid} deliberately invalid)")

    with open(os.path.join(out_dir, "ground_truth.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["shard_index", "invalid_count"])
        for idx, count in ground_truth.items():
            writer.writerow([idx, count])
    print("Ground truth written to ground_truth.csv:", ground_truth)


if __name__ == "__main__":
    main()
