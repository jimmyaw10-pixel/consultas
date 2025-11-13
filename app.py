import os
from flask import Flask, render_template_string, request, jsonify
import mysql.connector
import urllib.parse as urlparse
from datetime import datetime
from dateutil.relativedelta import relativedelta # Librería para cálculo de edad

app = Flask(__name__)

# --- CONFIGURACIÓN DE CONEXIÓN (PROBADA EN DIAGNÓSTICO) ---
# Leemos la variable que funciona (que inyectaste manualmente)
MYSQL_URL_ENV_NAME = 'MYSQL_PUBLIC_URL'
MYSQL_URL = os.environ.get(MYSQL_URL_ENV_NAME)

DB_HOST = None
DB_USER = None
DB_PASS = None
DB_PORT = None
DB_NAME = 'cedulas' 

if MYSQL_URL:
    try:
        url = urlparse.urlparse(MYSQL_URL)
        DB_HOST = url.hostname
        DB_USER = url.username
        DB_PASS = url.password
        DB_PORT = url.port
    except Exception as e:
        print(f"Error al analizar la URL de MySQL: {e}")

# --- FUNCIONES DE FORMATO Y CÁLCULO (NUEVAS) ---

def calcular_edad(fecha_nacimiento):
    """Calcula la edad a partir de la fecha de nacimiento."""
    if not fecha_nacimiento:
        return "N/A"
    
    # Asegurarse de que el input es un objeto datetime o una cadena válida
    if isinstance(fecha_nacimiento, str):
        try:
            fn = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        except ValueError:
            return "N/A"
    else:
        fn = fecha_nacimiento
        
    now = datetime.now()
    edad = relativedelta(now, fn)
    return f"{edad.years} años"

def formatear_fecha(fecha):
    """Formatea la fecha a día / mes(ABR) / año."""
    if not fecha:
        return "N/A"
        
    if isinstance(fecha, str):
        try:
            dt = datetime.strptime(fecha, '%Y-%m-%d')
        except ValueError:
            return str(fecha)
    else:
        dt = fecha
        
    meses_abreviados = {
        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 
        7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
    }
    
    mes_abr = meses_abreviados.get(dt.month, 'N/A')
    # Se añade el 0 a los días/meses de un dígito para el formato '02'
    return f"{dt.day:02d} / {dt.month:02d}({mes_abr}) / {dt.year}"


# --- LÓGICA DE LA API Y FRONTEND ---

@app.route('/', methods=['GET'])
def index():
    """Sirve la interfaz web (frontend) con el nuevo formato."""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consulta de Cédulas (Producción)</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; }
            .container { max-width: 600px; margin: 0 auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 20px; }
            input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
            button { width: 25%; padding: 10px; background-color: #5cb85c; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 5px; }
            button:hover { background-color: #4cae4c; }
            #results { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background-color: #e9e9e9; white-space: pre-wrap; line-height: 1.6; }
            #results strong { display: inline-block; width: 150px; }
            .loading { text-align: center; color: #777; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Buscador de Cédulas (Final)</h1>
            <div>
                <input type="text" id="cedulaInput" placeholder="Ingrese el número de cédula" maxlength="10">
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
                        resultsDiv.innerHTML = `⚠️ Error: ${data.error || data.message || 'Fallo desconocido'}`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = '🚨 Error de red o respuesta JSON inválida.';
                }
            }

            function formatResults(data) {
                // El orden lo dictamos aquí, ya que los datos están pre-formateados por Python
                let html = '<h3>✅ Información Encontrada</h3>';
                
                // Nombres y Apellidos
                html += `<p><strong>Cédula:</strong> ${data['Cédula']}</p>`;
                html += `<p><strong>Nombres:</strong> ${data['Nombres']}</p>`;
                html += `<p><strong>Apellidos:</strong> ${data['Apellidos']}</p>`;
                html += `<hr style="border: 0.5px solid #ccc;">`;
                
                // Fechas y Edad
                html += `<p><strong>Fch. Nacimiento:</strong> ${data['Fecha de Nacimiento']}</p>`;
                html += `<p><strong>Fch. Expedición:</strong> ${data['Fecha de Expedicion']}</p>`;
                html += `<p><strong>Edad Actual:</strong> ${data['Edad']}</p>`;
                
                return html;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/api/cedula', methods=['GET'])
def get_cedula():
    """Función API para consultar la base de datos y formatear los resultados."""
    cedula_id = request.args.get('cedulaId')
    
    # Verifica que la conexión funcione
    if not DB_HOST:
        return jsonify({'error': f"Error de configuración: Variable de entorno '{MYSQL_URL_ENV_NAME}' no encontrada."}), 500

    if not cedula_id:
        return jsonify({'error': 'Cédula no proporcionada.'}), 400

    try:
        # Conexión PROBADA EXITOSAMENTE
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
            # --- MANEJO Y FORMATO DE DATOS FINALES ---
            fch_nacimiento = result.get('ANIFchNacimiento')
            fch_expedicion = result.get('ANIFchExpedicion')
            
            # Construcción del diccionario final con el formato deseado
            formato_data = {
                'Cédula': result.get('ANINuip', 'N/A'),
                'Nombres': f"{result.get('ANINombre1', '')} {result.get('ANINombre2', '')}".strip(),
                'Apellidos': f"{result.get('ANIApellido1', '')} {result.get('ANIApellido2', '')}".strip(),
                'Fecha de Nacimiento': formatear_fecha(fch_nacimiento),
                'Fecha de Expedicion': formatear_fecha(fch_expedicion),
                'Edad': calcular_edad(fch_nacimiento),
            }
            
            return jsonify(formato_data), 200
        else:
            return jsonify({'message': 'Cédula no encontrada.'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': f"Error de la base de datos: {err.msg}"}), 500
    except Exception as e:
        return jsonify({'error': f"Error interno del servidor: {e}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
