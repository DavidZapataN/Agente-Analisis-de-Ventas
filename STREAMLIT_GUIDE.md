# 🎨 Guía de Uso - Interfaz Web con Streamlit

## 📋 Descripción

La interfaz web de Streamlit proporciona una experiencia visual e interactiva para el Agente de Análisis de Ventas, permitiendo hacer preguntas, ver gráficos en tiempo real y descargar resultados.

---

## 🚀 Instalación

### 1. Instalar Streamlit

```bash
pip install streamlit pillow
```

### 2. Verificar instalación

```bash
streamlit --version
```

---

## ▶️ Cómo Ejecutar

### Opción A: Script automático (recomendado)

```bash
./run_streamlit.sh
```

### Opción B: Comando directo

```bash
streamlit run app_streamlit.py
```

### Opción C: Con configuración personalizada

```bash
streamlit run app_streamlit.py --server.port 8501 --server.address localhost
```

La aplicación se abrirá automáticamente en tu navegador en: **http://localhost:8501**

---

## 🎯 Características de la Interfaz

### 1. **Chat Interactivo**
- Escribe tus preguntas en lenguaje natural
- Historial de conversación persistente durante la sesión
- Respuestas del agente en tiempo real

### 2. **Sidebar Informativo**
- **Estado del Sistema**: Verifica que la BD y AWS estén configurados
- **Ejemplos Rápidos**: Botones con preguntas pre-escritas
- **Configuración**: Ajusta modelo y temperatura
- **Limpiar Historial**: Resetea la conversación

### 3. **Visualización de Gráficos**
- Los gráficos se muestran automáticamente en la interfaz
- Opción de descarga en formato PNG
- Visualización responsive (se adapta al tamaño de pantalla)

### 4. **Descarga de Archivos**
- Archivos CSV y Excel generados se pueden descargar directamente
- Botones de descarga aparecen automáticamente

### 5. **Indicadores de Estado**
- Spinners mientras el agente procesa
- Mensajes de éxito/error claros
- Contador de mensajes en el footer

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Consulta Simple

1. Escribe en el chat: **"¿Cuáles son los 5 productos más vendidos?"**
2. El agente ejecutará la consulta
3. Verás los resultados en formato tabla

### Ejemplo 2: Generar Gráfico

1. Haz clic en el botón: **"Muéstrame un gráfico de barras de ventas por sede"**
2. El agente generará el gráfico
3. El gráfico aparecerá debajo de la respuesta
4. Haz clic en "⬇️ Descargar" para guardarlo

### Ejemplo 3: Exportar Datos

1. Pregunta: **"Exporta las ventas por vendedor a CSV"**
2. El agente genera el archivo
3. Aparece un botón de descarga
4. Haz clic para descargar el CSV

---

## ⚙️ Configuración Avanzada

### Cambiar el Modelo

En el sidebar, selecciona entre:
- **Claude 3.5 Sonnet** (recomendado) - Más preciso
- **Claude 3 Haiku** - Más rápido y económico

### Ajustar Temperatura

- **0.0** - Respuestas determinísticas y consistentes
- **0.5** - Balance entre creatividad y precisión
- **1.0** - Respuestas más creativas y variadas

---

## 🎨 Personalización

### Modificar Colores y Estilos

Edita el CSS en `app_streamlit.py`:

```python
st.markdown("""
    <style>
    .chat-message.user {
        background-color: #e3f2fd;  /* Cambia este color */
    }
    </style>
""", unsafe_allow_html=True)
```

### Agregar Más Ejemplos

En el sidebar, agrega ejemplos a la lista:

```python
ejemplos = [
    "Tu nueva pregunta aquí",
    # ... más ejemplos
]
```

---

## 📊 Estructura de la Interfaz

