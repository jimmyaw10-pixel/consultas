const express = require('express');
const mysql = require('mysql2/promise');

const app = express();
const PORT = process.env.PORT || 3000; 

// --------------------------------------------------------------------------
// ¡SOLUCIÓN DE EMERGENCIA!
// Usamos el host y puerto de proxy público (inseguro) para saltar el firewall interno.
// --------------------------------------------------------------------------
const pool = mysql.createPool({
    host: 'ballast.proxy.rlwy.net',           // <-- HOST PÚBLICO (COMO WORKBENCH)
    user: 'root',                             // Usuario
    password: 'kdvOXgdliBYdDhKzBoaiboabmCPwDxTa', // Contraseña
    database: 'railway',                      // Esquema
    port: 35462,                              // <-- PUERTO PÚBLICO TCP
    waitForConnections: true,
    connectionLimit: 10
});

app.use(express.json());

// RUTA PRINCIPAL DE CONSULTA POR CÉDULA
app.get('/api/cedula/:id', async (req, res) => {
    const cedulaId = req.params.id;
    
    // Consulta SQL con la tabla y columna correctas
    const query = `SELECT * FROM ani_filtered WHERE ANINuip = ? LIMIT 1`; 

    try {
        const [rows] = await pool.execute(query, [cedulaId]);

        if (rows.length === 0) {
            return res.status(404).json({ message: "Cédula no encontrada." });
        }
        
        res.json(rows[0]);

    } catch (error) {
        // En este punto, el error ya no debería ser de conexión.
        console.error("Error al consultar la base de datos:", error);
        res.status(500).json({ error: 'Error interno del servidor al consultar datos.' });
    }
});

app.get('/', (req, res) => {
    res.send('API de Cédulas en funcionamiento.');
});


app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
