from datetime import datetime, timedelta
import jwt
import os
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from pathlib import Path

# ✅ Cargar .env desde la carpeta raíz del proyecto
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 🔐 Validación defensiva
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
expire_raw = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

if not SECRET_KEY:
    raise RuntimeError("❌ Falta SECRET_KEY en el archivo .env")
if not ALGORITHM:
    raise RuntimeError("❌ Falta ALGORITHM en el archivo .env")
if not expire_raw:
    raise RuntimeError("❌ Falta ACCESS_TOKEN_EXPIRE_MINUTES en el archivo .env")

ACCESS_TOKEN_EXPIRE_MINUTES = int(expire_raw)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")