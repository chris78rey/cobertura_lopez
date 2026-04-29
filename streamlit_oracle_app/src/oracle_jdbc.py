# =========================
# NUEVO: conexión Oracle JDBC con failover manual
# =========================

from __future__ import annotations

import pandas as pd
import jaydebeapi

from src.config import get_jdbc_jar, get_oracle_targets


ORACLE_DRIVER = "oracle.jdbc.OracleDriver"


def oracle_connect(username: str, password: str):
    """
    Crea una conexión nueva a Oracle usando JDBC.

    Importante:
    - No se comparte la conexión entre usuarios.
    - No se cachea globalmente.
    - Se intenta nodo por nodo para soportar failover manual.
    """

    if not username or not password:
        raise RuntimeError("Usuario o contraseña vacíos")

    jar = get_jdbc_jar()
    targets = get_oracle_targets()

    last_error: Exception | None = None

    for host, port, sid in targets:
        url = f"jdbc:oracle:thin:@{host}:{port}:{sid}"

        try:
            conn = jaydebeapi.connect(
                ORACLE_DRIVER,
                url,
                [username, password],
                jars=[str(jar)],
            )
            return conn

        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"No fue posible conectar a Oracle en ningún nodo. Último error: {last_error}"
    )


def test_login(username: str, password: str) -> dict:
    """
    Valida las credenciales contra Oracle.
    Si conecta y ejecuta SELECT 1 FROM DUAL, el login es correcto.
    """

    conn = None

    try:
        conn = oracle_connect(username, password)
        cursor = conn.cursor()
        cursor.execute("SELECT USER FROM DUAL")
        row = cursor.fetchone()
        cursor.close()

        return {
            "ok": True,
            "db_user": row[0] if row else username.upper(),
            "error": None,
        }

    except Exception as exc:
        return {
            "ok": False,
            "db_user": None,
            "error": str(exc),
        }

    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def query_dataframe(
    username: str,
    password: str,
    sql: str,
    params: list | tuple | None = None,
    max_rows: int = 500,
) -> pd.DataFrame:
    """
    Ejecuta una consulta y devuelve DataFrame.

    Protección:
    - Abre conexión nueva por consulta.
    - Cierra conexión al finalizar.
    - Aplica límite defensivo de filas envolviendo la consulta.
    """

    conn = None

    safe_sql = f"""
        SELECT *
        FROM (
            {sql}
        )
        WHERE ROWNUM <= {int(max_rows)}
    """

    try:
        conn = oracle_connect(username, password)
        cursor = conn.cursor()

        cursor.execute(safe_sql, params or [])

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        cursor.close()

        return pd.DataFrame(rows, columns=columns)

    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

# =========================
# FIN NUEVO
# =========================
