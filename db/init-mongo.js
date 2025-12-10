// MongoDB Initialization Script
// Crea índices y configuraciones iniciales

db = db.getSiblingDB('person_tracking');

// Crear colección sessions si no existe
db.createCollection('sessions');

// Crear índices
db.sessions.createIndex(
    { "device_id": 1, "start_time": 1 },
    { name: "device_time_idx" }
);

db.sessions.createIndex(
    { "start_time": 1 },
    { name: "time_idx" }
);

db.sessions.createIndex(
    { "device_id": 1 },
    { name: "device_idx" }
);

// Crear índice para búsquedas por fecha
db.sessions.createIndex(
    { "start_time": -1 },
    { name: "time_desc_idx" }
);

print("✓ MongoDB inicializado correctamente");
print("  - Base de datos: person_tracking");
print("  - Colección: sessions");
print("  - Índices creados: 4");
