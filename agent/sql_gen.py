# agent/sql_gen.py
import re
import unicodedata
from datetime import date, timedelta
from typing import Optional, Tuple, List

TABLE = "ventas"
ALLOWED_COLS = {"id","vendedor","sede","producto","cantidad","precio","fecha","total"}

# ---------------- Normalización / helpers ----------------
def _no_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _norm(s: str) -> str:
    return _no_accents(s.lower())

CITY_MAP = {
    "medellin": "Medellín",
    "bogota": "Bogotá",
    "cali": "Cali",
    "barranquilla": "Barranquilla",
}

def _pick_city(tn: str) -> Optional[str]:
    for k, v in CITY_MAP.items():
        if re.search(rf"\b{k}\b", tn):
            return v
    return None

def _extract_int(tn: str, default: int = 5) -> int:
    m = re.search(r"\btop\s*(\d+)\b", tn) or re.search(r"\btop(\d+)\b", tn)
    if m:
        try: return int(m.group(1))
        except ValueError: pass
    m2 = re.search(r"\b(bottom|peores?|menos)\s*(\d+)\b", tn)
    if m2:
        try: return int(m2.group(2))
        except ValueError: pass
    return default

# palabras que NO son nombre de producto tras "producto"
_STOP_AFTER_PRODUCT = {"mas","más","mejor","mejores","vendido","vendida","vendidos","vendidas","top","ranking","menos","peor","peores"}

def _extract_product(tn: str) -> Optional[str]:
    m = re.search(r"(?:\bdel\b|\bde\b|\bpor\b)\s+producto\s+([a-z0-9\"'\-\s]+)", tn)
    if not m: m = re.search(r"\bproducto\s+([a-z0-9\"'\-\s]+)", tn)
    if not m: return None
    cand = m.group(1).strip().strip('"\' ')
    if not cand: return None
    first = cand.split()[0]
    if first in _STOP_AFTER_PRODUCT: return None
    cand = re.split(r"\s+(en|de|por|para|en\s+la|en\s+el)\b", cand)[0].strip()
    return cand or None

def _extract_seller(tn: str) -> Optional[str]:
    m = re.search(r"(?:\bdel\b|\bde\b|\bpor\b)\s+vendedor[a]?\s+([a-záéíóúñ\s]+)", tn)
    if not m: m = re.search(r"\bvendedor[a]?\s+([a-záéíóúñ\s]+)", tn)
    if not m: return None
    cand = m.group(1).strip()
    cand = re.split(r"\s+(en|de|por|para)\b", cand)[0].strip()
    return cand or None

def _extract_dates(tn: str) -> Tuple[Optional[str], Optional[str]]:
    m = re.search(r"entre\s*(\d{4}-\d{2}-\d{2})\s*y\s*(\d{4}-\d{2}-\d{2})", tn)
    if m: return (m.group(1), m.group(2))
    today = date.today()
    if "hoy" in tn:  d=today.isoformat(); return (d,d)
    if "ayer" in tn: d=(today - timedelta(days=1)).isoformat(); return (d,d)
    if "ultimo mes" in tn or "último mes" in tn:
        last = (today.replace(day=1) - timedelta(days=1))
        return (last.replace(day=1).isoformat(), last.isoformat())
    if any(k in tn for k in ["ultima semana","última semana","ultimos 7 dias","últimos 7 días"]):
        return ((today - timedelta(days=7)).isoformat(), today.isoformat())
    m = re.search(r"(?:en|año)\s*(\d{4})", tn)
    if m:
        y=int(m.group(1)); return (f"{y}-01-01", f"{y}-12-31")
    MONTHS = {"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06",
              "julio":"07","agosto":"08","septiembre":"09","setiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"}
    m = re.search(r"en\s*(\d{4})-(\d{2})", tn)
    if m:
        y,mm=m.group(1),m.group(2); return (f"{y}-{mm}-01", f"{y}-{mm}-31")
    for esp,mm in MONTHS.items():
        m = re.search(rf"en\s*{esp}\s*(\d{{4}})", tn)
        if m:
            y=m.group(1); return (f"{y}-{mm}-01", f"{y}-{mm}-31")
    return (None, None)

def _want_chart(tn: str) -> Optional[str]:
    if any(k in tn for k in ["pastel","torta","pie"]): return "pie"
    if any(k in tn for k in ["linea","línea","line"]): return "line"
    if any(k in tn for k in ["barra","barras","bar","grafico","gráfico"]): return "bar"
    return None

