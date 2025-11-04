# 🏗️ Arquitectura del Sistema

## 📐 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                          USUARIO                                 │
│                  (Pregunta en lenguaje natural)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       agent/app.py                               │
│                   (Aplicación Principal)                         │
│                                                                  │
│  • Recibe input del usuario                                      │
│  • Mantiene el loop de interacción                               │
│  • Soporta modo legacy y modo inteligente                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   agent/bedrock_agent.py                        │
│                  (Agente Inteligente Core)                      │
│                                                                 │
│  ┌───────────────────────────────────────────────────┐          │
│  │   Strands Agent + Amazon Bedrock                  │          │
│  │   (Amazon Lite)                                   │          │
│  │                                                   │          │
│  │   • Razonamiento de lenguaje natural              │          │
│  │   • Decisión de qué herramientas usar             │          │
│  │   • Orquestación de acciones                      │          │
│  │   • Generación de respuestas                      │          │
│  └───────────────────────────────────────────────────┘          │
│                             │                                   │
│                             │ (invoca tools)                    │
│                             ▼                                   │
│  ┌───────────────────────────────────────────────────┐          │
│  │              HERRAMIENTAS (Tools)                 │          │
│  │            agent/tools.py                          │         │
│  │                                                    │         │
│  │  [1] query_database(sql_query)                    │          │
│  │  [2] generate_chart(sql, chart_type, title)       │          │
│  │  [3] export_to_file(sql, format)                  │          │
│  │  [4] get_database_schema()                        │          │
│  └───────────────────────────────────────────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│  DATOS & CONSULTAS   │              │   VISUALIZACIÓN Y    │
│                      │              │     EXPORTACIÓN      │
└──────────────────────┘              └──────────────────────┘
         │                                       │
         ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│ agent/mcp_sql_client │              │   agent/outputs.py   │
│                      │              │                      │
│ • Cliente MCP        │              │ • render_table()     │
│ • Ejecuta SQL        │              │ • render_chart()     │
│ • Valida seguridad   │              │ • save_file()        │
└──────────┬───────────┘              └──────────────────────┘
           │                                       │
           ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│  MCP Server (Node)   │              │  Matplotlib / Pandas │
│  @executeautomation/ │              │                      │
│  database-server     │              │  • Gráficos PNG      │
│                      │              │  • CSV / Excel       │
└──────────┬───────────┘              └──────────────────────┘
           │
           ▼
┌──────────────────────┐
│   SQLite Database    │
│   db/ventas.db       │
│                      │
│ • Tabla: ventas      │
│ • Datos de CSV       │
└──────────────────────┘
```

---

## 🔄 Flujo de Datos Detallado

### 1. Pregunta del Usuario

```
Usuario: "¿Cuáles son los 5 productos más vendidos en Medellín?"
```

### 2. Procesamiento por el Agente

```python
# app.py recibe la pregunta
agent = create_agent()
response = agent.ask_sync(question)

# bedrock_agent.py procesa con Claude
agent.run(question)
  ↓
Claude analiza:
  - Entender intención: "Buscar productos top en Medellín"
  - Identificar filtros: sede='Medellín', top=5
  - Decidir herramienta: query_database
  - Generar SQL apropiado
```

### 3. Ejecución de Herramienta

```python
# tools.py ejecuta query_database
await query_database(
    "SELECT producto, SUM(cantidad) AS total "
    "FROM ventas WHERE sede='Medellín' "
    "GROUP BY producto ORDER BY total DESC LIMIT 5"
)
  ↓
# mcp_sql_client.py envía a MCP
await run_sql(sql_query)
  ↓
# MCP Server ejecuta en SQLite
npx @executeautomation/database-server db/ventas.db
  ↓
# Retorna: [(producto, total), ...]
```

### 4. Generación de Respuesta

```python
# Amazon Lite recibe los datos y genera respuesta natural
"✅ Consulta ejecutada exitosamente. Resultados:

producto     total
---------    -----
Laptop       150
Mouse        120
Teclado      95
Monitor      80
Webcam       65

