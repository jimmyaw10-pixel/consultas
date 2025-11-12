const express = require('express');
const mysql = require('mysql2/promise'); // Usamos la versión con promesas para código moderno

const app = express();
const PORT = process.env.PORT || 3000;

// Configuración de la conexión a MySQL usando las variables de entorno de Railway
// Railway inyecta automáticamente estas variables para la conexión interna (Private Networking)
const pool = mysql.createPool({
    host: process.env.MYSQLHOST,           // e.g., mysql.railway.internal
    user: process.env.MYSQLUSER,           // e.g., root
    password: process.env.MYSQLPASSWORD,   // Contraseña larga
    database: process.env.MYSQLDATABASE,   // e.g., cedulas
    port: process.env.MYSQLPORT || 3306,
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
    // La consulta SQL debe ser modificada si tu columna no se llama 'cedula_id'
    const query = `SELECT * FROM cedulas WHERE cedula_id = ? LIMIT 1`; 

    try {
        const [rows] = await pool.execute(query, [cedulaId]);

        if (rows.length === 0) {
            return res.status(404).json({ message: "Cédula no encontrada." });
        }
        // Devuelve el primer resultado como JSON
        res.json(rows[0]);

    } catch (error) {
        console.error("Error al consultar la base de datos:", error);
        res.status(500).json({ error: 'Error interno del servidor al consultar datos.' });
    }
});

// Ruta de prueba
app.get('/', (req, res) => {
    res.send('API de Cédulas en funcionamiento.');
});


app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});