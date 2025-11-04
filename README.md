# 🤖 Agente de Análisis de Ventas con IA

**Agente inteligente** para análisis de ventas que usa:
- 🧠 **Amazon Bedrock** (Amazon Nova Lite) para razonamiento
- 🔗 **Strands Framework** para orquestación de agentes
- 🗄️ **SQLite** para almacenamiento de datos
- 📊 **Matplotlib** para visualización de datos

El agente interpreta preguntas en lenguaje natural, genera consultas SQL automáticas, 
crea gráficos y exporta resultados, todo sin necesidad de código adicional.

---

## ⚡ Inicio Rápido

```bash
# 1. Instalar dependencias del sistema
sudo apt update && sudo apt install -y python3 python3-venv python3-pip sqlite3

# 2. Clonar y configurar
git clone https://github.com/DavidZapataN/Agente-Analisis-de-ventas.git
cd Agente-Analisis-de-Ventas

# 3. Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configurar AWS Bedrock
aws configure  # Ingresa tus credenciales de AWS

# 5. Inicializar base de datos
python db/init_db.py

# 6. Ejecutar interfaz web (recomendado)
streamlit run app_streamlit.py
```

**¡Listo!** La aplicación se abrirá en http://localhost:8501 🎉

---

## 🎯 Características

✅ **Lenguaje natural**: Pregunta como lo harías a un analista humano  
✅ **SQL automático**: El agente construye las consultas por ti  
✅ **Visualizaciones**: Gráficos de barras, líneas y tortas  
✅ **Exportación**: Guarda resultados en CSV o Excel  
✅ **Seguro**: Validación automática de consultas (solo SELECT)  
✅ **Inteligente**: Usa LLM para decidir qué herramientas ejecutar  

---

## 🚀 Instalación

### 1. Requisitos del sistema

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip sqlite3
```

### 2. Clonar y configurar el proyecto

```bash
git clone <tu-repo>
cd Agente-Analisis-de-Ventas

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias de Python
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar AWS Bedrock

**Opción A: Usar AWS CLI (recomendado)**
```bash
aws configure
# Ingresa: Access Key ID, Secret Access Key, Region (ej: us-east-1)
```

**Opción B: Variables de entorno**
```bash
cp .env.example .env
# Edita .env con tus credenciales de AWS
```

**Importante**: Asegúrate de tener acceso habilitado a Amazon Bedrock en tu cuenta de AWS 
y permisos para usar el modelo `amazon.nova-lite-v1:0`.

### 4. Inicializar la base de datos

```bash
# Inicializar la base de datos desde el CSV
python db/init_db.py

# Verificar que se creó correctamente
sqlite3 data/ventas.sqlite "SELECT COUNT(*) FROM ventas;"
```

**Nota**: La base de datos se crea automáticamente en `data/ventas.sqlite` a partir del archivo `data/ventas_demo.csv`.

---

## 🎮 Uso

### Opción 1: Interfaz Web (Streamlit) 🎨 **RECOMENDADO**

Interfaz visual e interactiva con chat, visualización de gráficos y descarga de archivos:

```bash
./run_streamlit.sh
# O directamente:
streamlit run app_streamlit.py
```

La aplicación se abrirá en: **http://localhost:8501**

**Características de la interfaz:**
- 💬 Chat interactivo con historial
- 📊 Visualización de gráficos en tiempo real
- ⬇️ Descarga directa de gráficos y archivos
- 🎯 Botones con ejemplos rápidos
- ⚙️ Configuración de modelo y temperatura

📖 **Guía completa**: Ver `STREAMLIT_GUIDE.md`

---

### Opción 2: Terminal (CLI)

```bash
python -m agent.app
```

El agente usará Amazon Bedrock para interpretar tus preguntas y decidir qué hacer.

### Ejemplos de preguntas:

```
❓ ¿Cuáles son los 5 productos más vendidos en Medellín?
❓ ¿Quién fue el vendedor con más ventas en Bogotá?
❓ Muéstrame un gráfico de barras con las ventas por sede
❓ Guarda las ventas por vendedor en un archivo CSV
❓ ¿Cuál es el ticket promedio?
❓ Muéstrame un gráfico de líneas con las ventas por mes
```

### Modo Legacy (basado en reglas)

Si prefieres el modo anterior sin LLM:

```bash
export LEGACY_MODE=true
python -m agent.app
```

