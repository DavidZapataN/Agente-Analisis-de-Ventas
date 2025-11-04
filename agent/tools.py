# agent/tools.py
"""
Herramientas (tools) para el agente inteligente.
Cada tool puede ser llamada por el LLM cuando lo considere apropiado.
"""

import asyncio
import pandas as pd
from typing import Optional, Literal
from pathlib import Path
from strands import tool

from agent.db import init_db
from agent.outputs import render_chart, save_file


@tool
async def query_database(sql_query: str) -> str:
    """
    Ejecuta una consulta SQL en la base de datos de ventas y retorna los resultados.
    
    Args:
        sql_query: Consulta SQL SELECT a ejecutar. Solo se permiten consultas SELECT.
                  La tabla se llama 'ventas' con columnas: id, vendedor, sede, 
                  producto, cantidad, precio, fecha, total.
    
    Returns:
        Resultados de la consulta en formato de texto tabular.
        
    Example:
        sql_query = "SELECT producto, SUM(cantidad) AS total FROM ventas GROUP BY producto LIMIT 5"
    """
    try:
        # Asegurar que la BD esté inicializada
        init_db()
        
        # Validación básica de seguridad
        sql_lower = sql_query.lower().strip()
        dangerous_keywords = ["insert", "update", "delete", "drop", "alter", "create", "attach", "pragma"]
        if any(keyword in sql_lower for keyword in dangerous_keywords):
            return f"❌ Error: Consulta no permitida. Solo se permiten consultas SELECT."
        
        if not sql_lower.startswith("select"):
            return f"❌ Error: Solo se permiten consultas SELECT."
        
        # Ejecutar consulta directamente con SQLite (más estable que MCP)
        import sqlite3
        from pathlib import Path
        
        db_path = Path("data/ventas.sqlite")
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(sql_query, conn)
        
        if df.empty:
            return "⚠️ La consulta no devolvió resultados."
        
        # Retornar tabla formateada
        result = f"✅ Consulta ejecutada exitosamente. Resultados:\n\n"
        result += df.to_string(index=False)
        result += f"\n\n📊 Total de filas: {len(df)}"
        
        return result
        
    except Exception as e:
        return f"❌ Error al ejecutar la consulta: {str(e)}"


@tool
async def generate_chart(
    sql_query: str,
    chart_type: Literal["bar", "line", "pie"],
    title: Optional[str] = None
) -> str:
    """
    Genera un gráfico a partir de una consulta SQL y lo guarda como imagen.
    
    Args:
        sql_query: Consulta SQL que devuelve datos para graficar. 
                  Debe retornar al menos 2 columnas: eje X y eje Y.
        chart_type: Tipo de gráfico - "bar" (barras), "line" (línea), o "pie" (torta/pastel)
        title: Título opcional para el gráfico
    
    Returns:
        Ruta del archivo de imagen generado o mensaje de error.
        
    Example:
        sql_query = "SELECT producto, SUM(cantidad) AS total FROM ventas GROUP BY producto LIMIT 5"
        chart_type = "bar"
        title = "Top 5 Productos Más Vendidos"
    """
    try:
        # Asegurar que la BD esté inicializada
        init_db()
        
        # Ejecutar consulta directamente con SQLite
        import sqlite3
        from pathlib import Path
        
        db_path = Path("data/ventas.sqlite")
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(sql_query, conn)
        
        if df.empty or len(df.columns) < 2:
            return "⚠️ La consulta debe devolver al menos 2 columnas con datos para generar un gráfico."
        
        # Generar gráfico
        x_col, y_col = df.columns[0], df.columns[1]
        chart_path = render_chart(
            df, 
            chart=chart_type, 
            x=x_col, 
            y=y_col, 
            title=title or f"{y_col} por {x_col}"
        )
        
        # También mostrar datos
        data_preview = df.to_string(index=False)
        
        return f"✅ Gráfico generado exitosamente.\n\n📊 Archivo: {chart_path}\n\n📋 Datos:\n{data_preview}"
        
    except Exception as e:
        return f"❌ Error al generar el gráfico: {str(e)}"


