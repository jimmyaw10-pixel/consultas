import os
from flask import Flask, render_template_string, request, jsonify
import mysql.connector

app = Flask(__name__)

# --- CONFIGURACIÓN DE CONEXIÓN SEGURA (Variables de Railway) ---
DB_HOST = 'mysql.railway.internal'
DB_USER = os.environ.get('MYSQL_USER') or os.environ.get('MYSQL_ROOT_USER')
DB_PASS = os.environ.get('MYSQL_ROOT_PASSWORD')
DB_NAME = 'cedulas'


@app.route('/', methods=['GET'])
def index():
    """Sirve la interfaz web (frontend)."""
    # El HTML de tu antigua interfaz (simplificado para el ejemplo)
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <title>Consulta de Cédulas (Python)</title>
        <script>
            // JS para llamar a la API interna /api/cedula
            async function buscarCedula() {
                const cedulaId = document.getElementById('cedulaInput').value.trim();
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="loading">Cargando datos...</div>';
                
                try {
                    const response = await fetch('/api/cedula?cedulaId=' + cedulaId);
                    const data = await response.json();
                    
                    if (response.status === 200) {
                        resultsDiv.innerHTML = JSON.stringify(data, null, 2); // Muestra datos
                    } else {
                        resultsDiv.innerHTML = '⚠️ Error: ' + (data.error || 'Cédula no encontrada.');
                    }
                } catch(e) {
                    resultsDiv.innerHTML = '🚨 Error de conexión o JSON inválido.';
                }
            }
        </script>
        <style> /* Tu estilo CSS va aquí */ </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Buscador de Cédulas (Python)</h1>
            <div>
                <input type="text" id="cedulaInput" placeholder="Ingrese el número de cédula">
                <button onclick="buscarCedula()">Buscar</button>
            </div>
            <pre id="results">Ingrese una cédula para comenzar la búsqueda.</pre>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/api/cedula', methods=['GET'])
def get_cedula():
    """Función API para consultar la base de datos."""
    cedula_id = request.args.get('cedulaId')
    
    if not cedula_id:
        return jsonify({'error': 'Cédula no proporcionada.'}), 400

    try:
        # Intenta la conexión
        cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
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
        # Devuelve el error de la DB (solucionando el 500)
        return jsonify({'error': f"Error de la base de datos: {err.msg}"}), 500

if __name__ == '__main__':
    # Usamos el puerto que Railway/Render nos asigna
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
