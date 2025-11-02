from fastapi import APIRouter, Form, HTTPException, status
from app.database import get_connection
from app.utils.security import create_access_token
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login")
def login(correo: str = Form(...), contrasena: str = Form(...)):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM usuarios 
            WHERE correo = %s AND estado = 1 AND is_deleted = 0
        """, (correo,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Correo no registrado o usuario inactivo")

        # 🔍 Depuración y validación defensiva
        print("📨 contrasena recibida:", repr(contrasena))
        print("🔐 Hash en BD:", repr(user.get("contrasena")))

        if not user.get("contrasena") or not user["contrasena"].startswith("$2b$"):
            raise HTTPException(status_code=401, detail="Hash inválido o no registrado")

        if not pwd_context.verify(contrasena, user["contrasena"]):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        
        conn.commit()

        # ✅ Generar token JWT
        token = create_access_token(data={
            "sub": user["correo"],
            "user_id": user["user_id"],
            "tipo_usuario": user["tipo_usuario"]
        })
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el login: {e}")
    finally:
        cursor.close()
        conn.close()