import os
from flask import Flask, render_template_string, request, jsonify
import mysql.connector
import urllib.parse as urlparse
# Importar la librería CORS
from flask_cors import CORS 

# 1. CREAR LA APLICACIÓN FLASK
app = Flask(__name__)

# 2. HABILITAR CORS (SOLUCIÓN AL ERROR)
CORS(app) 

# --- LÓGICA DE TRADUCCIÓN DE CÓDIGOS DE UBICACIÓN (lug_ori.txt) ---
# Se usará un diccionario global para guardar los códigos {código_DANE: nombre_ciudad}
LOCATION_MAP = {}

def load_location_data():
    """
    Carga los códigos de ubicación del archivo lug_ori.txt a un diccionario para búsquedas rápidas.
    El archivo DEBE estar en el mismo directorio que app.py.
    """
    global LOCATION_MAP
    file_path = 'lug_ori.txt' # Nombre del archivo
    
    try:
        # Intenta leer el archivo con codificación UTF-8
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                # La línea tiene el formato |CÓDIGO|CIUDAD
                # Elimina el primer y último pipe y divide por el pipe restante
                parts = line.strip('|').split('|')
                if len(parts) == 2:
                    code, city_name = parts
                    # Guardamos el código (ej: '01001') y el nombre de la ciudad
                    LOCATION_MAP[code.strip()] = city_name.strip()
            except:
                continue
        print(f"Cargados {len(LOCATION_MAP)} códigos de ubicación desde {file_path}.")
    
    except FileNotFoundError:
        print(f"ERROR: Archivo de ubicaciones '{file_path}' no encontrado. Asegúrese de incluirlo en el deploy de Railway.")
        print("La traducción de códigos no funcionará hasta que se suba el archivo.")
    except Exception as e:
        print(f"Error al cargar datos de ubicación: {e}")


def process_location_code(full_code):
    """
    Procesa el código completo (e.g., 24421001000) para extraer el código municipal (e.g., 21001).
    Busca el nombre de la ciudad en LOCATION_MAP.
    """
    if not full_code:
        return 'N/A'
    
    code_str = str(full_code)
    
    # Lógica de extracción: quitar los 3 primeros y los 3 últimos (244|XXXXX|000)
    # Se espera un código total de 11 dígitos para esta lógica
    if len(code_str) == 11:
        # Extrae los 5 dígitos centrales (índices 3 al 8)
        search_code = code_str[3:8] 
        # Si el mapa está vacío, devolvemos un mensaje de advertencia
        if not LOCATION_MAP:
             return f'Código ({search_code}) (Datos de ubicación faltantes)'

        return LOCATION_MAP.get(search_code, f'Código Desconocido ({search_code})')
    
    # Si el código ya tiene 5 dígitos (código DANE), lo busca directamente 
    if len(code_str) == 5:
         if not LOCATION_MAP:
             return f'Código ({code_str}) (Datos de ubicación faltantes)'
             
         return LOCATION_MAP.get(code_str, f'Código Desconocido ({code_str})')

    return 'Código de Ubicación Inválido'

# Llamar a la función de carga al inicio de la aplicación
load_location_data()


# --- 1. CONFIGURACIÓN DE CONEXIÓN (PROBADA Y ESTABLE) ---
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

# --- 2. FRONTEND (HTML/JS con LÓGICA de Formato) ---

