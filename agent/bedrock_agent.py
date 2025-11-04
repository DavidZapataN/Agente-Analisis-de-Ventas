# agent/bedrock_agent.py
"""
Agente inteligente usando Strands + Amazon Bedrock.
El LLM decide qué herramientas usar según la pregunta del usuario.
"""

import os
import asyncio
from typing import Optional, List, Callable, Any
from pathlib import Path

from strands import Agent
from strands.models.bedrock import BedrockModel

from agent.tools import (
    query_database,
    generate_chart,
    export_to_file,
    get_database_schema
)
from agent.db import init_db


class SalesAnalysisAgent:
    """
    Agente de análisis de ventas con capacidad de razonamiento.
    Usa Amazon Bedrock (Amazon Lite) para interpretar preguntas y ejecutar acciones.
    """
    
    def __init__(
        self,
        model_id: str = "amazon.nova-lite-v1:0",
        region: str = "us-east-1",
        temperature: float = 0.0
    ):
        """
        Inicializa el agente con el modelo de Bedrock especificado.
        
        Args:
            model_id: ID del modelo en Bedrock (ej: "amazon.nova-lite-v1:0")
            region: Región de AWS donde está habilitado Bedrock
            temperature: Temperatura para el modelo (0.0 = determinístico, 1.0 = creativo)
        """
        self.model_id = model_id
        self.region = region
        self.temperature = temperature
        
        # Inicializar base de datos
        try:
            init_db()
        except Exception as e:
            print(f"⚠️ Advertencia al inicializar DB: {e}")
        
        # Configurar el modelo de Bedrock
        self.model = BedrockModel(
            model_id=model_id,
            region_name=region,
            temperature=temperature
        )
        
        # Las herramientas son las funciones async directamente
        self.tools = [
            query_database,
            generate_chart,
            export_to_file,
            get_database_schema
        ]
        
        # Crear el agente con Strands
        self.agent = Agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self._get_system_prompt()
        )
    
    #El promp del agente se define aca
    def _get_system_prompt(self) -> str:
        """Define el comportamiento del agente"""
        return """Eres un asistente experto en análisis de ventas. Tu trabajo es ayudar a los usuarios 
a analizar datos de ventas mediante consultas SQL y visualizaciones.

**IMPORTANTE - Restricción de Tema:**
SOLO puedes responder preguntas relacionadas con análisis de ventas, consultas a la base de datos, 
gráficos y exportación de datos. Si el usuario pregunta sobre temas no relacionados (recetas, 
entretenimiento, información general, etc.), debes responder amablemente:
"Lo siento, soy un asistente especializado en análisis de ventas. Solo puedo ayudarte con consultas 
sobre la base de datos de ventas, gráficos y reportes. ¿Hay algo sobre las ventas que quieras analizar?"

**Capacidades:**
- Ejecutar consultas SQL en una base de datos SQLite con la tabla 'ventas'
- Generar gráficos (barras, líneas, tortas) para visualizar datos
- Exportar resultados a archivos CSV o Excel
- Interpretar preguntas en lenguaje natural y convertirlas en consultas SQL precisas

**Base de datos:**
La tabla 'ventas' contiene: id, vendedor, sede, producto, cantidad, precio, fecha, total

**Instrucciones:**
1. PRIMERO valida que la pregunta sea sobre análisis de ventas. Si no lo es, rechaza educadamente
2. Cuando el usuario haga una pregunta válida, determina qué información necesita
3. Si necesitas conocer la estructura de la BD, usa get_database_schema
4. Construye la consulta SQL apropiada
5. Si el usuario pide un gráfico, usa generate_chart con el tipo correcto
6. Si el usuario pide guardar/exportar, usa export_to_file
7. Siempre explica brevemente lo que estás haciendo
8. Si hay múltiples interpretaciones, elige la más lógica o pregunta al usuario

**Ejemplos de preguntas típicas:**
- "Top 5 productos más vendidos en Medellín" → Consulta + opcionalmente gráfico de barras
- "Vendedor con más ventas en Bogotá" → Consulta con filtro y ORDER BY
- "Guarda las ventas por vendedor en CSV" → Consulta + export_to_file
- "Muéstrame un gráfico de ventas por mes" → Consulta con DATE + generate_chart tipo line

Sé conciso, preciso y útil. Siempre valida que la consulta SQL sea segura (solo SELECT)."""
    
    async def ask(self, question: str) -> str:
        """
        Procesa una pregunta del usuario y retorna la respuesta.
        
        Args:
            question: Pregunta en lenguaje natural
            
        Returns:
            Respuesta del agente después de ejecutar las herramientas necesarias
        """
        try:
            response = await self.agent.invoke_async(question)
            # La respuesta es un objeto, necesitamos extraer el texto
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                return str(response)
        except Exception as e:
            return f"❌ Error al procesar la pregunta: {str(e)}"
    
    def ask_sync(self, question: str) -> str:
        """Versión síncrona de ask()"""
        return asyncio.run(self.ask(question))


# Función helper para crear una instancia del agente fácilmente
def create_agent(
    model_id: Optional[str] = None,
    region: Optional[str] = None
) -> SalesAnalysisAgent:
    """
    Crea una instancia del agente con configuración por defecto o desde variables de entorno.
    
    Args:
        model_id: ID del modelo de Bedrock (por defecto desde AWS_BEDROCK_MODEL_ID o Amazon Nova-lite)
        region: Región de AWS (por defecto desde AWS_REGION o us-east-1)
    
    Returns:
        Instancia configurada del agente
    """
    model_id = model_id or os.getenv("AWS_BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    region = region or os.getenv("AWS_REGION", "us-east-1")
    
    return SalesAnalysisAgent(model_id=model_id, region=region)


# Ejemplo de uso
if __name__ == "__main__":
    # Crear agente
    agent = create_agent()
    
    # Ejemplos de preguntas
    questions = [
        "¿Cuáles son los 5 productos más vendidos en Medellín?",
        "¿Quién fue el vendedor con más ventas en Bogotá?",
        "Muéstrame un gráfico de barras con las ventas por sede"
    ]
    
    print("🤖 Agente de Análisis de Ventas con Amazon Bedrock\n")
    
    for q in questions:
        print(f"\n❓ Pregunta: {q}")
        print("-" * 80)
        answer = agent.ask_sync(q)
        print(f"💬 Respuesta:\n{answer}\n")
