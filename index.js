const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path'); // Módulo necesario para servir archivos estáticos

const app = express();
const PORT = process.env.PORT || 3000; 

// --- CONFIGURACIÓN DE CONEXIÓN DE EMERGENCIA (PÚBLICA) ---
// Usamos el Host y Puerto de Proxy TCP para evitar el firewall interno,
// conectando exitosamente al esquema 'cedulas'.
const pool = mysql.createPool({
    host: 'ballast.proxy.rlwy.net',           // HOST PÚBLICO (Inseguro, pero funcional)
    user: 'root',                             // Usuario de BD
    password: 'kdvOXgdliBYdDhKzBoaiboabmCPwDxTa', // Contraseña
    database: 'cedulas',                      // Esquema corregido
    port: 35462,                              // PUERTO PÚBLICO TCP
    waitForConnections: true,
    connectionLimit: 10
});

// Middleware para aceptar JSON
app.use(express.json());

// Servir archivos estáticos (incluyendo index.html) del directorio actual
// Esta línea es clave para que el HTML se muestre en la ruta /
app.use(express.static(__dirname)); 

// ----------------------------------------------------
// RUTA PRINCIPAL DE CONSULTA POR CÉDULA
// ----------------------------------------------------
app.get('/api/cedula/:id', async (req, res) => {
    const cedulaId = req.params.id;
    
    // Consulta SQL final
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