@app.route('/', methods=['GET'])
def index():
    """Sirve la interfaz web (frontend) y contiene toda la lógica de presentación."""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consulta de Cédulas (Producción Final)</title>
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
            <h1>🔍 Buscador de Cédulas (Final con Ubicación)</h1>
            <div>
                <input type="text" id="cedulaInput" placeholder="Ingrese el número de cédula" maxlength="10">
                <br><br><button onclick="buscarCedula()">Buscar</button>
            </div>
            <pre id="results">Ingrese una cédula para comenzar la búsqueda.</pre>
        </div>

        <script>
            // --- LÓGICA DE FORMATO Y CÁLCULO EN JAVASCRIPT (Frontend) ---
            const MESES_ABR = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

            function formatearFecha(fechaStr) {
                if (!fechaStr) return 'N/A';
                
                // Crea objeto Date a partir de la cadena de MySQL (ej: '1980-05-15')
                const date = new Date(fechaStr);
                if (isNaN(date.getTime())) return fechaStr;

                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0'); // Mes de 0 a 11
                const monthAbr = MESES_ABR[date.getMonth()];
                const year = date.getFullYear();

                // Formato: día / mes(ABR) / año en digitos
                return `${day} / ${month}(${monthAbr}) / ${year}`;
            }

            function calcularEdad(fechaNacimientoStr) {
                if (!fechaNacimientoStr) return 'N/A';

                const fechaNacimiento = new Date(fechaNacimientoStr);
                const hoy = new Date();
                
                let edad = hoy.getFullYear() - fechaNacimiento.getFullYear();
                const mes = hoy.getMonth() - fechaNacimiento.getMonth();
                
                if (mes < 0 || (mes === 0 && hoy.getDate() < fechaNacimiento.getDate())) {
                    edad--;
                }
                
                return `${edad} años`;
            }

            // --- FUNCIÓN DE BÚSQUEDA Y DISPLAY ---
            async function buscarCedula() {
                const cedulaId = document.getElementById('cedulaInput').value.trim();
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="loading">Cargando datos...</div>';

                if (!cedulaId) {
                    resultsDiv.innerHTML = 'Ingrese un número de cédula válido.';
                    return;
                }

                try {
                    // Llama a la API que devuelve datos crudos y traducidos
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
                // Formateo de fechas para el display
                const fchNacimientoFormatted = formatearFecha(data.ANIFchNacimiento);
                const fchExpedicionFormatted = formatearFecha(data.ANIFchExpedicion);

                let html = '<h3>✅ Información Encontrada</h3>';
                
                // ORDEN SOLICITADO
                html += `<p><strong>Cédula:</strong> ${data.ANINuip || 'N/A'}</p>`;
                
                // Nombres (Primera línea)
                html += `<p><strong>Nombres:</strong> ${data.ANINombre1 || ''} ${data.ANINombre2 || ''}</p>`;
                
                // Apellidos (Segunda línea)
                html += `<p><strong>Apellidos:</strong> ${data.ANIApellido1 || ''} ${data.ANIApellido2 || ''}</p>`;
                html += `<hr style="border: 0.5px solid #ccc;">`;
                
                // FECHA Y LUGAR DE NACIMIENTO (Nuevo Orden)
                html += `<p><strong>Fecha de Nacimiento:</strong> ${fchNacimientoFormatted}</p>`;
                html += `<p><strong>Lugar de Nacimiento:</strong> ${data.LugarNacimientoNombre || 'N/A'}</p>`;
                html += `<hr style="border: 0.5px solid #ccc;">`;

                // FECHA Y LUGAR DE EXPEDICIÓN (Nuevo Orden)
                html += `<p><strong>Fecha de Expedición:</strong> ${fchExpedicionFormatted}</p>`;
                html += `<p><strong>Lugar de Expedición:</strong> ${data.LugarExpedicionNombre || 'N/A'}</p>`;
                html += `<hr style="border: 0.5px solid #ccc;">`;
                
                // Edad (Quinta línea)
                html += `<p><strong>Edad Actual:</strong> ${calcularEdad(data.ANIFchNacimiento)}</p>`;
                
                return html;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

# --- 3. API BACKEND (Devuelve Datos Crudos y Traducidos) ---

@app.route('/api/cedula', methods=['GET'])
def get_cedula():
    """Función API que consulta la base de datos, traduce los códigos de ubicación y devuelve los datos."""
    cedula_id = request.args.get('cedulaId')
    
    # Verifica que la conexión funcione
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
            # TRADUCIR CÓDIGOS DE UBICACIÓN
            # Asumimos que los campos de la DB se llaman LUGIdNacimiento y LUGIdExpedicion
            lug_nac_id = result.get('LUGIdNacimiento')
            lug_exp_id = result.get('LUGIdExpedicion') 
            
            # Traducir los códigos a nombres de ciudades y añadir al JSON de respuesta
            result['LugarNacimientoNombre'] = process_location_code(lug_nac_id)
            result['LugarExpedicionNombre'] = process_location_code(lug_exp_id)
            
            return jsonify(result), 200
        else:
            return jsonify({'message': 'Cédula no encontrada.'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': f"Error de la base de datos: {err.msg}"}), 500
    except Exception as e:
        return jsonify({'error': f"Error interno del servidor: {e}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) puedess revisar este codigo que cuando consulto la fecha de nacimiento sale con un dia menos del que deberia
