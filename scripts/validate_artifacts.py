import json
import os
import sys


def main():
    """Validate required artifacts in `out_dir` and exit with non-zero on failure."""
    out_dir = sys.argv[1] if len(sys.argv) > 1 else ".tmp_ci_artifacts/unknown"

    required = [
        "demo.db",
        "demo_output.txt",
        "metrics.txt",
        "health.txt",
    ]

    missing = [name for name in required if not os.path.exists(os.path.join(out_dir, name))]
    if missing:
        print("Missing required artifacts:", missing)
        sys.exit(1)

    with open(os.path.join(out_dir, "health.txt"), "r", encoding="utf-8") as f:
        health = json.load(f)
    if health.get("status") != "ok":
        print("health.txt is not ok:", health)
        sys.exit(1)

    with open(os.path.join(out_dir, "metrics.txt"), "r", encoding="utf-8") as f:
        metrics = json.load(f)

    jobs_by_status = metrics.get("jobs_by_status") or {}
    try:
        total_jobs = sum(int(v) for v in jobs_by_status.values())
    except Exception:
        print("Invalid jobs_by_status:", jobs_by_status)
        sys.exit(1)

    succeeded = int(jobs_by_status.get("SUCCEEDED", 0) or 0)
    canceled = int(jobs_by_status.get("CANCELED", 0) or 0)

    if total_jobs < 3:
        print("Expected at least 3 jobs in metrics, got:", total_jobs)
        print("metrics:", metrics)
        sys.exit(1)
    if succeeded < 1:
        print("Expected at least 1 SUCCEEDED job, got:", succeeded)
        print("metrics:", metrics)
        sys.exit(1)
    if canceled < 1:
        print("Expected at least 1 CANCELED job, got:", canceled)
        print("metrics:", metrics)
        sys.exit(1)

    print("Artifacts OK")
    print("metrics:", metrics)


if __name__ == "__main__":
    main()