```
┌─────────────────────────────────────────────────────────┐
│  🤖 Agente Inteligente de Análisis de Ventas           │
│  Powered by Amazon Bedrock + Strands                    │
├──────────────────┬──────────────────────────────────────┤
│                  │                                      │
│  SIDEBAR         │  ÁREA DE CHAT                        │
│                  │                                      │
│  ℹ️ Información  │  👤 Usuario: ¿Top 5 productos?      │
│  ✅ Estado       │                                      │
│                  │  🤖 Asistente: Aquí están...         │
│  💡 Ejemplos     │  [Tabla de resultados]               │
│  [Botones]       │  [Gráfico]                           │
│                  │  [Botón Descargar]                   │
│  ⚙️ Config       │                                      │
│  [Modelo]        │  ┌──────────────────────────┐        │
│  [Temperatura]   │  │ Escribe tu pregunta...   │        │
│                  │  └──────────────────────────┘        │
│  🗑️ Limpiar      │                                      │
│                  │                                      │
└──────────────────┴──────────────────────────────────────┘
│  📊 Total mensajes: 4  │  🤖 Modelo: Claude 3.5  │
└────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### "streamlit: command not found"

**Solución:**
```bash
pip install --upgrade streamlit
# O usa:
python3 -m streamlit run app_streamlit.py
```

### "No module named streamlit"

**Solución:**
Asegúrate de estar en el entorno virtual:
```bash
source .venv/bin/activate
pip install streamlit
```

### La aplicación no se abre en el navegador

**Solución:**
Abre manualmente: http://localhost:8501

### Error de credenciales AWS

**Solución:**
```bash
aws configure
# Ingresa tus credenciales
```

### Los gráficos no se muestran

**Solución:**
```bash
pip install pillow matplotlib
```

---

## 🚦 Puertos y Configuración

### Puerto por defecto
- **8501** - Puerto estándar de Streamlit

### Cambiar puerto
```bash
streamlit run app_streamlit.py --server.port 8080
```

### Deshabilitar autorecarga
```bash
streamlit run app_streamlit.py --server.runOnSave false
```

### Modo headless (sin navegador)
```bash
streamlit run app_streamlit.py --server.headless true
```

---

## 📱 Acceso desde Otros Dispositivos

### En la misma red local

```bash
streamlit run app_streamlit.py --server.address 0.0.0.0
```

Luego accede desde: `http://<tu-ip-local>:8501`

Para encontrar tu IP:
```bash
hostname -I
```

---

## 💾 Datos Persistentes

### Historial de Conversación
- Se mantiene durante la sesión
- Se pierde al recargar la página
- Usa el botón "🗑️ Limpiar Historial" para resetear

### Archivos Generados
- Los gráficos se guardan en `data/grafico_*.png`
- Los CSV/Excel en `data/salida_*`
- Puedes acceder a ellos incluso después de cerrar la app

---

## 🎯 Atajos de Teclado

- **Enter** - Enviar mensaje
- **Ctrl + R** - Recargar la aplicación
- **Ctrl + C** (en terminal) - Detener la aplicación

---

## 📈 Rendimiento

### Optimizaciones
- El agente se inicializa una sola vez (cached en session_state)
- Los gráficos se detectan por timestamp (últimos 10 segundos)
- Las imágenes se cargan on-demand

### Consumo de Recursos
- **Memoria**: ~200-300 MB
- **CPU**: Bajo (excepto al generar gráficos)
- **Red**: Solo para llamadas a Bedrock

---

## 🔐 Seguridad

### Variables de Entorno
Las credenciales de AWS se leen de variables de entorno, no se almacenan en la app.

### Validación SQL
Todas las consultas se validan antes de ejecutarse (solo SELECT permitido).

---

## 📚 Recursos Adicionales

- [Documentación de Streamlit](https://docs.streamlit.io/)
- [Galería de Streamlit](https://streamlit.io/gallery)
- [Componentes de Streamlit](https://streamlit.io/components)

---

## 🎉 ¡Listo para Usar!

Ejecuta:
```bash
./run_streamlit.sh
```

Y disfruta de tu interfaz web para análisis de ventas con IA! 🚀📊
