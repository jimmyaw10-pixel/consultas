import os
from flask import Flask, render_template_string, request, jsonify
import mysql.connector
import urllib.parse as urlparse # Necesario para analizar la URL pública

app = Flask(__name__)

# --- 1. CONFIGURACIÓN DE CONEXIÓN FINAL Y SEGURA ---
# Usamos la URL pública de Railway, que es la única que funciona sin fallos de DNS interno.
MYSQL_URL = os.environ.get('MYSQL_PUBLIC_URL')

DB_HOST = None
DB_USER = None
DB_PASS = None
DB_PORT = None
DB_NAME = 'cedulas' # El nombre de tu base de datos (fijo)

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
        # Si falla, DB_HOST seguirá siendo None
        
# --- 2. LÓGICA DE LA API ---

@app.route('/', methods=['GET'])
def index():
    """Sirve la interfaz web (frontend) y el formulario."""
    
    # ⚠️ NOTA: El HTML incluye el JS para llamar a la API /api/cedula
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consulta de Cédulas (Python Final)</title>
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
            <h1>🔍 Buscador de Cédulas (Python Final)</h1>
            <div>
                <input type="text" id="cedulaInput" placeholder="Ingrese el número de cédula (ej: 100)" maxlength="10">
                <button onclick="buscarCedula()">Buscar</button>
            </div>
            <div id="results">
                Ingrese una cédula para comenzar la búsqueda.
            </div>
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
                        // Muestra el error de conexión de la DB o 404
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
    
    if not DB_HOST:
        return jsonify({'error': 'Error de configuración: URL de MySQL no encontrada o falló el análisis.'}), 500

    if not cedula_id:
        return jsonify({'error': 'Cédula no proporcionada.'}), 400

    try:
        # Intenta la conexión usando las partes extraídas de la URL pública
        cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT
        )
        cursor = cnx.cursor(dictionary=True)
        
        # Consulta SQL optimizada
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
        # Devuelve el error de la DB (por ejemplo, si la contraseña es incorrecta)
        return jsonify({'error': f"Error de la base de datos: {err.msg}"}), 500
    except Exception as e:
        # Para cualquier otro error inesperado del servidor
        return jsonify({'error': f"Error interno del servidor: {e}"}), 500


if __name__ == '__main__':
    # Usamos el puerto que Railway nos asigna
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