def _want_file(tn: str) -> Optional[str]:
    if "excel" in tn or "xlsx" in tn: return "excel"
    if any(k in tn for k in ["csv","guarda","guardar","exporta","exportar","descarga","descargar","archivo"]): return "csv"
    return None

def _build_where(city: Optional[str], dfrom: Optional[str], dto: Optional[str],
                 prod: Optional[str], sell: Optional[str]) -> Tuple[str, List]:
    clauses, params = [], []
    if city: clauses.append("sede = ?"); params.append(city)
    if sell: clauses.append("LOWER(vendedor) LIKE ?"); params.append(f"%{sell.lower()}%")
    if prod: clauses.append("LOWER(producto) LIKE ?"); params.append(f"%{prod.lower()}%")
    if dfrom and dto: clauses.append("date(fecha) BETWEEN date(?) AND date(?)"); params += [dfrom, dto]
    elif dfrom:       clauses.append("date(fecha) = date(?)"); params.append(dfrom)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, params

def _like(tn: str, *needles: str) -> bool:
    return all(n in tn for n in needles)

# ---------------- Generador NL → SQL ----------------
def generate_sql(user_text: str):
    """
    Devuelve: (sql, (mode, params))
      sql:   str con '?' (SQLite)
      mode:  'table'|'bar'|'line'|'pie'|'csv'|'excel'|'text'
      params: tuple
    """
    tl = user_text.strip()
    if not tl:
        return (f"SELECT * FROM {TABLE} LIMIT 20;", ("table", ()))
    tn = _norm(tl)

    city      = _pick_city(tn)
    n         = _extract_int(tn, default=5)
    dfrom,dto = _extract_dates(tn)
    prod_like = _extract_product(tn)
    sell_like = _extract_seller(tn)
    chart     = _want_chart(tn)
    file_mode = _want_file(tn)
    where_sql, params = _build_where(city, dfrom, dto, prod_like, sell_like)

    # --- Producto más / menos vendido (singular) ---
    if re.search(r"\bproducto\b.*m[aá]s\s+vendid", tn) or re.search(r"m[aá]s\s+vendid[oa]\s+.*\bproducto\b", tn):
        sql = (
            f"SELECT producto, SUM(cantidad) AS total_cantidad "
            f"FROM {TABLE} {where_sql} GROUP BY producto "
            f"ORDER BY total_cantidad DESC LIMIT 1;"
        ); return (sql, ("text", tuple(params)))
    if re.search(r"\bproducto\b.*menos\s+vendid", tn) or re.search(r"menos\s+vendid[oa]\s+.*\bproducto\b", tn) or "peor producto" in tn:
        sql = (
            f"SELECT producto, SUM(cantidad) AS total_cantidad "
            f"FROM {TABLE} {where_sql} GROUP BY producto "
            f"ORDER BY total_cantidad ASC LIMIT 1;"
        ); return (sql, ("text", tuple(params)))

    # --- Vendedor con más / menos ventas (singular) ---
    if re.search(r"vendedor.*m[aá]s.*ventas", tn) or _like(tn,"quien","vendedor") or _like(tn,"quién","vendedor"):
        sql = (
            f"SELECT vendedor, SUM(cantidad*precio) AS total_ventas "
            f"FROM {TABLE} {where_sql} GROUP BY vendedor "
            f"ORDER BY total_ventas DESC LIMIT 1;"
        ); return (sql, ("text", tuple(params)))
    if re.search(r"vendedor.*menos.*ventas", tn) or "peor vendedor" in tn:
        sql = (
            f"SELECT vendedor, SUM(cantidad*precio) AS total_ventas "
            f"FROM {TABLE} {where_sql} GROUP BY vendedor "
            f"ORDER BY total_ventas ASC LIMIT 1;"
        ); return (sql, ("text", tuple(params)))

    # --- "top 5 ventas de medellin" (sin decir producto/vendedor) -> productos por monto ---
    if ("ventas" in tn or "venta" in tn) and (re.search(r"\btop(\d+)?\b", tn) or "top " in tn or "ranking" in tn):
        sql = (
            f"SELECT producto, SUM(cantidad*precio) AS total_ventas "
            f"FROM {TABLE} {where_sql} "
            f"GROUP BY producto ORDER BY total_ventas DESC LIMIT {n};"
        ); return (sql, (chart or file_mode or "table", tuple(params)))

    # --- TOP/BOTTOM N por productos (monto o cantidad) ---
    is_top    = bool(re.search(r"\btop(\d+)?\b", tn) or "top " in tn or "mejores" in tn or "ranking" in tn or "más vendidos" in tn or "mas vendidos" in tn)
    is_bottom = "peores" in tn or "menos vendidos" in tn or "bottom" in tn
    if ("producto" in tn or "productos" in tn) and (is_top or is_bottom):
        order  = "DESC" if is_top and not is_bottom else "ASC"
        by_qty = ("cantidad" in tn) or ("unidades" in tn) or ("vendid" in tn)
        if by_qty:
            sql = (
                f"SELECT producto, SUM(cantidad) AS total_cantidad "
                f"FROM {TABLE} {where_sql} GROUP BY producto "
                f"ORDER BY total_cantidad {order} LIMIT {n};"
            )
        else:
            sql = (
                f"SELECT producto, SUM(cantidad*precio) AS total_ventas "
                f"FROM {TABLE} {where_sql} GROUP BY producto "
                f"ORDER BY total_ventas {order} LIMIT {n};"
            )
        return (sql, (chart or file_mode or "table", tuple(params)))

    # --- TOP/BOTTOM N por vendedores (monto o cantidad) ---
    if ("vendedor" in tn or "vendedores" in tn) and (is_top or is_bottom):
        order  = "DESC" if is_top and not is_bottom else "ASC"
        by_qty = ("cantidad" in tn) or ("unidades" in tn)
        if by_qty:
            sql = (
                f"SELECT vendedor, SUM(cantidad) AS total_cantidad "
                f"FROM {TABLE} {where_sql} GROUP BY vendedor "
                f"ORDER BY total_cantidad {order} LIMIT {n};"
            )
        else:
            sql = (
                f"SELECT vendedor, SUM(cantidad*precio) AS total_ventas "
                f"FROM {TABLE} {where_sql} GROUP BY vendedor "
                f"ORDER BY total_ventas {order} LIMIT {n};"
            )
        return (sql, (chart or file_mode or "table", tuple(params)))

    # --- Ranking por sede ---
    if "por sede" in tn and ("ranking" in tn or "top" in tn or "mejores" in tn or "peores" in tn):
        order = "ASC" if "peores" in tn or "bottom" in tn else "DESC"
        sql = (
            f"SELECT sede, SUM(cantidad*precio) AS total_ventas "
            f"FROM {TABLE} {where_sql} GROUP BY sede "
            f"ORDER BY total_ventas {order} LIMIT {n};"
        ); return (sql, (chart or file_mode or "table", tuple(params)))

    # --- Totales / promedios / precio promedio (global o por producto) ---
    if "ticket promedio" in tn or "promedio por venta" in tn or _like(tn,"promedio","venta"):
        sql = f"SELECT AVG(cantidad*precio) AS ticket_promedio FROM {TABLE} {where_sql};"
        return (sql, ("text", tuple(params)))
    if "promedio de precio" in tn or _like(tn,"precio","promedio"):
        # si piden de un producto concreto (prod_like), el WHERE ya lo filtra
        sql = f"SELECT AVG(precio) AS precio_promedio FROM {TABLE} {where_sql};"
        return (sql, ("text", tuple(params)))

    # --- Total de ventas (global o agrupado) ---
    if "total de ventas" in tn or "ingreso" in tn or "facturacion" in tn or "facturación" in tn or "ventas totales" in tn:
        if "por vendedor" in tn or "por vendedores" in tn:
            sql = (
                f"SELECT vendedor, SUM(cantidad*precio) AS total_ventas "
                f"FROM {TABLE} {where_sql} GROUP BY vendedor ORDER BY total_ventas DESC;"
            ); return (sql, (chart or file_mode or "table", tuple(params)))
        if "por sede" in tn or "por sedes" in tn:
            sql = (
                f"SELECT sede, SUM(cantidad*precio) AS total_ventas "
                f"FROM {TABLE} {where_sql} GROUP BY sede ORDER BY total_ventas DESC;"
            ); return (sql, (chart or file_mode or "table", tuple(params)))
        if "por producto" in tn or "por productos" in tn:
            sql = (
                f"SELECT producto, SUM(cantidad*precio) AS total_ventas "
                f"FROM {TABLE} {where_sql} GROUP BY producto ORDER BY total_ventas DESC;"
            ); return (sql, (chart or file_mode or "table", tuple(params)))
        sql = f"SELECT SUM(cantidad*precio) AS total_ventas FROM {TABLE} {where_sql};"
        return (sql, ("text", tuple(params)))

    # --- Cantidad/Unidades por agrupación ---
    if "cantidad" in tn or "unidades" in tn:
        if "por vendedor" in tn:
            sql = (
                f"SELECT vendedor, SUM(cantidad) AS total_cantidad "
                f"FROM {TABLE} {where_sql} GROUP BY vendedor ORDER BY total_cantidad DESC;"
            ); return (sql, (chart or file_mode or "table", tuple(params)))
        if "por sede" in tn:
            sql = (
                f"SELECT sede, SUM(cantidad) AS total_cantidad "
                f"FROM {TABLE} {where_sql} GROUP BY sede ORDER BY total_cantidad DESC;"
            ); return (sql, (chart or file_mode or "table", tuple(params)))
        if "por producto" in tn or "por productos" in tn:
            sql = (
                f"SELECT producto, SUM(cantidad) AS total_cantidad "
                f"FROM {TABLE} {where_sql} GROUP BY producto ORDER BY total_cantidad DESC;"
            ); return (sql, (chart or file_mode or "table", tuple(params)))

    # --- Participación (%) por grupo (producto/vendedor/sede) ---
    if "participacion" in tn or "participación" in tn or "porcentaje" in tn:
        # Detectar grupo
        if "por vendedor" in tn:
            sql = (
                f"SELECT vendedor, "
                f"SUM(cantidad*precio) AS total_ventas, "
                f"ROUND(100.0*SUM(cantidad*precio) / "
                f"(SELECT SUM(cantidad*precio) FROM {TABLE} {where_sql}), 2) AS pct "
                f"FROM {TABLE} {where_sql} GROUP BY vendedor ORDER BY total_ventas DESC;"
            ); return (sql, ("table", tuple(params)))
        if "por sede" in tn:
            sql = (
                f"SELECT sede, "
                f"SUM(cantidad*precio) AS total_ventas, "
                f"ROUND(100.0*SUM(cantidad*precio) / "
                f"(SELECT SUM(cantidad*precio) FROM {TABLE} {where_sql}), 2) AS pct "
                f"FROM {TABLE} {where_sql} GROUP BY sede ORDER BY total_ventas DESC;"
            ); return (sql, ("table", tuple(params)))
        # por producto (default)
        sql = (
            f"SELECT producto, "
            f"SUM(cantidad*precio) AS total_ventas, "
            f"ROUND(100.0*SUM(cantidad*precio) / "
            f"(SELECT SUM(cantidad*precio) FROM {TABLE} {where_sql}), 2) AS pct "
            f"FROM {TABLE} {where_sql} GROUP BY producto ORDER BY total_ventas DESC;"
        ); return (sql, ("table", tuple(params)))

    # --- Tendencias por tiempo (opcionalmente por producto/vendedor) ---
    if "por dia" in tn or "por día" in tn:
        sql = (
            f"SELECT date(fecha) AS dia, SUM(cantidad*precio) AS total_ventas "
            f"FROM {TABLE} {where_sql} GROUP BY dia ORDER BY dia;"
        ); return (sql, (chart or "line", tuple(params)))
    if "por mes" in tn:
        sql = (
            f"SELECT strftime('%Y-%m', date(fecha)) AS mes, SUM(cantidad*precio) AS total_ventas "
            f"FROM {TABLE} {where_sql} GROUP BY mes ORDER BY mes;"
        ); return (sql, (chart or "line", tuple(params)))
    if "por año" in tn or "por anio" in tn:
        sql = (
            f"SELECT strftime('%Y', date(fecha)) AS anio, SUM(cantidad*precio) AS total_ventas "
            f"FROM {TABLE} {where_sql} GROUP BY anio ORDER BY anio;"
        ); return (sql, (chart or "line", tuple(params)))

    # --- Exportaciones explícitas ---
    if file_mode:
        # por defecto exportamos ventas por vendedor (filtrado si aplicó)
        sql = (
            f"SELECT vendedor, SUM(cantidad*precio) AS total_ventas "
            f"FROM {TABLE} {where_sql} GROUP BY vendedor ORDER BY total_ventas DESC;"
        ); return (sql, (file_mode, tuple(params)))

    # --- Mostrar tabla / lista ---
    if any(k in tn for k in ["tabla","muestr","lista","ver ventas","detalle"]):
        sql = f"SELECT * FROM {TABLE} {where_sql} ORDER BY date(fecha) DESC, id DESC LIMIT 200;"
        return (sql, ("table", tuple(params)))

    # --- Fallback genérico ---
    sql = f"SELECT * FROM {TABLE} {where_sql} LIMIT 50;"
    return (sql, ("table", tuple(params)))

# --- Compatibilidad / seguridad ---
def is_sql_safe(sql: str) -> bool:
    s = sql.lower()
    bad = ["insert ","update ","delete ","drop ","alter ","create ","attach ","pragma "]
    return all(x not in s for x in bad) and " from " in s and TABLE in s
