import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
import uvicorn

from Acceso import AccessSeeder, JwtService
from Data import AppDbContext
from GraphQL import Mutation, Query

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent.parent / ".env")
load_dotenv(BASE_DIR / ".env")


def load_config() -> Dict[str, Any]:
    cfg_path = BASE_DIR / "appsettings.json"
    cfg: Dict[str, Any] = {}
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)

    conn_env = (
        os.environ.get("ConnectionStrings__DefaultConnection")
        or os.environ.get("DATABASE_URL")
    )
    if conn_env:
        cfg.setdefault("ConnectionStrings", {})["DefaultConnection"] = conn_env

    jwt_key_env = os.environ.get("Jwt__Key") or os.environ.get("JWT_KEY")
    if jwt_key_env:
        cfg.setdefault("Jwt", {})["Key"] = jwt_key_env

    if not cfg.get("Jwt", {}).get("Key"):
        cfg.setdefault("Jwt", {})["Key"] = "clave_secreta_desarrollo_sistema_empresarial_32chars"

    return cfg


CONFIG = load_config()
DB_PATH = str(BASE_DIR / "sistema_empresarial.db")


def create_db_context() -> AppDbContext:
    conn_str = CONFIG.get("ConnectionStrings", {}).get("DefaultConnection") or DB_PATH
    return AppDbContext(conn_str)


# Inicializar esquema y semilla al arrancar (igual que en Program.cs)
_startup_ctx = create_db_context()
try:
    _startup_ctx.ensure_created()
    AccessSeeder.seed(_startup_ctx)
finally:
    _startup_ctx.close()


async def get_context(request: Request) -> Dict[str, Any]:
    db = create_db_context()
    request.state.db = db
    claims: Optional[Dict[str, Any]] = None

    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        claims = JwtService.validar(token, CONFIG)

    return {
        "db": db,
        "claims": claims,
        "config": CONFIG,
        "request": request,
    }


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context, graphql_ide="graphiql")

app = FastAPI(title="SistemaEmpresarial API")

# CORS para el dashboard en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def close_db_context_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    finally:
        db = getattr(request.state, "db", None)
        if db is not None:
            db.close()


app.include_router(graphql_app, prefix="/graphql")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5016"))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
