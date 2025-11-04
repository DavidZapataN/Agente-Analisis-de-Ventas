# app_streamlit.py
"""
Interfaz web con Streamlit para el Agente de Análisis de Ventas.
"""

import streamlit as st
import asyncio
from pathlib import Path
import os
from datetime import datetime
from PIL import Image

from agent.bedrock_agent import create_agent
from agent.db import init_db

# Configuración de la página
st.set_page_config(
    page_title="Agente de Análisis de Ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e3f2fd;
    }
    .chat-message.assistant {
        background-color: #f5f5f5;
    }
    .chat-message .message-content {
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("🤖 Agente Inteligente de Análisis de Ventas")
st.markdown("**Powered by Amazon Bedrock + Strands**")
st.divider()

# Sidebar con información
with st.sidebar:
    st.header("ℹ️ Información")
    
    # Estado de la configuración
    st.subheader("Estado del Sistema")
    
    try:
        init_db()
        st.success("✅ Base de datos conectada")
    except Exception as e:
        st.error(f"❌ Error en BD: {str(e)}")
    
    # Verificar credenciales AWS
    if os.getenv("AWS_ACCESS_KEY_ID"):
        st.success("✅ AWS configurado")
    else:
        st.warning("⚠️ Credenciales AWS no encontradas")
    
    st.divider()
    
    # Ejemplos de preguntas
    st.subheader("💡 Ejemplos de preguntas")
    ejemplos = [
        "¿Cuáles son los 5 productos más vendidos?",
        "¿Quién fue el vendedor con más ventas en Bogotá?",
        "Muéstrame un gráfico de barras de ventas por sede",
        "Exporta las ventas por vendedor a CSV",
        "¿Cuál es el ticket promedio?",
        "Ventas por mes en gráfico de líneas"
    ]
    
    for ejemplo in ejemplos:
        if st.button(ejemplo, key=f"btn_{ejemplo[:20]}", use_container_width=True):
            st.session_state.pregunta_seleccionada = ejemplo
    
    st.divider()
    
    
    temperatura = st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="0 = Determinístico, 1 = Creativo"
    )
    
    if st.button("🗑️ Limpiar Historial", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Inicializar el historial de mensajes en session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializar el agente en session_state
if "agent" not in st.session_state:
    with st.spinner("🔄 Inicializando agente..."):
        try:
            # create_agent() ya maneja el modelo por defecto desde:
            # 1. Variable de entorno AWS_BEDROCK_MODEL_ID
            # 2. O usa "amazon.nova-lite-v1:0" por defecto
            st.session_state.agent = create_agent()
            st.success("✅ Agente listo", icon="🤖")
        except Exception as e:
            st.error(f"❌ Error al inicializar agente: {str(e)}")
            st.stop()

# Mostrar el historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Mostrar imágenes si hay
        if "images" in message and message["images"]:
            cols = st.columns(len(message["images"]))
            for idx, img_path in enumerate(message["images"]):
                with cols[idx]:
                    if Path(img_path).exists():
                        st.image(img_path, use_container_width=True)

# Input del usuario
pregunta = st.chat_input("Escribe tu pregunta sobre análisis de ventas...")

# Si hay una pregunta seleccionada del sidebar, usarla
if "pregunta_seleccionada" in st.session_state:
    pregunta = st.session_state.pregunta_seleccionada
    del st.session_state.pregunta_seleccionada

# Procesar la pregunta
if pregunta:
    # Agregar mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": pregunta})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(pregunta)
    
    # Mostrar respuesta del asistente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("🤔 Pensando..."):
            try:
                # Ejecutar el agente de forma asíncrona
                async def get_response():
                    return await st.session_state.agent.ask(pregunta)
                
                respuesta = asyncio.run(get_response())
                
                # Mostrar la respuesta
                message_placeholder.markdown(respuesta)
                
                # Buscar imágenes generadas recientemente
                imagenes = []
                data_dir = Path("data")
                if data_dir.exists():
                    # Buscar gráficos generados en los últimos 10 segundos
                    now = datetime.now().timestamp()
                    for img_file in data_dir.glob("grafico_*.png"):
                        if now - img_file.stat().st_mtime < 10:  # Últimos 10 segundos
                            imagenes.append(str(img_file))
                
                # Mostrar imágenes si hay
                if imagenes:
                    st.divider()
                    st.subheader("📊 Gráficos Generados")
                    cols = st.columns(len(imagenes))
                    for idx, img_path in enumerate(imagenes):
                        with cols[idx]:
                            st.image(img_path, use_container_width=True)
                            # Botón de descarga
                            with open(img_path, "rb") as f:
                                st.download_button(
                                    label="⬇️ Descargar",
                                    data=f,
                                    file_name=Path(img_path).name,
                                    mime="image/png",
                                    key=f"download_{Path(img_path).name}"
                                )
                
                # Buscar archivos CSV/Excel generados recientemente
                archivos = []
                for ext in ["csv", "xlsx"]:
                    for archivo in data_dir.glob(f"salida_*.{ext}"):
                        if now - archivo.stat().st_mtime < 10:  # Últimos 10 segundos
                            archivos.append(str(archivo))
                
                # Mostrar archivos si hay
                if archivos:
                    st.divider()
                    st.subheader("📎 Archivos Generados")
                    for archivo in archivos:
                        with open(archivo, "rb") as f:
                            st.download_button(
                                label=f"⬇️ Descargar {Path(archivo).name}",
                                data=f,
                                file_name=Path(archivo).name,
                                mime="text/csv" if archivo.endswith(".csv") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"download_{Path(archivo).name}"
                            )
                
                # Agregar respuesta al historial
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": respuesta,
                    "images": imagenes
                })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**📊 Total de mensajes:** " + str(len(st.session_state.messages)))
with col2:
    st.markdown("**🤖 Modelo:** Amazon Nova-lite")
with col3:
    st.markdown("**🔗 Framework:** Strands + Bedrock")
