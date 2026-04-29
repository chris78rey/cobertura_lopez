# =========================
# REEMPLAZAR COMPLETO
# src/pages/dashboard.py
# Flujo minimalista:
# 1. Buscar código
# 2. Confirmar encontrado
# 3. Preparar CSV
# 4. Descargar
# =========================

from pathlib import Path

import streamlit as st

from src.async_jobs import submit_job, render_current_job
from src.export_planillas import (
    buscar_id_generacion,
    export_planillas_csv_no_header,
)


# =========================
# CONFIGURACIÓN OCULTA
# =========================

DEFAULT_SEARCH_TIMEOUT_SECONDS = 60
DEFAULT_EXPORT_TIMEOUT_SECONDS = 600
DEFAULT_FETCH_SIZE = 5000


def _clear_job_state():
    for key in [
        "current_future",
        "current_job_name",
        "current_result",
        "current_error",
        "current_timeout_seconds",
        "current_started_at_utc",
        "current_timed_out_ui",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def _clear_search_state():
    for key in [
        "codigo_buscado",
        "codigo_encontrado",
        "codigo_total_registros",
        "codigo_validado",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def _init_state():
    if "codigo_buscado" not in st.session_state:
        st.session_state.codigo_buscado = ""

    if "codigo_encontrado" not in st.session_state:
        st.session_state.codigo_encontrado = False

    if "codigo_total_registros" not in st.session_state:
        st.session_state.codigo_total_registros = 0

    if "codigo_validado" not in st.session_state:
        st.session_state.codigo_validado = False


def _render_minimal_css():
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 720px;
            padding-top: 2.2rem;
        }

        section[data-testid="stSidebar"] {
            display: none;
        }

        .main-title {
            text-align: center;
            font-size: 2rem;
            font-weight: 850;
            color: #0f172a;
            margin-bottom: 0.35rem;
        }

        .main-subtitle {
            text-align: center;
            color: #64748b;
            font-size: 1rem;
            margin-bottom: 2rem;
        }

        .simple-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            padding: 1.6rem;
            box-shadow: 0 14px 38px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.2rem;
        }

        .status-ok {
            background: #ecfdf5;
            border: 1px solid #bbf7d0;
            color: #166534;
            border-radius: 18px;
            padding: 1rem;
            font-weight: 750;
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .status-warn {
            background: #fff7ed;
            border: 1px solid #fed7aa;
            color: #9a3412;
            border-radius: 18px;
            padding: 1rem;
            font-weight: 700;
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .status-info {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1e3a8a;
            border-radius: 18px;
            padding: 1rem;
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .status-success {
            background: #ecfdf5;
            border: 1px solid #bbf7d0;
            color: #166534;
            border-radius: 18px;
            padding: 1rem;
            text-align: center;
            font-weight: 800;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .stTextInput input {
            font-size: 1.15rem !important;
            border-radius: 16px !important;
            padding: 0.85rem !important;
        }

        .stButton > button {
            border-radius: 16px !important;
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            padding: 0.85rem 1rem !important;
        }

        div[data-testid="stDownloadButton"] > button {
            border-radius: 16px !important;
            font-size: 1.05rem !important;
            font-weight: 850 !important;
            padding: 0.85rem 1rem !important;
            background-color: #16a34a !important;
            color: white !important;
            border: none !important;
        }

        div[data-testid="stDownloadButton"] > button:hover {
            background-color: #15803d !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_download_button(result: dict | None):
    if not result:
        return

    if not isinstance(result, dict):
        st.error("No se pudo preparar el archivo generado.")
        return

    if not result.get("ok"):
        st.error("No se pudo generar el archivo.")
        return

    file_path = Path(result["file_path"])
    file_name = result["file_name"]
    rows = int(result.get("rows", 0))

    if not file_path.exists():
        st.error("El archivo generado ya no está disponible. Vuelva a generarlo.")
        return

    st.markdown(
        f"""
        <div class="status-success">
            Archivo listo para descargar<br>
            Registros exportados: {rows:,}
        </div>
        """.replace(",", "."),
        unsafe_allow_html=True,
    )

    with file_path.open("rb") as file:
        st.download_button(
            "Descargar CSV",
            data=file,
            file_name=file_name,
            mime="text/csv",
            key="download_planillas_csv_button",
            use_container_width=True,
        )


def dashboard_page():
    _init_state()
    _render_minimal_css()

    st.markdown(
        """
        <div class="main-title">Exportar planillas</div>
        <div class="main-subtitle">
            Busque el código de generación y descargue el archivo CSV.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="simple-card">', unsafe_allow_html=True)

    codigo_generacion = st.text_input(
        "Código de generación",
        placeholder="Ingrese el código de generación",
        key="planillas_id_generacion_input",
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        buscar = st.button(
            "Buscar",
            key="buscar_codigo_generacion_button",
            use_container_width=True,
        )

    with col2:
        preparar_descarga = st.button(
            "Preparar descarga",
            key="preparar_descarga_button",
            use_container_width=True,
            disabled=not st.session_state.codigo_encontrado,
        )

    if buscar:
        _clear_job_state()
        _clear_search_state()

        codigo_limpio = codigo_generacion.strip()

        if not codigo_limpio:
            st.warning("Ingrese el código de generación.")
        else:
            with st.spinner("Buscando código de generación..."):
                try:
                    result = buscar_id_generacion(
                        st.session_state.oracle_user,
                        st.session_state.oracle_password,
                        codigo_limpio,
                        DEFAULT_SEARCH_TIMEOUT_SECONDS,
                    )

                    st.session_state.codigo_buscado = codigo_limpio
                    st.session_state.codigo_validado = True
                    st.session_state.codigo_encontrado = bool(result["found"])
                    st.session_state.codigo_total_registros = int(result["rows"])

                    st.rerun()

                except Exception as exc:
                    st.session_state.codigo_validado = False
                    st.session_state.codigo_encontrado = False
                    st.session_state.codigo_total_registros = 0
                    st.error("No se pudo realizar la búsqueda.")
                    st.code(str(exc))

    if st.session_state.codigo_validado:
        if st.session_state.codigo_encontrado:
            st.markdown(
                f"""
                <div class="status-ok">
                    Código encontrado<br>
                    Registros disponibles: {st.session_state.codigo_total_registros:,}
                </div>
                """.replace(",", "."),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="status-warn">
                    No se encontraron registros para ese código.
                </div>
                """,
                unsafe_allow_html=True,
            )

    if preparar_descarga:
        _clear_job_state()

        submit_job(
            "Preparación del archivo CSV",
            export_planillas_csv_no_header,
            st.session_state.oracle_user,
            st.session_state.oracle_password,
            st.session_state.codigo_buscado,
            DEFAULT_EXPORT_TIMEOUT_SECONDS,
            DEFAULT_FETCH_SIZE,
            timeout_seconds=DEFAULT_EXPORT_TIMEOUT_SECONDS,
        )

        st.rerun()

    future = st.session_state.get("current_future")

    if future:
        st.markdown(
            """
            <div class="status-info">
                Preparando archivo. La pantalla seguirá activa mientras finaliza el proceso.
            </div>
            """,
            unsafe_allow_html=True,
        )

        result = render_current_job()

        if result is None:
            result = st.session_state.get("current_result")

        _render_download_button(result)

    current_error = st.session_state.get("current_error")

    if current_error:
        st.error("No se pudo preparar el archivo.")
        with st.expander("Ver detalle técnico"):
            st.code(current_error)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    if st.button(
        "Salir",
        key="minimal_logout_button",
        use_container_width=True,
    ):
        st.session_state.auth_ok = False
        st.session_state.oracle_user = None
        st.session_state.oracle_password = None
        st.session_state.db_user = None
        _clear_job_state()
        _clear_search_state()
        st.rerun()


# =========================
# FIN
# =========================
