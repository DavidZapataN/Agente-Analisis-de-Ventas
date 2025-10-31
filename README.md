# 🧠 Agente de Análisis de Ventas
# Agente-Analisis-de-Ventas
Agente inteligente para análisis de ventas con lenguaje natural, consultas SQL automáticas y visualización de resultados.

# Asegúrate de tener instalados:

sudo apt update
sudo apt install -y python3 python3-venv python3-pip sqlite3 nodejs npm

# Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Instalar el servidor MCP (Node.js)

sudo npm install -g @executeautomation/database-server

# Generar y cargar la base de datos

python db/init_db.py
sqlite3 db/ventas.db "SELECT COUNT(*) FROM ventas;"

# Ejecución
# Terminal 1 — Iniciar el servidor MCP

cd ~/Blend/AgenteAnalisisDeVentas
source .venv/bin/activate
npx -y @executeautomation/database-server db/ventas.db

# Terminal 2 — Ejecutar el agente
cd ~/Blend/AgenteAnalisisDeVentas
source .venv/bin/activate
python -m agent.app

