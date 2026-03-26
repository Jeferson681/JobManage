import os
import time
import argparse
import psycopg2


def wait_for_pg(timeout: int = 60) -> int:
    start = time.time()
    host = os.environ.get("PGHOST", "localhost")
    port = int(os.environ.get("PGPORT", 5432))
    user = os.environ.get("PGUSER")
    password = os.environ.get("PGPASSWORD")
    dbname = os.environ.get("PGDATABASE")

    while time.time() - start < timeout:
        try:
            conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
            conn.close()
            print("Postgres available")
            return 0
        except Exception:
            time.sleep(1)
    print("Timed out waiting for Postgres")
    return 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--timeout", type=int, default=60)
    args = p.parse_args()
    raise SystemExit(wait_for_pg(args.timeout))