@tool
async def export_to_file(
    sql_query: str,
    format: Literal["csv", "excel"] = "csv",
    filename: Optional[str] = None
) -> str:
    """
    Exporta los resultados de una consulta SQL a un archivo CSV o Excel.
    
    Args:
        sql_query: Consulta SQL para obtener los datos a exportar
        format: Formato del archivo - "csv" o "excel"
        filename: Nombre opcional del archivo (sin extensión)
    
    Returns:
        Ruta del archivo generado o mensaje de error.
        
    Example:
        sql_query = "SELECT vendedor, SUM(cantidad*precio) AS total_ventas FROM ventas GROUP BY vendedor"
        format = "csv"
    """
    try:
        # Asegurar que la BD esté inicializada
        init_db()
        
        # Ejecutar consulta directamente con SQLite
        import sqlite3
        from pathlib import Path
        
        db_path = Path("data/ventas.sqlite")
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(sql_query, conn)
        
        if df.empty:
            return "⚠️ La consulta no devolvió datos para exportar."
        
        # Guardar archivo
        file_path = save_file(df, mode=format)
        
        return f"✅ Archivo exportado exitosamente.\n\n📎 Ruta: {file_path}\n📊 Filas exportadas: {len(df)}"
        
    except Exception as e:
        return f"❌ Error al exportar archivo: {str(e)}"


@tool
def get_database_schema() -> str:
    """
    Devuelve información sobre el esquema de la base de datos.
    
    Returns:
        Descripción del esquema de la tabla 'ventas' con ejemplos.
    """
    schema = """
📊 **Esquema de la Base de Datos**

**Tabla: ventas**

Columnas:
- **id** (INTEGER): Identificador único de la venta
- **vendedor** (TEXT): Nombre del vendedor
- **sede** (TEXT): Ciudad/sede donde se realizó la venta (ej: Medellín, Bogotá, Cali, Barranquilla)
- **producto** (TEXT): Nombre del producto vendido
- **cantidad** (INTEGER): Cantidad de unidades vendidas
- **precio** (REAL): Precio unitario del producto
- **fecha** (DATE): Fecha de la venta en formato YYYY-MM-DD
- **total** (REAL): Monto total de la venta (cantidad × precio)

**Ejemplos de consultas útiles:**

1. Top productos más vendidos:
   ```sql
   SELECT producto, SUM(cantidad) AS total_vendido 
   FROM ventas 
   GROUP BY producto 
   ORDER BY total_vendido DESC 
   LIMIT 5;
   ```

2. Ventas por vendedor en una sede específica:
   ```sql
   SELECT vendedor, SUM(total) AS total_ventas 
   FROM ventas 
   WHERE sede = 'Bogotá' 
   GROUP BY vendedor 
   ORDER BY total_ventas DESC;
   ```

3. Ventas por mes:
   ```sql
   SELECT strftime('%Y-%m', fecha) AS mes, SUM(total) AS ventas_mes
   FROM ventas 
   GROUP BY mes 
   ORDER BY mes;
   ```
"""
    return schema


# Versiones síncronas para compatibilidad (wrappean las async)
def query_database_sync(sql_query: str) -> str:
    """Versión síncrona de query_database"""
    return asyncio.run(query_database(sql_query))

def generate_chart_sync(sql_query: str, chart_type: Literal["bar", "line", "pie"], title: Optional[str] = None) -> str:
    """Versión síncrona de generate_chart"""
    return asyncio.run(generate_chart(sql_query, chart_type, title))

def export_to_file_sync(sql_query: str, format: Literal["csv", "excel"] = "csv", filename: Optional[str] = None) -> str:
    """Versión síncrona de export_to_file"""
    return asyncio.run(export_to_file(sql_query, format, filename))
