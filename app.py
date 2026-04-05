import os
from flask import Flask, render_template_string, request, jsonify
import mysql.connector
import urllib.parse as urlparse
from flask_cors import CORS 

# 1. CREAR LA APLICACIÓN FLASK
app = Flask(__name__)

# 2. HABILITAR CORS
CORS(app) 

# --- LÓGICA DE TRADUCCIÓN DE CÓDIGOS DE UBICACIÓN ---
LOCATION_MAP = {}

def load_location_data():
    global LOCATION_MAP
    file_path = 'lug_ori.txt'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.strip('|').split('|')
                if len(parts) == 2:
                    code, city_name = parts
                    LOCATION_MAP[code.strip()] = city_name.strip()
            except:
                continue
        print(f"Cargados {len(LOCATION_MAP)} códigos de ubicación.")
    except FileNotFoundError:
        print(f"ERROR: Archivo '{file_path}' no encontrado.")
    except Exception as e:
        print(f"Error al cargar datos: {e}")

def process_location_code(full_code):
    if not full_code:
        return 'N/A'
    code_str = str(full_code)
    if len(code_str) == 11:
        search_code = code_str[3:8] 
        return LOCATION_MAP.get(search_code, f'Código Desconocido ({search_code})')
    if len(code_str) == 5:
        return LOCATION_MAP.get(code_str, f'Código Desconocido ({code_str})')
    return 'Código Inválido'

load_location_data()

# --- CONFIGURACIÓN DE CONEXIÓN ---
MYSQL_URL = os.environ.get('MYSQL_PUBLIC_URL')
DB_NAME = 'cedulas' 

# --- FRONTEND (HTML/JS CORREGIDO) ---
@app.route('/', methods=['GET'])
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consulta de Cédulas</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; }
            .container { max-width: 600px; margin: 0 auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
            h1 { color: #333; text-align: center; }
            input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
            button { width: 25%; padding: 10px; background-color: #5cb85c; color: white; border: none; border-radius: 4px; cursor: pointer; }
            #results { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background-color: #e9e9e9; white-space: pre-wrap; }
            #results strong { display: inline-block; width: 160px; }
            hr { border: 0.5px solid #ccc; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Buscador de Cédulas</h1>
            <div>
                <input type="text" id="cedulaInput" placeholder="Número de cédula" maxlength="10">
                <button onclick="buscarCedula()">Buscar</button>
            </div>
            <div id="results">Ingrese una cédula para comenzar.</div>
        </div>

        <script>
            const MESES_ABR = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

            // SOLUCIÓN AL ERROR DEL DÍA DE RETRASO
            function parsearFechaLocal(fechaStr) {
                if (!fechaStr) return null;
                // Divide la fecha (YYYY-MM-DD) para evitar que JS la trate como UTC
                const partes = fechaStr.split(/[-T ]/);
                const year = parseInt(partes[0]);
                const month = parseInt(partes[1]) - 1; // Enero es 0
                const day = parseInt(partes[2]);
                return new Date(year, month, day);
            }

            function formatearFecha(fechaStr) {
                const date = parsearFechaLocal(fechaStr);
                if (!date || isNaN(date.getTime())) return 'N/A';

                const day = String(date.getDate()).padStart(2, '0');
                const monthNum = String(date.getMonth() + 1).padStart(2, '0');
                const monthAbr = MESES_ABR[date.getMonth()];
                const year = date.getFullYear();

                return `${day} / ${monthNum}(${monthAbr}) / ${year}`;
            }

            function calcularEdad(fechaNacimientoStr) {
                const fechaNacimiento = parsearFechaLocal(fechaNacimientoStr);
                if (!fechaNacimiento) return 'N/A';

                const hoy = new Date();
                let edad = hoy.getFullYear() - fechaNacimiento.getFullYear();
                const mesDiff = hoy.getMonth() - fechaNacimiento.getMonth();
                
                if (mesDiff < 0 || (mesDiff === 0 && hoy.getDate() < fechaNacimiento.getDate())) {
                    edad--;
                }
                return `${edad} años`;
            }

            async function buscarCedula() {
                const cedulaId = document.getElementById('cedulaInput').value.trim();
                const resultsDiv = document.getElementById('results');
                if (!cedulaId) return;

                resultsDiv.innerHTML = 'Cargando...';

                try {
                    const response = await fetch('/api/cedula?cedulaId=' + cedulaId);
                    const data = await response.json();

                    if (response.status === 200) {
                        resultsDiv.innerHTML = `
                            <h3>✅ Información Encontrada</h3>
                            <strong>Cédula:</strong> ${data.ANINuip || 'N/A'}
                            <strong>Nombres:</strong> ${data.ANINombre1 || ''} ${data.ANINombre2 || ''}
                            <strong>Apellidos:</strong> ${data.ANIApellido1 || ''} ${data.ANIApellido2 || ''}
                            <hr>
                            <strong>Fecha de Nacimiento:</strong> ${formatearFecha(data.ANIFchNacimiento)}
                            <strong>Lugar de Nacimiento:</strong> ${data.LugarNacimientoNombre || 'N/A'}
                            <hr>
                            <strong>Fecha de Expedición:</strong> ${formatearFecha(data.ANIFchExpedicion)}
                            <strong>Lugar de Expedición:</strong> ${data.LugarExpedicionNombre || 'N/A'}
                            <hr>
                            <strong>Edad Actual:</strong> ${calcularEdad(data.ANIFchNacimiento)}
                        `;
                    } else {
                        resultsDiv.innerHTML = `⚠️ ${data.message || 'Error'}`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = '🚨 Error de conexión.';
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

# --- API BACKEND ---
@app.route('/api/cedula', methods=['GET'])
def get_cedula():
    cedula_id = request.args.get('cedulaId')
    if not MYSQL_URL or not cedula_id:
        return jsonify({'error': 'Configuración o cédula faltante'}), 400

    try:
        url = urlparse.urlparse(MYSQL_URL)
        cnx = mysql.connector.connect(
            host=url.hostname, user=url.username, password=url.password,
            port=url.port, database=DB_NAME
        )
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ani_filtered WHERE ANINuip = %s LIMIT 1", (cedula_id,))
        result = cursor.fetchone()
        
        if result:
            # Aseguramos que las fechas se conviertan a string ISO para el JSON
            if result.get('ANIFchNacimiento'):
                result['ANIFchNacimiento'] = str(result['ANIFchNacimiento'])
            if result.get('ANIFchExpedicion'):
                result['ANIFchExpedicion'] = str(result['ANIFchExpedicion'])

            result['LugarNacimientoNombre'] = process_location_code(result.get('LUGIdNacimiento'))
            result['LugarExpedicionNombre'] = process_location_code(result.get('LUGIdExpedicion'))
            return jsonify(result), 200
        return jsonify({'message': 'No encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
