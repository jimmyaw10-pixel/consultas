import os
from flask import Flask, jsonify
import mysql.connector
import urllib.parse as urlparse

app = Flask(__name__)

def run_diagnostics():
    """Ejecuta una serie de pruebas para aislar el fallo de conexión."""
    
    # Lista para almacenar los resultados de las pruebas
    results = []

    # --- PRUEBA 1: VERIFICAR LECTURA DE CREDENCIALES ---
    # Usamos las variables que acabas de configurar manualmente
    db_user_val = os.environ.get('MYSQL_USER')
    db_pass_val = os.environ.get('MYSQL_ROOT_PASSWORD')
    
    if db_user_val and db_pass_val:
        results.append(f"1. ✅ Credenciales: OK. User: {db_user_val}, Pass: (Hidden)")
    else:
        results.append("1. ❌ Credenciales: ¡FALLÓ! No se encontraron MYSQL_USER o MYSQL_ROOT_PASSWORD. El problema es la configuración de VARIABLES de Railway.")
        # No podemos continuar sin credenciales

    # --- PRUEBA 2: VERIFICAR HOST INTERNO (El que fallaba) ---
    internal_host = 'mysql.railway.internal'
    try:
        # Intenta una conexión básica de MySQL al host interno (sin usar el usuario/pass)
        # Esto prueba la resolución DNS.
        mysql.connector.connect(
            host=internal_host,
            database='cedulas', 
            user=db_user_val, 
            password=db_pass_val, 
            connection_timeout=5 # Tiempo de espera corto
        )
        results.append("2. ✅ Host Interno: OK. Pudo conectar a 'mysql.railway.internal'.")
    except mysql.connector.Error as err:
        if err.errno == 2005: # 2005 es "Unknown MySQL server host"
             results.append(f"2. ❌ Host Interno: ¡FALLÓ DNS! Unknown MySQL server host '{internal_host}' ({err.errno}). El problema es la red interna de Railway.")
        elif err.errno == 2003: # 2003 es "Can't connect to MySQL server"
             results.append(f"2. ❌ Host Interno: ¡FALLÓ CONEXIÓN! Can't connect to MySQL server ({err.errno}). El host existe, pero la conexión fue rechazada.")
        elif err.errno == 1045: # 1045 es "Access denied"
             results.append("2. ✅ Host Interno: OK. Pudo conectar. (Pero Access Denied - Credenciales son el problema).")
        else:
            results.append(f"2. ❌ Host Interno: FALLÓ {err.errno}. {err.msg}")
    except Exception as e:
        results.append(f"2. ❌ Host Interno: FALLÓ EXCEPCIÓN. {e}")


    # --- PRUEBA 3: VERIFICAR CONEXIÓN CON URL PÚBLICA (Solución final) ---
    public_url = os.environ.get('MYSQL_PUBLIC_URL')
    
    if public_url:
        try:
            url = urlparse.urlparse(public_url)
            
            # Intenta la conexión
            mysql.connector.connect(
                host=url.hostname,
                port=url.port,
                database='cedulas', 
                user=url.username, 
                password=url.password,
                connection_timeout=5
            )
            results.append(f"3. ✅ URL Pública: OK. Conexión exitosa a '{url.hostname}'.")
        except mysql.connector.Error as err:
            results.append(f"3. ❌ URL Pública: ¡FALLÓ! {err.msg} ({err.errno}). La URL no funciona.")
        except Exception as e:
            results.append(f"3. ❌ URL Pública: FALLÓ EXCEPCIÓN. {e}")
    else:
        results.append("3. ❌ URL Pública: ¡FALLÓ! Variable MYSQL_PUBLIC_URL no encontrada en el entorno.")
        
    return "\n".join(results)

@app.route('/', methods=['GET'])
def diagnostic_page():
    """Página que muestra el resultado de los diagnósticos."""
    output = run_diagnostics()
    # Usamos pre para mantener el formato de texto plano
    return f"<pre>--- RESULTADOS DEL DIAGNÓSTICO DE RAILWAY ---\n\n{output}</pre>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
