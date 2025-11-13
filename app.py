import os
from flask import Flask, render_template_string, request, jsonify
import mysql.connector
import urllib.parse as urlparse

app = Flask(__name__)

# --- 1. CONFIGURACIÓN DE CONEXIÓN CONSISTENTE (Probada en Diagnóstico) ---
# Leemos la variable que funciona (debe ser el mismo nombre que la que inyectaste manualmente)
MYSQL_URL_ENV_NAME = 'MYSQL_PUBLIC_URL'
MYSQL_URL = os.environ.get(MYSQL_URL_ENV_NAME)

DB_HOST = None
DB_USER = None
DB_PASS = None
DB_PORT = None
DB_NAME = 'cedulas' # Nombre de tu base de datos

if MYSQL_URL:
    try:
        # Analiza la URL para obtener las partes (host, user, pass, port)
        url = urlparse.urlparse(MYSQL_URL)
        DB_HOST = url.hostname
        DB_USER = url.username
        DB_PASS = url.password
        DB_PORT = url.port

    except Exception as e:
        print(f"Error al analizar la URL de MySQL: {e}")
        
# --- 2. LÓGICA DE LA API Y FRONTEND ---

@app.route('/', methods=['GET'])
def index():
    """Sirve la interfaz web (frontend)."""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consulta de Cédulas (Final)</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; }
            .container { max-width: 600px; margin: 0 auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 20px; }
            input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
            button { width: 25%; padding: 10px; background-color: #5cb85c; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 5px; }
            button:hover { background-color: #4cae4c; }
            #results { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background-color: #e9e9e9; white-space: pre-wrap; }
            .loading { text-align: center; color: #777; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Buscador de Cédulas (Producción)</h1>
            <div>
                <input type="text" id="cedulaInput" placeholder="Ingrese el número de cédula (ej: 100)" maxlength="10">
                <button onclick="buscarCedula()">Buscar</button>
            </div>
            <pre id="results">Ingrese una cédula para comenzar la búsqueda.</pre>
        </div>

        <script>
            async function buscarCedula() {
                const cedulaId = document.getElementById('cedulaInput').value.trim();
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="loading">Cargando datos...</div>';

                if (!cedulaId) {
                    resultsDiv.innerHTML = 'Ingrese un número de cédula válido.';
                    return;
                }

                try {
                    const response = await fetch('/api/cedula?cedulaId=' + cedulaId);
                    const data = await response.json();

                    if (response.status === 200) {
                        resultsDiv.innerHTML = formatResults(data);
                    } else {
                        // Muestra el error de la DB o 404
                        resultsDiv.innerHTML = `⚠️ Error: ${data.error || data.message || 'Fallo desconocido'}`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = '🚨 Error de red o respuesta JSON inválida.';
                }
            }

            function formatResults(data) {
                const fieldMap = {
                    'ANINuip': 'Cédula', 'ANIApellido1': 'Primer Apellido', 'ANIApellido2': 'Segundo Apellido',
                    'ANINombre1': 'Primer Nombre', 'ANINombre2': 'Segundo Nombre', 'ANINombresPadre': 'Nombre del Padre',
                    'ANINombresMadre': 'Nombre de la Madre', 'ANIFchNacimiento': 'Fecha de Nacimiento',
                    'ANIFchExpedicion': 'Fecha de Expedición'
                };
                let html = '<h3>✅ Resultado Encontrado</h3>';
                for (const key in fieldMap) {
                    let value = data[key] !== null ? data[key] : 'N/A';
                    html += `<div class="data-item"><span class="data-label">${fieldMap[key]}:</span> <span class="data-value">${value}</span></div>`;
                }
                return html;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/api/cedula', methods=['GET'])
def get_cedula():
    """Función API para consultar la base de datos."""
    cedula_id = request.args.get('cedulaId')
    
    # Verifica que la conexión funcione antes de intentar la DB
    if not DB_HOST:
        return jsonify({'error': f"Error de configuración: Variable de entorno '{MYSQL_URL_ENV_NAME}' no encontrada."}), 500

    if not cedula_id:
        return jsonify({'error': 'Cédula no proporcionada.'}), 400

    try:
        # CONEXIÓN PROBADA EXITOSAMENTE
        cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT
        )
        cursor = cnx.cursor(dictionary=True)
        
        # Consulta SQL
        query = "SELECT * FROM ani_filtered WHERE ANINuip = %s LIMIT 1"
        cursor.execute(query, (cedula_id,))
        result = cursor.fetchone()
        
        cursor.close()
        cnx.close()

        if result:
            return jsonify(result), 200
        else:
            return jsonify({'message': 'Cédula no encontrada.'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': f"Error de la base de datos: {err.msg}"}), 500
    except Exception as e:
        return jsonify({'error': f"Error interno del servidor: {e}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
