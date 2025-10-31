import os, asyncio
from agent.intents import classify_intent
from agent.sql_gen import generate_sql, is_sql_safe
from agent.outputs import render_table, render_chart, save_file
from agent.memory import Memory

USE_MCP = os.environ.get("USE_MCP", "0") == "1"
if USE_MCP:
    from agent.mcp_sql_client import run_sql
else:
    # fallback directo SQLite (sin MCP) opcional
    import sqlite3
    def run_sql(sql: str):
        con = sqlite3.connect("db/ventas.db"); con.row_factory = sqlite3.Row
        cur = con.cursor(); cur.execute(sql)
        rows = [tuple(r) for r in cur.fetchall()]
        cols = [d[0] for d in cur.description] if cur.description else []
        con.close()
        return rows, cols

mem = Memory()

async def handle_query(text: str):
    intent = classify_intent(text)
    sql = generate_sql(text)
    if not is_sql_safe(sql): return "Consulta bloqueada por políticas de seguridad."
    rows, cols = await run_sql(sql) if USE_MCP else run_sql(sql)
    mem.last_sql, mem.last_result = sql, (rows, cols)

    if intent["format"] == "table": return render_table(rows, cols)
    if intent["format"] == "chart": return render_chart(rows, cols)
    if intent["format"] == "file":
        path = save_file(rows, cols, "resultado", intent.get("file") or "csv")
        return f"Archivo guardado en {path}"
    return render_table(rows, cols)

if __name__ == "__main__":
    q = input("Pregunta sobre ventas: ")
    out = asyncio.run(handle_query(q))
    print(out if out else "")
