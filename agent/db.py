# agent/db.py
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Tuple

DB_PATH = Path("data/ventas.sqlite")

def _find_csv() -> Tuple[Path, bool]:
    """
    Busca un CSV de ventas. Prioridad:
      1) data/ventas.csv
      2) data/ventas_demo.csv
      3) ventas.csv (raíz)
    Devuelve (path, exists)
    """
    candidates = [Path("data/ventas.csv"), Path("data/ventas_demo.csv"), Path("ventas.csv")]
    for p in candidates:
        if p.exists():
            return p, True
    return candidates[0], False  # por defecto

def init_db() -> str:
    csv_path, exists = _find_csv()
    if not exists:
        raise FileNotFoundError(
            f"No encontré dataset CSV. Crea 'data/ventas.csv' o 'data/ventas_demo.csv'. Busqué: {csv_path}"
        )

    df = pd.read_csv(csv_path)
    # Asegura columnas mínimas
    expected = {"id", "vendedor", "sede", "producto", "cantidad", "precio", "fecha"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en {csv_path}: {missing}. Esperadas: {sorted(expected)}")

    # Normaliza tipos básicos
    if "total" not in df.columns:
        df["total"] = df["cantidad"] * df["precio"]
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.date.astype(str)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("ventas", conn, if_exists="replace", index=False)
        cur = conn.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sede ON ventas(sede);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_vendedor ON ventas(vendedor);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_producto ON ventas(producto);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fecha ON ventas(fecha);")
        conn.commit()
    return str(DB_PATH)

def query(sql: str, params: tuple = ()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)
