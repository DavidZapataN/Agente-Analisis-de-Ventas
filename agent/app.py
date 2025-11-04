# agent/app.py
"""
Aplicación principal del agente de análisis de ventas.
Ahora usa un agente inteligente con Amazon Bedrock + Strands.
"""

import os
from agent.bedrock_agent import create_agent

# Mantener compatibilidad con versión anterior (basada en reglas)
LEGACY_MODE = os.getenv("LEGACY_MODE", "false").lower() == "true"

if LEGACY_MODE:
    # Importar versión anterior si se activa modo legacy
    from agent.sql_gen import generate_sql, is_sql_safe
    from agent.db import init_db, query
    from agent.outputs import render_table, render_chart, save_file

    def answer(q: str):
        init_db()  # prepara SQLite desde CSV (silencioso)
        sql, (mode, params) = generate_sql(q)

        if not is_sql_safe(sql):
            print("❌ Consulta no permitida.")
            return

        df = query(sql, params)

        if mode == "text":
            if df.empty:
                print("⚠️  Sin resultados.")
                return
            row = df.iloc[0]
            if {"producto","total_cantidad"}.issubset(df.columns):
                print(f"🏆 Producto líder: {row['producto']} con {int(row['total_cantidad'])} unidades")
            elif {"vendedor","total_ventas"}.issubset(df.columns):
                print(f"🏆 Vendedor líder: {row['vendedor']} con total_ventas={int(row['total_ventas']):,}")
            elif "ticket_promedio" in df.columns:
                print(f"🧾 Ticket promedio: {float(row['ticket_promedio']):,.2f}")
            elif "precio_promedio" in df.columns:
                print(f"💲 Precio promedio: {float(row['precio_promedio']):,.2f}")
            elif "total_ventas" in df.columns:
                print(f"💰 Total de ventas: {int(row['total_ventas']):,}")
            else:
                render_table(df)
            return

        if mode in ("bar","line","pie"):
            if df.empty or df.shape[1] < 2:
                print("⚠️  Sin datos para graficar.")
                return
            x, y = df.columns[0], df.columns[1]
            render_chart(df, chart=mode, x=x, y=y, title=q)
            render_table(df)
            return

        if mode in ("csv","excel"):
            if df.empty:
                print("⚠️  Nada que exportar.")
                return
            path = save_file(df, mode=mode)
            print(f"📎 Archivo generado: {path}")
            return

        # por defecto: tabla
        render_table(df)
else:
    # Nueva versión: agente inteligente con Bedrock
    def answer(q: str):
        """
        Procesa una pregunta usando el agente inteligente.
        El LLM decide qué herramientas usar.
        """
        try:
            # Crear instancia del agente (singleton podría optimizarse)
            agent = create_agent()
            
            # Procesar pregunta
            response = agent.ask_sync(q)
            
            # Mostrar respuesta
            print("\n" + "="*80)
            print(response)
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            print("💡 Asegúrate de tener configuradas las credenciales de AWS.")
            print("   Ejecuta: aws configure")
            print("   O define las variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION\n")


def main():
    """Loop principal de interacción con el usuario"""
    
    print("\n" + "="*80)
    if LEGACY_MODE:
        print("🔧 MODO LEGACY (basado en reglas)")
        print("   Para usar el agente inteligente, desactiva LEGACY_MODE")
    else:
        print("🤖 AGENTE INTELIGENTE DE ANÁLISIS DE VENTAS")
        print("   Powered by Amazon Bedrock + Strands")
    print("="*80)
    print("\n💡 Ejemplos de preguntas:")
    print("   - ¿Cuáles son los 5 productos más vendidos en Medellín?")
    print("   - ¿Quién fue el vendedor con más ventas en Bogotá?")
    print("   - Muéstrame un gráfico de barras con las ventas por sede")
    print("   - Guarda las ventas por vendedor en un archivo CSV")
    print("   - ¿Cuál es el ticket promedio?")
    print("\n" + "="*80 + "\n")
    
    try:
        while True:
            q = input("❓ Ingresa tu consulta (o 'salir'): ").strip()
            if not q:
                continue
            if q.lower() in ('salir', 'exit', 'quit'):
                print("\n👋 ¡Hasta luego!\n")
                break
            
            answer(q)
            
    except (EOFError, KeyboardInterrupt):
        print("\n\n👋 ¡Hasta luego!\n")


if __name__ == "__main__":
    main()