📊 Total de filas: 5"
```

---

## 🛠️ Componentes Principales

### 1. **Agente Inteligente** (`agent/bedrock_agent.py`)

**Responsabilidades:**
- Interpretar lenguaje natural
- Razonar sobre qué hacer
- Decidir qué herramientas invocar
- Generar respuestas coherentes

**Tecnologías:**
- `strands-agents`: Framework de orquestación
- `boto3`: SDK de AWS
- Amazon Bedrock: Servicio de IA
- Amazon Lite: Modelo LLM

---

### 2. **Herramientas (Tools)** (`agent/tools.py`)

#### Tool 1: `query_database(sql_query)`
- **Propósito**: Ejecutar consultas SQL
- **Input**: String SQL (solo SELECT)
- **Output**: Resultados en formato tabla
- **Seguridad**: Valida que no haya INSERT/UPDATE/DELETE

#### Tool 2: `generate_chart(sql_query, chart_type, title)`
- **Propósito**: Crear visualizaciones
- **Input**: SQL + tipo de gráfico (bar/line/pie)
- **Output**: Ruta del archivo PNG generado
- **Tecnología**: Matplotlib

#### Tool 3: `export_to_file(sql_query, format, filename)`
- **Propósito**: Exportar datos
- **Input**: SQL + formato (csv/excel)
- **Output**: Ruta del archivo exportado
- **Tecnología**: Pandas

#### Tool 4: `get_database_schema()`
- **Propósito**: Obtener info del esquema
- **Input**: Ninguno
- **Output**: Descripción de la tabla ventas
- **Uso**: Para que el agente entienda la estructura

---

### 3. **Cliente MCP** (`agent/mcp_sql_client.py`)

**Responsabilidades:**
- Comunicarse con el servidor MCP (Node.js)
- Ejecutar consultas SQL a través del protocolo MCP
- Normalizar resultados a formato Python

**Protocolo:**
```
Python (asyncio) ←→ stdio ←→ Node.js MCP Server ←→ SQLite
```

---

### 4. **Base de Datos** (`agent/db.py`)

**Responsabilidades:**
- Inicializar SQLite desde CSV
- Crear índices para optimizar consultas
- Mantener compatibilidad con modo legacy

**Esquema:**
```sql
CREATE TABLE ventas (
    id INTEGER,
    vendedor TEXT,
    sede TEXT,
    producto TEXT,
    cantidad INTEGER,
    precio REAL,
    fecha DATE,
    total REAL
);
```

---

### 5. **Visualización** (`agent/outputs.py`)

**Responsabilidades:**
- Renderizar tablas en consola
- Generar gráficos (Matplotlib)
- Exportar a CSV/Excel (Pandas)

**Formatos soportados:**
- Tabla → Consola (ASCII)
- Gráficos → PNG (data/*.png)
- Archivos → CSV/Excel (data/*.csv|xlsx)

---

## 🔐 Seguridad

### Validaciones Implementadas

1. **SQL Injection Prevention:**
   ```python
   if not sql_query.lower().strip().startswith("select"):
       raise ValueError("Solo SELECT permitido")
   ```

2. **Palabras clave peligrosas:**
   ```python
   dangerous = ["insert", "update", "delete", "drop", "alter", ...]
   if any(keyword in sql.lower() for keyword in dangerous):
       return error
   ```

3. **Límites de recursos:**
   - Timeouts en consultas
   - Límite de filas retornadas

---

## 🚀 Modos de Operación

### Modo Inteligente (por defecto)

```
LEGACY_MODE=false

Usuario → Agente → LLM → Tools → Respuesta
```

**Ventajas:**
- ✅ Flexible y adaptable
- ✅ Entiende lenguaje natural complejo
- ✅ Puede combinar múltiples herramientas
- ✅ Aprende de ejemplos

**Desventajas:**
- ⚠️ Requiere AWS Bedrock
- ⚠️ Tiene costo por uso
- ⚠️ Latencia del API (~1-3s)

---

### Modo Legacy (basado en reglas)

```
LEGACY_MODE=true

Usuario → Regex patterns → SQL directo → Respuesta
```

**Ventajas:**
- ✅ Sin costos de API
- ✅ Respuesta instantánea
- ✅ Funciona sin internet

**Desventajas:**
- ⚠️ Menos flexible
- ⚠️ Requiere patterns específicos
- ⚠️ No aprende

---

## 📊 Flujo de Decisión del Agente

```
Pregunta del usuario
    ↓
¿Necesito conocer el esquema de la BD?
    ↓ Sí
[get_database_schema()]
    ↓
Analizar intención:
    ├─ "mostrar", "listar" → query_database()
    ├─ "gráfico", "chart" → query_database() + generate_chart()
    ├─ "guardar", "exportar" → query_database() + export_to_file()
    └─ combinación → múltiples tools en secuencia
    ↓
Construir SQL
    ↓
Ejecutar tool(s)
    ↓
Interpretar resultados
    ↓
Generar respuesta en lenguaje natural
    ↓
Retornar al usuario
```

---

## 🧩 Dependencias Clave

| Librería | Propósito |
|----------|-----------|
| `strands-agents` | Framework de agentes |
| `boto3` | SDK de AWS |
| `pandas` | Manipulación de datos |
| `matplotlib` | Gráficos |
| `mcp` | Protocolo MCP |
| `asyncio` | Programación asíncrona |
| `sqlite3` | Base de datos |

---

## 🎯 Ventajas de esta Arquitectura

✅ **Modular**: Cada componente tiene responsabilidad única  
✅ **Extensible**: Fácil agregar nuevas tools  
✅ **Mantenible**: Separación clara de concerns  
✅ **Testeable**: Cada componente se puede probar aislado  
✅ **Flexible**: Soporta múltiples modos de operación  
✅ **Escalable**: MCP permite agregar más fuentes de datos  

---

