#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración del agente.
Ejecuta este script para asegurarte de que todo esté correctamente instalado.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Verifica que Python sea >= 3.8"""
    print("\n🔍 Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (Se requiere >= 3.8)")
        return False

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print("\n🔍 Verificando dependencias de Python...")
    
    required = {
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'boto3': 'boto3',
        'strands': 'strands-agents',
        'mcp': 'mcp'
    }
    
    all_ok = True
    for module, package in required.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (faltante)")
            all_ok = False
    
    return all_ok

def check_aws_credentials():
    """Verifica que las credenciales de AWS estén configuradas"""
    print("\n🔍 Verificando credenciales de AWS...")
    
    # Verificar variables de entorno
    has_env = all([
        os.getenv('AWS_ACCESS_KEY_ID'),
        os.getenv('AWS_SECRET_ACCESS_KEY')
    ])
    
    # Verificar archivo de credenciales de AWS CLI
    aws_creds = Path.home() / '.aws' / 'credentials'
    has_file = aws_creds.exists()
    
    if has_env:
        print("   ✅ Credenciales encontradas en variables de entorno")
        return True
    elif has_file:
        print("   ✅ Credenciales encontradas en ~/.aws/credentials")
        return True
    else:
        print("   ⚠️  No se encontraron credenciales de AWS")
        print("      Ejecuta: aws configure")
        print("      O define: AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY")
        return False

def check_bedrock_access():
    """Intenta conectarse a Bedrock"""
    print("\n🔍 Verificando acceso a Amazon Bedrock...")
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        region = os.getenv('AWS_REGION', 'us-east-1')
        bedrock = boto3.client('bedrock', region_name=region)
        
        # Intentar listar modelos
        response = bedrock.list_foundation_models()
        
        # Buscar modelos de Claude
        claude_models = [
            m for m in response.get('modelSummaries', [])
            if 'claude' in m.get('modelId', '').lower()
        ]
        
        if claude_models:
            print(f"   ✅ Conexión exitosa a Bedrock (región: {region})")
            print(f"   ℹ️  Modelos de Claude disponibles: {len(claude_models)}")
            return True
        else:
            print(f"   ⚠️  Conexión exitosa pero no se encontraron modelos de Claude")
            print("      Asegúrate de habilitar el acceso en la consola de Bedrock")
            return False
            
    except NoCredentialsError:
        print("   ❌ No se encontraron credenciales de AWS")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnrecognizedClientException':
            print("   ❌ Credenciales inválidas")
        elif error_code == 'AccessDeniedException':
            print("   ❌ Sin permisos para acceder a Bedrock")
            print("      Agrega la política AmazonBedrockFullAccess a tu usuario IAM")
        else:
            print(f"   ❌ Error: {error_code}")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {str(e)}")
        return False

def check_database():
    """Verifica que exista el dataset y se pueda crear la BD"""
    print("\n🔍 Verificando base de datos...")
    
    # Verificar CSV
    csv_paths = [
        Path('data/ventas.csv'),
        Path('data/ventas_demo.csv'),
        Path('ventas.csv')
    ]
    
    csv_found = None
    for csv_path in csv_paths:
        if csv_path.exists():
            csv_found = csv_path
            break
    
    if csv_found:
        print(f"   ✅ Dataset encontrado: {csv_found}")
    else:
        print("   ❌ No se encontró dataset CSV")
        print("      Crea: data/ventas.csv o data/ventas_demo.csv")
        return False
    
    # Intentar inicializar BD
    try:
        from agent.db import init_db
        db_path = init_db()
        print(f"   ✅ Base de datos inicializada: {db_path}")
        return True
    except Exception as e:
        print(f"   ❌ Error al inicializar BD: {str(e)}")
        return False

def check_mcp_server():
    """Verifica que npx esté disponible para el servidor MCP"""
    print("\n🔍 Verificando servidor MCP (Node.js)...")
    
    import subprocess
    try:
        result = subprocess.run(
            ['npx', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"   ✅ npx disponible (v{result.stdout.strip()})")
            return True
        else:
            print("   ❌ npx no funciona correctamente")
            return False
    except FileNotFoundError:
        print("   ❌ npx no está instalado")
        print("      Instala Node.js: sudo apt install nodejs npm")
        return False
    except Exception as e:
        print(f"   ⚠️  Error al verificar npx: {str(e)}")
        return False

def run_quick_test():
    """Ejecuta una prueba rápida del agente"""
    print("\n🧪 Ejecutando prueba rápida del agente...")
    
    try:
        from agent.bedrock_agent import create_agent
        
        print("   🔄 Creando instancia del agente...")
        agent = create_agent()
        
        print("   🔄 Enviando pregunta de prueba...")
        response = agent.ask_sync("¿Cuántas ventas hay en total?")
        
        if response and not response.startswith("❌"):
            print("   ✅ Agente respondió correctamente")
            print(f"\n   📝 Respuesta:\n{response[:200]}...")
            return True
        else:
            print(f"   ❌ El agente devolvió un error: {response}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error al ejecutar prueba: {str(e)}")
        return False

def main():
    """Ejecuta todas las verificaciones"""
    print("="*80)
    print("🔧 VERIFICACIÓN DE CONFIGURACIÓN - AGENTE DE ANÁLISIS DE VENTAS")
    print("="*80)
    
    results = {
        'Python': check_python_version(),
        'Dependencias': check_dependencies(),
        'Credenciales AWS': check_aws_credentials(),
        'Bedrock': check_bedrock_access(),
        'Base de datos': check_database(),
        'Servidor MCP': check_mcp_server()
    }
    
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    
    for check, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {check}")
    
    all_ok = all(results.values())
    
    if all_ok:
        print("\n🎉 ¡Todo está configurado correctamente!")
        print("\n¿Deseas ejecutar una prueba rápida del agente? (s/n): ", end='')
        
        try:
            response = input().strip().lower()
            if response in ('s', 'si', 'sí', 'y', 'yes'):
                run_quick_test()
        except (EOFError, KeyboardInterrupt):
            pass
        
        print("\n✨ Para iniciar el agente, ejecuta:")
        print("   python -m agent.app")
    else:
        print("\n⚠️  Hay problemas de configuración. Consulta AWS_SETUP.md para más ayuda.")
        print("   cat AWS_SETUP.md")
        return 1
    
    print("\n" + "="*80 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
