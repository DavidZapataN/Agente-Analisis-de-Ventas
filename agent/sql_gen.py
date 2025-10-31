ALLOWED_COLS = {"id","vendedor","sede","producto","cantidad","precio","fecha"}
TABLE = "ventas"

def generate_sql(user_text: str) -> str:
    tl = user_text.lower()
    if "top" in tl and "medellín" in tl:
        return ("SELECT producto, SUM(cantidad) AS total_vendido "
                "FROM ventas WHERE sede='Medellín' "
                "GROUP BY producto ORDER BY total_vendido DESC LIMIT 5;")
    if "vendedor" in tl and "bogotá" in tl:
        return ("SELECT vendedor, SUM(cantidad*precio) AS total_ventas "
                "FROM ventas WHERE sede='Bogotá' "
                "GROUP BY vendedor ORDER BY total_ventas DESC LIMIT 1;")
    if ("guarda" in tl or "csv" in tl or "excel" in tl) and "vendedor" in tl:
        return ("SELECT vendedor, SUM(cantidad*precio) AS total_ventas "
                "FROM ventas GROUP BY vendedor ORDER BY total_ventas DESC;")
    return f"SELECT * FROM {TABLE} LIMIT 20;"

def is_sql_safe(sql: str) -> bool:
    bad = ["insert ", "update ", "delete ", "drop ", "alter ", "create "]
    s = sql.lower()
    return all(k not in s for k in bad) and "ventas" in s
