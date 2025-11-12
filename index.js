const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path'); 

const app = express();
const PORT = process.env.PORT || 3000; 

// --- CONEXIÓN INTERNA SEGURA USANDO VARIABLES DE REFERENCIA ---
const pool = mysql.createPool({
    // Las variables DB_HOST, DB_USER, etc., se obtienen de forma segura del servicio MySQL
    // gracias a la configuración de ${{REF}} en Railway.
    host: process.env.DB_HOST,             // Lee mysql.railway.internal
    user: process.env.DB_USER,             // Lee root
    password: process.env.DB_PASSWORD,     // Lee la contraseña nueva y segura
    database: 'cedulas',                   // El esquema correcto
    port: process.env.DB_PORT,             // Lee 3306
    waitForConnections: true,
    connectionLimit: 10
});

// Middleware para aceptar JSON
app.use(express.json());

// Servir archivos estáticos (HTML, CSS, JS) del directorio actual
// Esto resuelve el error 'Cannot GET /index.html'
app.use(express.static(__dirname)); 

// ----------------------------------------------------
// RUTA PRINCIPAL DE CONSULTA POR CÉDULA
// ----------------------------------------------------
app.get('/api/cedula/:id', async (req, res) => {
    // La base de datos ya está optimizada con el índice (idx_nuip)
    // para que esta consulta sea rápida y no cause el error 499.
    const cedulaId = req.params.id;
    const query = `SELECT * FROM ani_filtered WHERE ANINuip = ? LIMIT 1`; 

    try {
        const [rows] = await pool.execute(query, [cedulaId]);

        if (rows.length === 0) {
            return res.status(404).json({ message: "Cédula no encontrada." });
        }
        
        res.json(rows[0]);

    } catch (error) {
        console.error("Error al consultar la base de datos:", error);
        res.status(500).json({ error: 'Error interno del servidor al consultar datos.' });
    }
});


app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
