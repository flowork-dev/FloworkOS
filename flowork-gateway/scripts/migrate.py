# C:\FLOWORK\flowork-gateway\scripts\migrate.py
# Simple SQLite migration runner.
import os, sqlite3, glob

DB_PATH = os.getenv("GW_DB_PATH", r"C:\FLOWORK\data\gateway.sqlite3")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# (English Hardcode) Use Linux paths as they will be inside the container
migrations = sorted(glob.glob(r"/app/migrations/*.sql"))
for mig in migrations:
    with open(mig, "r", encoding="utf-8") as f:
        sql = f.read()
        print(f"Applying {os.path.basename(mig)}")
        cur.executescript(sql)
conn.commit()
conn.close()
print("All migrations applied.")