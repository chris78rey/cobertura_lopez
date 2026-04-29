# =========================
# NUEVO: exportación CSV de planillas por ID_GENERACION
# =========================

from __future__ import annotations

import csv
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from src.oracle_jdbc import oracle_connect


def _validate_id_generacion(value: str) -> str:
    """
    Valida ID_GENERACION para evitar entradas raras.

    Se permite:
    - números
    - letras
    - guion
    - guion bajo
    - punto

    Si en la base DIG_ID_GENERACION es solo numérico, cambiar la expresión
    por: r"^[0-9]+$"
    """

    clean_value = str(value or "").strip()

    if not clean_value:
        raise RuntimeError("Debe ingresar el ID_GENERACION.")

    if not re.match(r"^[A-Za-z0-9_.-]+$", clean_value):
        raise RuntimeError(
            "ID_GENERACION inválido. Solo se permiten letras, números, punto, guion y guion bajo."
        )

    return clean_value


def buscar_id_generacion(
    username: str,
    password: str,
    id_generacion: str,
    timeout_seconds: int = 60,
) -> dict:
    """
    Valida si existe información exportable para el ID_GENERACION.

    No devuelve registros.
    Solo devuelve cantidad.
    """

    id_generacion = _validate_id_generacion(id_generacion)

    conn = None
    prepared_statement = None
    result_set = None

    sql = """
        SELECT COUNT(1)
        FROM digitalizacion d
        WHERE d.dig_id_generacion = ?
          AND d.dig_fecha_planilla IS NOT NULL
          AND d.dig_planillado = 'S'
    """

    try:
        conn = oracle_connect(username, password)
        java_conn = conn.jconn

        prepared_statement = java_conn.prepareStatement(sql)
        prepared_statement.setString(1, id_generacion)
        prepared_statement.setQueryTimeout(int(timeout_seconds))

        result_set = prepared_statement.executeQuery()

        total = 0

        if result_set.next():
            total = int(result_set.getLong(1))

        return {
            "ok": True,
            "id_generacion": id_generacion,
            "found": total > 0,
            "rows": total,
            "error": None,
        }

    finally:
        if result_set:
            try:
                result_set.close()
            except Exception:
                pass

        if prepared_statement:
            try:
                prepared_statement.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass


def export_planillas_csv_no_header(
    username: str,
    password: str,
    id_generacion: str,
    timeout_seconds: int = 300,
    fetch_size: int = 5000,
) -> dict[str, Any]:
    """
    Genera CSV UTF-8 sin encabezado.

    No carga todo en memoria.
    No devuelve DataFrame.
    No muestra el SQL al usuario.
    """

    id_generacion = _validate_id_generacion(id_generacion)

    conn = None
    prepared_statement = None
    result_set = None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_file_name = f"planillas_{id_generacion}_{timestamp}.csv"

    output_dir = Path(tempfile.gettempdir()) / "streamlit_oracle_exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / safe_file_name

    sql = """
        SELECT
            TO_CHAR(d.dig_tramite) AS planilla,
            d.dig_cedula AS cedula,
            TO_CHAR(d.dig_fecha_planilla, 'dd-mm-yyyy') AS fecha
        FROM digitalizacion d
        WHERE d.dig_id_generacion = ?
          AND d.dig_fecha_planilla IS NOT NULL
          AND d.dig_planillado = 'S'
    """

    total_rows = 0

    try:
        conn = oracle_connect(username, password)
        java_conn = conn.jconn

        prepared_statement = java_conn.prepareStatement(sql)
        prepared_statement.setString(1, id_generacion)
        prepared_statement.setQueryTimeout(int(timeout_seconds))
        prepared_statement.setFetchSize(int(fetch_size))

        result_set = prepared_statement.executeQuery()

        with output_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(
                csv_file,
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
                lineterminator="\n",
            )

            while result_set.next():
                planilla = result_set.getString(1)
                cedula = result_set.getString(2)
                fecha = result_set.getString(3)

                writer.writerow([
                    planilla or "",
                    cedula or "",
                    fecha or "",
                ])

                total_rows += 1

        return {
            "ok": True,
            "file_path": str(output_path),
            "file_name": safe_file_name,
            "rows": total_rows,
            "error": None,
        }

    except Exception as exc:
        message = str(exc)

        if "ORA-01013" in message or "cancel" in message.lower() or "timeout" in message.lower():
            raise RuntimeError(
                f"La exportación superó el timeout configurado de {timeout_seconds} segundos "
                "y fue cancelada por el driver JDBC."
            ) from exc

        raise

    finally:
        if result_set:
            try:
                result_set.close()
            except Exception:
                pass

        if prepared_statement:
            try:
                prepared_statement.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass

# =========================
# FIN NUEVO
# =========================
