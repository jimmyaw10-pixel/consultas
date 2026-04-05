import os
from flask import Flask, render_template_string, request, jsonify
import mysql.connector
import urllib.parse as urlparse
from flask_cors import CORS 

app = Flask(__name__)
CORS(app) 

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
                
            parts = line.strip('|').split('|')
            if len(parts) == 2:
                code, city_name = parts
                LOCATION_MAP[code.strip()] = city_name.strip()
        
        print(f"Cargados {len(LOCATION_MAP)} códigos.")
    
    except Exception as e:
        print(f"Error cargando ubicaciones: {e}")

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

MYSQL_URL = os.environ.get('MYSQL_PUBLIC_URL')

DB_HOST = None
DB_USER = None
DB_PASS = None
DB_PORT = None
DB_NAME = 'cedulas'

if MYSQL_URL:
    url = urlparse.urlparse(MYSQL_URL)
    DB_HOST = url.hostname
    DB_USER = url.username
    DB_PASS = url.password
    DB_PORT = url.port


@app.route('/', methods=['GET'])
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Consulta</title>
    </head>
    <body>

    <h2>Buscar Cédula</h2>

    <input type="text" id="cedulaInput">
    <button onclick="buscarCedula()">Buscar</button>

    <pre id="results"></pre>

    <script>

    const MESES_ABR = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];

    // 🔥 SOLUCIÓN REAL (sin zona horaria)
    function formatearFecha(fechaStr) {
        if (!fechaStr) return 'N/A';

        const parts = fechaStr.split('-');
        if (parts.length !== 3) return fechaStr;

        const year = parseInt(parts[0]);
        const month = parseInt(parts[1]) - 1;
        const day = parseInt(parts[2]);

        const date = new Date(year, month, day);

        const d = String(date.getDate()).padStart(2, '0');
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const ma = MESES_ABR[date.getMonth()];
        const y = date.getFullYear();

        return `${d} / ${m}(${ma}) / ${y}`;
    }

    // 🔥 TAMBIÉN CORREGIDO
    function calcularEdad(fechaNacimientoStr) {
        if (!fechaNacimientoStr) return 'N/A';

        const parts = fechaNacimientoStr.split('-');
        const fechaNacimiento = new Date(parts[0], parts[1] - 1, parts[2]);

        const hoy = new Date();
        
        let edad = hoy.getFullYear() - fechaNacimiento.getFullYear();
        const mes = hoy.getMonth() - fechaNacimiento.getMonth();
        
        if (mes < 0 || (mes === 0 && hoy.getDate() < fechaNacimiento.getDate())) {
            edad--;
        }
        
        return `${edad} años`;
    }

    async function buscarCedula() {
        const cedula = document.getElementById('cedulaInput').value;
        const res = document.getElementById('results');

        res.innerHTML = "Cargando...";

        const r = await fetch('/api/cedula?cedulaId=' + cedula);
        const data = await r.json();

        if (r.status === 200) {
            res.innerHTML = `
Cédula: ${data.ANINuip}

Nombres: ${data.ANINombre1} ${data.ANINombre2}
Apellidos: ${data.ANIApellido1} ${data.ANIApellido2}

Nacimiento: ${formatearFecha(data.ANIFchNacimiento)}
Lugar: ${data.LugarNacimientoNombre}

Expedición: ${formatearFecha(data.ANIFchExpedicion)}
Lugar: ${data.LugarExpedicionNombre}

Edad: ${calcularEdad(data.ANIFchNacimiento)}
            `;
        } else {
            res.innerHTML = "No encontrado";
        }
    }

    </script>

    </body>
    </html>
    """
    return render_template_string(html_content)


@app.route('/api/cedula')
def get_cedula():
    cedula = request.args.get('cedulaId')

    try:
        cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT
        )

        cursor = cnx.cursor(dictionary=True)

        query = "SELECT * FROM ani_filtered WHERE ANINuip = %s LIMIT 1"
        cursor.execute(query, (cedula,))
        result = cursor.fetchone()

        cursor.close()
        cnx.close()

        if result:
            result['LugarNacimientoNombre'] = process_location_code(result.get('LUGIdNacimiento'))
            result['LugarExpedicionNombre'] = process_location_code(result.get('LUGIdExpedicion'))
            return jsonify(result)

        return jsonify({'error': 'No encontrado'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
