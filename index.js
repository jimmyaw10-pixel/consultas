const express = require('express');
const mysql = require('mysql2/promise'); // Usamos la versión con promesas

const app = express();
// Railway expone el puerto 8080 por defecto, pero process.env.PORT es más seguro
const PORT = process.env.PORT || 3000; 

// --------------------------------------------------------------------------
// CONFIGURACIÓN DE CONEXIÓN CON VALORES FIJOS (para solución rápida)
// ¡Asegúrate de que la contraseña y el nombre de la base de datos sean correctos!
// --------------------------------------------------------------------------
const pool = mysql.createPool({
    host: 'mysql',                              // <-- Host interno (nombre del servicio)
    user: 'root',
    password: 'kdvOXgdliBYdDhKzBoaiboabmCPwDxTa', 
    database: 'railway',                          
    port: 3306,                                 // <-- Puerto interno (el que usa tu API)
    waitForConnections: true,
    connectionLimit: 10
});

// Middleware para aceptar JSON
app.use(express.json());

// ----------------------------------------------------
// RUTA PRINCIPAL DE CONSULTA POR CÉDULA
// ----------------------------------------------------
app.get('/api/cedula/:id', async (req, res) => {
    const cedulaId = req.params.id;
    
    // CONSULTA CORREGIDA: Usa la tabla 'ani_filtered' y la columna 'ANINuip'
    const query = `SELECT * FROM ani_filtered WHERE ANINuip = ? LIMIT 1`; 

    try {
        const [rows] = await pool.execute(query, [cedulaId]);

        if (rows.length === 0) {
            return res.status(404).json({ message: "Cédula no encontrada." });
        }
        
        // Devuelve el primer resultado (los datos de la persona) como JSON
        res.json(rows[0]);

    } catch (error) {
        // Esto registrará el error real (ej. problema de tabla/columna) en los logs de Railway
        console.error("Error al consultar la base de datos:", error);
        res.status(500).json({ error: 'Error interno del servidor al consultar datos.' });
    }
});

// Ruta de prueba simple
app.get('/', (req, res) => {
    res.send('API de Cédulas en funcionamiento.');
});


app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);

});