---

## 📁 Estructura del Proyecto

```
Agente-Analisis-de-Ventas/
├── agent/                     # 🤖 Módulos del agente inteligente
│   ├── app.py                 # Aplicación CLI principal
│   ├── bedrock_agent.py       # ⭐ Agente con Bedrock + Strands (configuración y prompt)
│   ├── tools.py               # ⭐ Herramientas del agente (query, chart, export, schema)
│   ├── db.py                  # Inicialización y gestión de base de datos SQLite
│   ├── outputs.py             # Renderizado de tablas y gráficos (matplotlib)
│   ├── sql_gen.py             # Generador SQL basado en reglas (modo legacy)
│   └── intents.py             # Detección de intenciones (modo legacy)
│
├── data/                      # 📊 Datos y archivos generados
│   ├── ventas_demo.csv        # Dataset de ejemplo
│   ├── ventas.sqlite          # Base de datos SQLite (generada automáticamente)
│   ├── grafico_*.png          # Gráficos generados por el agente
│   └── salida_*.csv           # Archivos CSV exportados
│
├── db/                        # 🗄️ Scripts de base de datos
│   ├── init_db.py             # Script para inicializar la BD desde CSV
│   └── schema.sql             # Esquema SQL de la tabla ventas
│
├── .github/                   # 🐙 Configuración de GitHub
│
├── app_streamlit.py           # 🎨 Interfaz web con Streamlit (RECOMENDADO)
├── test_setup.py              # ✅ Script de verificación de configuración
├── requirements.txt           # 📦 Dependencias de Python
├── .env.example               # 🔐 Plantilla de variables de entorno
├── README.md                  # 📖 Esta documentación
├── ARQUITECTURA.md            # 🏗️ Documentación de arquitectura detallada
└── STREAMLIT_GUIDE.md         # 📘 Guía de uso de la interfaz web
```

### 📝 Archivos Clave:

| Archivo | Descripción | Importancia |
|---------|-------------|-------------|
| `agent/bedrock_agent.py` | Configuración del agente con Strands + Bedrock, define el **system prompt** | ⭐⭐⭐ |
| `agent/tools.py` | Implementación de las 4 herramientas del agente (decorador `@tool`) | ⭐⭐⭐ |
| `app_streamlit.py` | Interfaz web completa con chat y visualizaciones | ⭐⭐⭐ |
| `agent/app.py` | Interfaz CLI, soporta modo legacy y modo inteligente | ⭐⭐ |
| `test_setup.py` | Verificación de dependencias, AWS y BD | ⭐⭐ |

---

## 🛠️ Arquitectura

### Flujo del Agente Inteligente:

```
Usuario → Pregunta en lenguaje natural
    ↓
Agente (Bedrock/Nova Lite) → Analiza la pregunta
    ↓
Decide qué herramientas usar:
    ├─→ query_database()     → Ejecuta SQL en SQLite
    ├─→ generate_chart()     → Crea gráfico con matplotlib
    └─→ export_to_file()     → Guarda CSV/Excel
    ↓
Respuesta al usuario
```

### Herramientas disponibles para el LLM:

1. **`query_database(sql_query)`**: Ejecuta consultas SELECT en la BD
2. **`generate_chart(sql_query, chart_type, title)`**: Genera gráficos (bar/line/pie)
3. **`export_to_file(sql_query, format)`**: Exporta a CSV o Excel
4. **`get_database_schema()`**: Obtiene info del esquema de la BD

El modelo LLM decide **automáticamente** cuál(es) usar según la pregunta.



### Cambiar región de AWS

```bash
AWS_REGION=us-west-2
```

---

## 🧪 Pruebas

### Probar el agente directamente:

```python
from agent.bedrock_agent import create_agent

agent = create_agent()
respuesta = agent.ask_sync("¿Top 5 productos más vendidos?")
print(respuesta)
```

### Probar las herramientas individualmente:

```python
from agent.tools import query_database_sync, generate_chart_sync

# Ejecutar SQL
resultado = query_database_sync("SELECT * FROM ventas LIMIT 5")
print(resultado)

# Generar gráfico
chart_path = generate_chart_sync(
    "SELECT sede, SUM(total) AS ventas FROM ventas GROUP BY sede",
    chart_type="bar",
    title="Ventas por Sede"
)
print(chart_path)
```

---

