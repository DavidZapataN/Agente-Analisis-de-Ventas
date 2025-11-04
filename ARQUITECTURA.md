# 🏗️ Arquitectura del Sistema

## 📐 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                          USUARIO                                 │
│           (Pregunta en lenguaje natural)                         │
│                                                                  │
│  Interfaz Web (Streamlit)  o  CLI (Terminal)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    app_streamlit.py / agent/app.py               │
│                     (Capa de Aplicación)                         │
│                                                                  │
│  • Recibe input del usuario                                      │
│  • Mantiene historial de conversación                            │
│  • Gestiona session state (Streamlit)                            │
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
│  │   (Amazon Nova Lite)                              │          │
│  │                                                   │          │
│  │   • Razonamiento de lenguaje natural              │          │
│  │   • System prompt con restricciones               │          │
│  │   • Decisión de qué herramientas usar             │          │
│  │   • Orquestación de acciones                      │          │
│  │   • Generación de respuestas                      │          │
│  └───────────────────────────────────────────────────┘          │
│                             │                                   │
│                             │ (invoca tools con @tool)          │
│                             ▼                                   │
│  ┌───────────────────────────────────────────────────┐          │
│  │              HERRAMIENTAS (Tools)                 │          │
│  │            agent/tools.py                          │         │
│  │                                                    │         │
│  │  [1] query_database(sql_query)                    │          │
│  │  [2] generate_chart(sql, chart_type, title)       │          │
│  │  [3] export_to_file(sql, format)                  │          │
│  │  [4] get_database_schema()                        │          │
│  │                                                    │          │
│  │  Todas usan: sqlite3.connect() directamente       │          │
│  └───────────────────────────────────────────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│  DATOS & CONSULTAS   │              │   VISUALIZACIÓN Y    │
│                      │              │     EXPORTACIÓN      │
│   agent/db.py        │              │   agent/outputs.py   │
│                      │              │                      │
│ • init_db()          │              │ • render_table()     │
│ • query()            │              │ • render_chart()     │
│ • SQLite directo     │              │ • save_file()        │
└──────────┬───────────┘              └──────────┬───────────┘
           │                                     │
           │ (sqlite3.connect)                   │ (matplotlib/pandas)
           │                                     │
           ▼                                     ▼
┌──────────────────────┐              ┌──────────────────────┐
│   SQLite Database    │              │  Archivos Generados  │
│ data/ventas.sqlite   │              │                      │
│                      │              │ • data/grafico_*.png │
│ • Tabla: ventas      │              │ • data/salida_*.csv  │
│ • Datos desde CSV    │              │ • exports/*.xlsx     │
│ • Índices optimizados│              └──────────────────────┘
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
# Conexión directa a SQLite (sin MCP)
import sqlite3
db_path = Path("data/ventas.sqlite")
with sqlite3.connect(db_path) as conn:
    df = pd.read_sql_query(sql_query, conn)
  ↓
# Retorna: DataFrame con los resultados
```

### 4. Generación de Respuesta

```python
# Amazon Nova Lite recibe los datos y genera respuesta natural
"✅ Consulta ejecutada exitosamente. Aquí están los 5 productos más 
vendidos en Medellín:

producto     total
---------    -----
Laptop       150
Mouse        120
Teclado      95
Monitor      80
Webcam       65

📊 Total de filas: 5

El producto más vendido en Medellín es la Laptop con 150 unidades."
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
- Amazon Nova Lite: Modelo LLM (ligero y económico)

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

### 3. **Base de Datos** (`agent/db.py`)

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

**Conexión:**
```python
import sqlite3
from pathlib import Path

DB_PATH = Path("data/ventas.sqlite")

def query(sql: str, params: tuple = ()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)
```

---

### 4. **Visualización** (`agent/outputs.py`)

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
| `boto3` | SDK de AWS para Bedrock |
| `pandas` | Manipulación de datos |
| `matplotlib` | Generación de gráficos |
| `sqlite3` | Base de datos (Python estándar) |
| `streamlit` | Interfaz web interactiva |
| `asyncio` | Programación asíncrona |

---

## 🎯 Ventajas de esta Arquitectura

✅ **Modular**: Cada componente tiene responsabilidad única  
✅ **Extensible**: Fácil agregar nuevas tools con decorador `@tool`  
✅ **Mantenible**: Separación clara de concerns  
✅ **Testeable**: Cada componente se puede probar aislado  
✅ **Flexible**: Soporta múltiples modos de operación (CLI y Web)  
✅ **Simple**: SQLite directo sin dependencias externas complejas  
✅ **Rápido**: Sin overhead de protocolos intermedios  

---

