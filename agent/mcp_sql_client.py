# agent/mcp_sql_client.py
# -*- coding: utf-8 -*-
"""
Cliente MCP para ejecutar SQL sobre SQLite usando @executeautomation/database-server (Node).
- Tool de lectura:  read_query  (parámetro: query)
- Otras tools útiles: list_tables, describe_table, export_query (no usadas aquí)
Seguridad básica: solo permite SELECT.
"""

import asyncio
from contextlib import AsyncExitStack
from typing import List, Tuple, Sequence, Dict, Any

from strands.tools.mcp import MCPClient, ToolFilters
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Comando para levantar el servidor MCP de base de datos (Node)
MCP_COMMAND = "npx"
MCP_ARGS = ["-y", "@executeautomation/database-server", "db/ventas.db"]

READ_TOOL_NAME = "read_query"     # según el listado de tools
READ_TOOL_PARAM = "query"         # parámetro que espera el server para el SQL

# --- Utilidades internas ------------------------------------------------------

def _is_select(sql: str) -> bool:
    return sql.strip().lower().startswith("select")

def _normalize_result(result: Any) -> Tuple[List[Tuple], List[str]]:
    """
    Normaliza la salida del servidor MCP a (rows, cols).
    Server suele devolver lista de dicts para read_query:
      [ {"col1": v1, "col2": v2, ...}, ... ]
    También contemplamos estructuras alternativas (columns/rows).
    """
    # Caso típico: lista de registros como dicts
    if isinstance(result, list):
        if not result:
            return [], []
        # columnas en el orden de las keys del primer registro
        cols = list(result[0].keys())
        rows = [tuple(rec.get(c) for c in cols) for rec in result]
        return rows, cols

    # Caso alternativo: dict con columns/rows
    if isinstance(result, dict):
        cols = result.get("columns") or []
        rows = result.get("rows") or []
        # Si rows vienen como dicts y no como tuplas:
        if rows and isinstance(rows[0], dict) and cols:
            rows = [tuple(r.get(c) for c in cols) for r in rows]
        return rows, cols

    # Fallback
    return [], []

async def _open_mcp_client(allow_patterns: Sequence[str] = (r".*query.*", r".*tables.*")) -> MCPClient:
    """
    Abre transporte stdio hacia el server MCP y devuelve un MCPClient listo.
    """
    stack = AsyncExitStack()
    await stack.enter_async_context(stack)  # para que el stack se cierre aunque retornemos el cliente

    params = StdioServerParameters(command=MCP_COMMAND, args=MCP_ARGS)
    read_stream, write_stream = await stack.enter_async_context(stdio_client(params))

    client = MCPClient((read_stream, write_stream),
                       tool_filters=ToolFilters(allow=list(allow_patterns)))
    await client.initialize()

    # Guardar el stack en el cliente para que no se cierre al salir de la función
    # y poder cerrar con close_mcp_client(client)
    client._stack = stack  # atributo privado ad-hoc
    return client

async def _close_mcp_client(client: MCPClient) -> None:
    try:
        await client.close()
    finally:
        stack = getattr(client, "_stack", None)
        if stack is not None:
            await stack.aclose()

# --- API pública --------------------------------------------------------------

async def run_sql(sql: str) -> Tuple[List[Tuple], List[str]]:
    """
    Ejecuta una consulta SELECT vía MCP (tool: read_query) y devuelve (rows, cols).
    Lanza ValueError si no es SELECT.
    """
    if not _is_select(sql):
        raise ValueError("Solo se permiten consultas SELECT por seguridad.")

    client = await _open_mcp_client()
    try:
        # Llamada a la tool real del server: read_query(query=...)
        payload = {READ_TOOL_PARAM: sql}
        result = await client.call_tool(READ_TOOL_NAME, payload)
        rows, cols = _normalize_result(result)
        return rows, cols
    finally:
        await _close_mcp_client(client)

async def list_tables() -> List[str]:
    """
    Devuelve el listado de tablas disponibles usando la tool list_tables (si existe).
    """
    client = await _open_mcp_client()
    try:
        if "list_tables" not in client.tools:
            return []
        result = await client.call_tool("list_tables", {})
        # El server suele devolver lista de nombres o lista de dicts con 'name'
        if isinstance(result, list):
            if result and isinstance(result[0], dict):
                return [r.get("name") or r.get("table") for r in result]
            return [str(r) for r in result]
        return []
    finally:
        await _close_mcp_client(client)

def run_sql_sync(sql: str) -> Tuple[List[Tuple], List[str]]:
    """
    Versión síncrona (útil para pruebas rápidas desde otros módulos).
    """
    return asyncio.run(run_sql(sql))

# --- Ejecución directa para prueba -------------------------------------------

if __name__ == "__main__":
    q = "SELECT producto, SUM(cantidad) AS total_vendido FROM ventas GROUP BY producto ORDER BY total_vendido DESC LIMIT 5;"
    rows, cols = asyncio.run(run_sql(q))
    print("Columns:", cols)
    for r in rows:
        print(r)
