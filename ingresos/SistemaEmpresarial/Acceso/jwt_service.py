import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional
from Models import User


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode((s + padding).encode("ascii"))


class PasswordService:
    """Hash y verificación de contraseñas con PBKDF2-HMAC-SHA256."""

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return f"pbkdf2_sha256$100000${_b64url_encode(salt)}${_b64url_encode(dk)}"

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        if not stored_hash or not stored_hash.startswith("pbkdf2_sha256$"):
            return False
        try:
            _, iter_str, salt_b64, dk_b64 = stored_hash.split("$", 3)
            iterations = int(iter_str)
            salt = _b64url_decode(salt_b64)
            expected = _b64url_decode(dk_b64)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False


class JwtService:
    """Generación y validación de tokens JWT (HS256) estándar RFC 7519."""

    @staticmethod
    def generar(user: User, company_user_id: str, company_id: str, cfg: Dict[str, Any]) -> str:
        jwt_cfg = cfg.get("Jwt", {})
        key_str = jwt_cfg.get("Key") or os.environ.get("JWT_KEY") or "clave_secreta_desarrollo_sistema_empresarial_32chars"
        issuer = jwt_cfg.get("Issuer", "SistemaEmpresarial")
        audience = jwt_cfg.get("Audience", "dashboard")

        header = {"alg": "HS256", "typ": "JWT"}
        now = int(time.time())
        payload = {
            "sub": user.id,
            "companyUserId": company_user_id,
            "companyId": company_id,
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "exp": now + 7200,  # 2 horas
        }

        h_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        p_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{h_b64}.{p_b64}".encode("ascii")
        signature = hmac.new(key_str.encode("utf-8"), signing_input, hashlib.sha256).digest()
        s_b64 = _b64url_encode(signature)
        return f"{h_b64}.{p_b64}.{s_b64}"

    @staticmethod
    def validar(token: str, cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            h_b64, p_b64, s_b64 = parts

            jwt_cfg = cfg.get("Jwt", {})
            key_str = jwt_cfg.get("Key") or os.environ.get("JWT_KEY") or "clave_secreta_desarrollo_sistema_empresarial_32chars"
            issuer = jwt_cfg.get("Issuer", "SistemaEmpresarial")
            audience = jwt_cfg.get("Audience", "dashboard")

            signing_input = f"{h_b64}.{p_b64}".encode("ascii")
            expected_sig = hmac.new(key_str.encode("utf-8"), signing_input, hashlib.sha256).digest()
            actual_sig = _b64url_decode(s_b64)
            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            payload = json.loads(_b64url_decode(p_b64).decode("utf-8"))
            now = int(time.time())
            if payload.get("exp", 0) < now:
                return None
            if issuer and payload.get("iss") != issuer:
                return None
            if audience and payload.get("aud") != audience:
                return None

            return payload
        except Exception:
            return None
