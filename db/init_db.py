import sqlite3, pandas as pd
from pathlib import Path

DB = Path(__file__).with_name("ventas.db")
CSV = Path(__file__).parents[1] / "data" / "ventas_demo.csv"
DDL = (Path(__file__).with_name("schema.sql")).read_text()

con = sqlite3.connect(DB)
cur = con.cursor()
cur.executescript(DDL)
df = pd.read_csv(CSV)
cur.execute("DELETE FROM ventas;")
df.to_sql("ventas", con, if_exists="append", index=False)
con.commit(); con.close()
print(f"OK: {len(df)} filas → {DB}")
