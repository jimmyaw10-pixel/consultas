<?php
// Reportar todos los errores para el diagnóstico
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "<h1>Prueba de Conexión a MySQL en Railway</h1>";

// --- 1. CREDENCIALES DE PRUEBA (Reemplazar con tus datos) ---
// **OBTÉN ESTOS VALORES DE LA PESTAÑA VARIABLES DE TU SERVICIO MySQL EN RAILWAY**
$dbHost     = 'mysql.railway.internal'; 
$dbUser     = 'root';         // <-- USUARIO REAL (probablemente 'root')
$dbPass     = 'kdvOXgdliBYdDhKzBoaiboabmCPwDxTa';     // <-- CONTRASEÑA REAL de MYSQL_ROOT_PASSWORD
$dbPort     = '3306';
$dbName     = 'cedulas'; 

// DSN forzado para evitar problemas de red/puerto
$dsn = "mysql:host=mysql.railway.internal;port=3306;dbname=$dbName;charset=utf8mb4";

try {
    echo "<h2>Intentando conectar...</h2>";
    
    // Conexión a la base de datos
    $pdo = new PDO($dsn, $dbUser, $dbPass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    echo "<h3>✅ Conexión Exitosa.</h3>";
    echo "<p>El problema no es la conexión, sino la lógica de index.php o las variables de entorno de producción.</p>";
    
    // --- Opcional: Probar una consulta simple ---
    $stmt = $pdo->query("SELECT COUNT(*) AS total_records FROM ani_filtered");
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "<p>Total de registros en la tabla: **{$result['total_records']}**</p>";

} catch (PDOException $e) {
    echo "<h3>❌ Error de Conexión.</h3>";
    echo "<p>El problema es la red de Railway o una credencial.</p>";
    echo "<p><strong>Mensaje de Error PDO:</strong> " . $e->getMessage() . "</p>";
    echo "<p><strong>Código de Error PDO:</strong> " . $e->getCode() . "</p>";

    // Imprimir los datos utilizados (excepto la contraseña)
    echo "<h4>Detalles de la Conexión Usada:</h4>";
    echo "<ul>";
    echo "<li>Host: $dbHost</li>";
    echo "<li>Usuario: $dbUser</li>";
    echo "<li>DSN: $dsn</li>";
    echo "</ul>";
}
?>
