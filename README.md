# Nuevo Backend - Estructura mínima (FastAPI sin ORM)

Esta plantilla crea la estructura básica para un backend en FastAPI usando una conexión directa a PostgreSQL con asyncpg (sin ORM).

Estructura creada:

- app/
  - main.py
  - routes/
    - users.py
  - controllers/
    - user_controller.py
  - schemas/
    - user.py
  - models/  (para SQL o definiciones, no usado por ORM)
  - db/
    - connection.py
    - init_db.py
  - core/
    - security.py
- .env.example
- requirements.txt

Cómo usar (Windows PowerShell):

1) Crear entorno virtual e instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Configura la variable de entorno DATABASE_URL o copia `.env.example` a `.env` y ajústala.

3) Ejecuta la app en desarrollo:

```powershell
uvicorn app.main:app --reload --port 8000
```

4) Crear la tabla `users` (opcional): hay un script ejemplo en `app/db/init_db.py` que usa el pool para crear la tabla.

Notas:
- Se usa asyncpg para conexiones y passlib para hashear contraseñas.
- La estructura está pensada para ser ampliada con servicios, tests e infra (Docker, CI).
