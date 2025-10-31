# agent/app.py
from agent.sql_gen import generate_sql, is_sql_safe
from agent.db import init_db, query
from agent.outputs import render_table, render_chart, save_file

def answer(q: str):
    init_db()  # prepara SQLite desde CSV (silencioso)
    sql, (mode, params) = generate_sql(q)

    if not is_sql_safe(sql):
        print("❌ Consulta no permitida.")
        return

    df = query(sql, params)

    if mode == "text":
        if df.empty:
            print("⚠️  Sin resultados.")
            return
        row = df.iloc[0]
        if {"producto","total_cantidad"}.issubset(df.columns):
            print(f"🏆 Producto líder: {row['producto']} con {int(row['total_cantidad'])} unidades")
        elif {"vendedor","total_ventas"}.issubset(df.columns):
            print(f"🏆 Vendedor líder: {row['vendedor']} con total_ventas={int(row['total_ventas']):,}")
        elif "ticket_promedio" in df.columns:
            print(f"🧾 Ticket promedio: {float(row['ticket_promedio']):,.2f}")
        elif "precio_promedio" in df.columns:
            print(f"💲 Precio promedio: {float(row['precio_promedio']):,.2f}")
        elif "total_ventas" in df.columns:
            print(f"💰 Total de ventas: {int(row['total_ventas']):,}")
        else:
            render_table(df)
        return

    if mode in ("bar","line","pie"):
        if df.empty or df.shape[1] < 2:
            print("⚠️  Sin datos para graficar.")
            return
        x, y = df.columns[0], df.columns[1]
        render_chart(df, chart=mode, x=x, y=y, title=q)
        render_table(df)
        return

    if mode in ("csv","excel"):
        if df.empty:
            print("⚠️  Nada que exportar.")
            return
        path = save_file(df, mode=mode)
        print(f"📎 Archivo generado: {path}")
        return

    # por defecto: tabla
    render_table(df)

def main():
    try:
        while True:
            q = input("Ingresa tu consulta (o 'salir'): ").strip()
            if not q or q.lower() == "salir":
                break
            answer(q)
    except (EOFError, KeyboardInterrupt):
        pass

if __name__ == "__main__":
    main()
