# agent/outputs.py
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def render_table(df: pd.DataFrame, save_csv: bool = False) -> None:
    if df.empty:
        print("⚠️  Sin resultados.")
        return
    print(df.to_string(index=False))
    if save_csv:
        path = DATA_DIR / "ultima_tabla.csv"
        df.to_csv(path, index=False)
        print(f"💾 Tabla guardada en: {path}")

def _timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")

def render_chart(df: pd.DataFrame, chart: str, x: str, y: str, title: str = "") -> str:
    if df.empty:
        print("⚠️  Sin datos para graficar.")
        return ""

    outfile = DATA_DIR / f"grafico_{chart}_{_timestamp()}.png"

    if chart == "pie":
        # Para pie usamos la primera columna como labels y la segunda como values
        labels = df[x].astype(str).tolist()
        values = df[y].values.tolist()
        plt.figure()
        plt.pie(values, labels=labels, autopct="%1.1f%%")
        plt.title(title or f"{y} por {x}")
        plt.tight_layout()
        plt.savefig(outfile, dpi=120)
        plt.close()
    elif chart == "line":
        plt.figure()
        plt.plot(df[x], df[y], marker="o")
        plt.title(title or f"{y} vs {x}")
        plt.xlabel(x)
        plt.ylabel(y)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(outfile, dpi=120)
        plt.close()
    else:  # bar (default)
        plt.figure()
        plt.bar(df[x].astype(str), df[y])
        plt.title(title or f"{y} por {x}")
        plt.xlabel(x)
        plt.ylabel(y)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(outfile, dpi=120)
        plt.close()

    print(f"📊 Gráfico guardado en: {outfile}")
    return str(outfile)

def save_file(df: pd.DataFrame, mode: str) -> str:
    if df.empty:
        print("⚠️  Nada que guardar.")
        return ""
    if mode == "excel":
        out = DATA_DIR / f"salida_{_timestamp()}.xlsx"
        df.to_excel(out, index=False)
        print(f"💾 Excel guardado en: {out}")
        return str(out)
    # CSV por defecto
    out = DATA_DIR / f"salida_{_timestamp()}.csv"
    df.to_csv(out, index=False)
    print(f"💾 CSV guardado en: {out}")
    return str(out)
