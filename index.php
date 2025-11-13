<?php
// --- 1. CONFIGURACIÓN DE CONEXIÓN SEGURA (Variables de Railway) ---
// El método getenv() es seguro porque las credenciales no se exponen al cliente.
// Usamos getenv() solo para las credenciales seguras (User y Pass).
$dbHost     = 'mysql.railway.internal'; // Host interno forzado
$dbUser     = 'root';         // <--- ¡REEMPLAZAR con tu usuario real! (Probablemente 'root')
$dbPass     = 'kdvOXgdliBYdDhKzBoaiboabmCPwDxTa';     // <--- ¡REEMPLAZAR con tu contraseña real!
$dbPort     = '3306';                    // Puerto estándar
$dbName     = 'cedulas';


// DSN forzado: Usamos el Host y Puerto fijos para evitar el error de conexión (Error 500)
$dsn = "mysql:host=mysql.railway.internal;port=3306;dbname=$dbName;charset=utf8mb4";

// Si la URL tiene un parámetro 'cedulaId', es una llamada API.
if (isset($_GET['cedulaId'])) {
    
    // --- 2. LÓGICA DE LA API (Servicio de datos) ---
    header('Content-Type: application/json');
    $cedulaId = filter_input(INPUT_GET, 'cedulaId', FILTER_SANITIZE_STRING);

    if (empty($cedulaId)) {
        http_response_code(400);
        echo json_encode(['error' => 'Cédula no proporcionada.']);
        exit;
    }

    try {
        // Conexión a la base de datos con el DSN forzado.
        $pdo = new PDO($dsn, $dbUser, $dbPass);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        // Consulta optimizada gracias al índice creado anteriormente.
        $stmt = $pdo->prepare("SELECT * FROM ani_filtered WHERE ANINuip = ? LIMIT 1");
        $stmt->execute([$cedulaId]);
        $result = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($result) {
            echo json_encode($result);
        } else {
            http_response_code(404);
            echo json_encode(['message' => 'Cédula no encontrada.']);
        }
    } catch (PDOException $e) {
        // Devuelve el error de conexión en la API para facilitar la depuración
        http_response_code(500);
        echo json_encode(['error' => 'Error de servidor: ' . $e->getMessage()]);
    }
    
    exit;
}
// --- 3. INTERFAZ WEB (Si no hay llamada API, muestra el HTML) ---
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consulta de Cédulas (PHP)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; }
        .container { max-width: 600px; margin: 0 auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 20px; }
        input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
        button { width: 25%; padding: 10px; background-color: #5cb85c; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 5px; }
        button:hover { background-color: #4cae4c; }
        #results { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background-color: #e9e9e9; }
        .data-item { margin-bottom: 10px; padding: 5px 0; border-bottom: 1px dashed #ccc; }
        .data-item:last-child { border-bottom: none; }
        .data-label { font-weight: bold; color: #555; display: inline-block; width: 150px; }
        .data-value { color: #333; }
        .loading { text-align: center; color: #777; }
    </style>
</head>
<body>

    <div class="container">
        <h1>🔍 Buscador de Cédulas (PHP)</h1>

        <div>
            <input type="text" id="cedulaInput" placeholder="Ingrese el número de cédula (ej: 100)" maxlength="10">
            <button onclick="buscarCedula()">Buscar</button>
        </div>

        <div id="results">
            Ingrese una cédula para comenzar la búsqueda.
        </div>
    </div>

    <script>
        // La URL de la API es el mismo archivo que está cargando esta página, 
        // lo que ELIMINA el problema CORS.
        const API_BASE_URL = window.location.href.split('?')[0];

        async function buscarCedula() {
            const cedulaId = document.getElementById('cedulaInput').value.trim();
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">Cargando datos...</div>';

            if (!cedulaId) {
                resultsDiv.innerHTML = 'Ingrese un número de cédula válido.';
                return;
            }

            try {
                // Llama al mismo archivo index.php usando el parámetro cedulaId
                const response = await fetch(API_BASE_URL + '?cedulaId=' + cedulaId);
                const data = await response.json();

                if (response.status === 404) {
                    resultsDiv.innerHTML = '❌ Cédula no encontrada en la base de datos.';
                } else if (response.status === 200) {
                    mostrarResultados(data);
                } else {
                    // Si el servidor devuelve 500, el mensaje de error de PDO debería estar aquí
                    resultsDiv.innerHTML = `⚠️ Error del servidor: ${data.error || 'Algo salió mal.'}`;
                }

            } catch (error) {
                console.error('Error de conexión:', error);
                resultsDiv.innerHTML = '🚨 Error de conexión. Verifique que la API esté activa.';
            }
        }
        
        // Función para mostrar resultados
        function mostrarResultados(data) {
            const resultsDiv = document.getElementById('results');
            let html = '<h3>✅ Resultado Encontrado</h3>';

            const fieldMap = {
                'ANINuip': 'Cédula',
                'ANIApellido1': 'Primer Apellido',
                'ANIApellido2': 'Segundo Apellido',
                'ANINombre1': 'Primer Nombre',
                'ANINombre2': 'Segundo Nombre',
                'ANINombresPadre': 'Nombre del Padre',
                'ANINombresMadre': 'Nombre de la Madre',
                'ANIFchNacimiento': 'Fecha de Nacimiento',
                'ANIFchExpedicion': 'Fecha de Expedición',
                'LUGIdNacimiento': 'ID Lugar Nacimiento',
                'LUGIdExpedicion': 'ID Lugar Expedicion'
            };

            const order = [
                'ANINuip', 'ANINombre1', 'ANINombre2', 'ANIApellido1', 'ANIApellido2', 
                'ANIFchNacimiento', 'ANIFchExpedicion', 
                'ANINombresPadre', 'ANINombresMadre', 
                'LUGIdNacimiento', 'LUGIdExpedicion'
            ];

            order.forEach(key => {
                let value = data[key] !== null ? data[key] : 'N/A';
                
                if (key.includes('Fch') && value !== 'N/A') {
                    const dateObj = new Date(value);
                    if (!isNaN(dateObj)) {
                        value = dateObj.toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' });
                    }
                }

                html += `
                    <div class="data-item">
                        <span class="data-label">${fieldMap[key] || key}:</span>
                        <span class="data-value">${value}</span>
                    </div>
                `;
            });

            resultsDiv.innerHTML = html;
        }
    </script>

</body>
</html>
