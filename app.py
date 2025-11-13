import os
from flask import Flask
import mysql.connector
import urllib.parse as urlparse

app = Flask(__name__)

def run_diagnostics():
    """Ejecuta una serie de pruebas para aislar el fallo de conexión."""
    
    # 1. PRUEBA DE CONSISTENCIA DE VARIABLES: Leer la URL Pública
    # Si esta variable no se lee correctamente, la prueba fallará inmediatamente.
    MYSQL_URL_ENV_NAME = 'MYSQL_PUBLIC_URL'
    MYSQL_URL = os.environ.get(MYSQL_URL_ENV_NAME)
    
    results = [f"--- RESULTADOS DEL DIAGNÓSTICO DE CONEXIÓN ---\n"]
    
    # --- PRUEBA 1: LECTURA DE LA VARIABLE DE ENTORNO ---
    if not MYSQL_URL:
        results.append(f"1. ❌ VARIABLE: ¡FALLÓ! La variable '{MYSQL_URL_ENV_NAME}' no fue inyectada o está vacía. El problema es la configuración de Railway. (Debe ser copiada directamente).")
        return "\n".join(results)
    
    results.append(f"1. ✅ VARIABLE: OK. {MYSQL_URL_ENV_NAME} encontrada.")
    
    # --- PRUEBA 2: ANÁLISIS DE LA URL PÚBLICA ---
    try:
        url = urlparse.urlparse(MYSQL_URL)
        DB_HOST = url.hostname
        DB_USER = url.username
        DB_PASS = url.password
        DB_PORT = url.port
        DB_NAME = 'cedulas' # Nombre de la DB
        
        results.append(f"2. ✅ ANÁLISIS: OK. Host: {DB_HOST}, Port: {DB_PORT}, User: {DB_USER}")
        
    except Exception as e:
        results.append(f"2. ❌ ANÁLISIS: ¡FALLÓ! La URL es inválida. Error: {e}")
        return "\n".join(results)

    # --- PRUEBA 3: CONEXIÓN REAL A LA DB ---
    try:
        # Intenta la conexión usando las partes extraídas de la URL
        cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT,
            connection_timeout=7 # Tiempo de espera de 7 segundos
        )
        cnx.close()
        results.append("3. 🟢 CONEXIÓN FINAL: ¡ÉXITO! Conexión a la DB establecida y cerrada correctamente. El sistema funciona.")
        
    except mysql.connector.Error as err:
        if err.errno == 1045:
             results.append(f"3. ⚠️ CONEXIÓN FINAL: ¡FALLÓ! (Acceso Denegado 1045). El host funciona, pero la contraseña/usuario es incorrecta.")
        elif err.errno == 2003 or err.errno == 2005:
            results.append(f"3. ❌ CONEXIÓN FINAL: ¡FALLÓ! ({err.errno}). El host no se puede contactar o resolver (Problema de red de Railway).")
        else:
            results.append(f"3. ❌ CONEXIÓN FINAL: FALLÓ {err.errno}. {err.msg}")
            
    except Exception as e:
        results.append(f"3. ❌ CONEXIÓN FINAL: FALLÓ EXCEPCIÓN. {e}")
        
    return "\n".join(results)

@app.route('/', methods=['GET'])
def diagnostic_page():
    """Página que muestra el resultado de los diagnósticos."""
    output = run_diagnostics()
    # Usamos pre para mantener el formato de texto plano
    return f"<pre>{output}</pre>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
