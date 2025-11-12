const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path'); 
const cors = require('cors'); // <-- Implementación de CORS

const app = express();
const PORT = process.env.PORT || 3000; 

// --- IMPLEMENTAR CORS PARA PERMITIR PETICIONES ENTRE DOMINIOS ---
app.use(cors()); 

// --- CONEXIÓN INTERNA SEGURA USANDO VARIABLES DE REFERENCIA ---
const pool = mysql.createPool({
    // Lee las variables DB_HOST, DB_USER, etc., configuradas en Railway
    host: process.env.DB_HOST,             
    user: process.env.DB_USER,             
    password: process.env.DB_PASSWORD,     
    database: 'cedulas',                   // El esquema donde está la tabla
    port: process.env.DB_PORT,             
    waitForConnections: true,
    connectionLimit: 10
});

app.use(express.json());

// Servir archivos estáticos (incluyendo index.html) del directorio raíz
app.use(express.static(__dirname)); 

// ----------------------------------------------------
// RUTA PRINCIPAL DE CONSULTA POR CÉDULA
// ----------------------------------------------------
app.get('/api/cedula/:id', async (req, res) => {
    // La consulta es rápida gracias a la indexación completada.
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