# Unidad III · Actividad 1 · Dashboard financiero

**Integrantes:** (completar)

Proyecto desarrollado en Python manteniendo el contrato GraphQL, estructura y pruebas de `SistemaEmpresarial`.

## Stack

- **Backend (`ingresos/SistemaEmpresarial/`):** Python 3 (FastAPI + Strawberry GraphQL + Uvicorn), persistencia SQL (`AppDbContext` compatible con SQLite/PostgreSQL), autenticación JWT Bearer (HS256).
- **Pruebas (`ingresos/SistemaEmpresarial.Tests/`):** `unittest` (`test_balance_calculator.py`, `test_role_permission_atomicity.py`).
- **Dashboard (`dashboard/`):** HTML + CSS + JavaScript que consume `/graphql` con `fetch` (opción 1 del PDF).

## Requisitos

- Python 3.10+
- Dependencias en `ingresos/SistemaEmpresarial/requirements.txt` (`fastapi`, `strawberry-graphql`, `uvicorn`, `python-dotenv`, `pydantic`)
- Docker Desktop (opcional si se levanta PostgreSQL en contenedor)

## Cómo levantar el proyecto

**1. Base de datos (opcional con Docker o automática local)**

Desde la raíz del paquete, puedes crear un archivo `.env` (no se sube al repo):

```env
POSTGRES_PASSWORD=tu_password_local
JWT_KEY=una_clave_de_al_menos_32_caracteres_aqui
```

Si usas Docker:
```bash
docker compose up -d
```
*(Si no defines `DATABASE_URL`, el backend inicializa automáticamente la base local `sistema_empresarial.db` con todas las tablas, índices y el `AccessSeeder`).*

**2. Ejecutar la API (Backend en Python)**

```bash
cd ingresos/SistemaEmpresarial
python main.py
```

La API queda escuchando en `http://localhost:5016` y expone GraphiQL y el endpoint en `http://localhost:5016/graphql`.

**3. Ejecutar las pruebas automatizadas**

```bash
cd ingresos/SistemaEmpresarial.Tests
python -m unittest discover -v
```

**4. Dashboard**

```bash
cd dashboard
python -m http.server 5173
```

Abre `http://localhost:5173`. Ese origen ya está permitido por CORS en el backend.

## Usuario de prueba y período de demostración

- **Correo:** (completar)
- **Contraseña:** (completar; no subir a Git)
- **Período de demo:** 26 al 30 de octubre de 2026
- **Valores esperados:** saldo inicial 1,000.00 · ingresos 3,500.00 · egresos 2,900.00 · profit 600.00 · saldo final 1,600.00 · general en rojo: No · cuentas en rojo: 1 (Caja)

## Decisiones de diseño

- El login devuelve un `token` (JWT). El dashboard lo guarda en `sessionStorage` y lo envía en `Authorization: Bearer`.
- La consulta del dashboard es `miGeneralBalance`. Toma la empresa y la membresía del claim `companyUserId` del token; el cliente no envía identidad.
- Los importes llegan del servidor como texto con dos decimales. El cliente solo los formatea y no recalcula totales.
- Se quitó el middleware de `X-User-Id` porque sobrescribía la identidad del token.
- El backend sigue siendo la única fuente de cálculo; no hay tablas de caché.

## Estructura

```
unidad3_actividad1_equipo/
├── README.md
├── docker-compose.yml
├── evidencias.md
├── guion_demo.md
├── ingresos/          # backend en Python (SistemaEmpresarial y SistemaEmpresarial.Tests)
└── dashboard/
    └── index.html
```
