# =========================
# NUEVO: pantalla principal de consulta
# =========================

import streamlit as st

from src.config import get_default_max_rows
from src.oracle_jdbc import query_dataframe
from src.async_jobs import submit_job, render_current_job


def dashboard_page():
    st.title("Consulta Oracle 11gR2")

    st.write(
        "Esta pantalla ejecuta consultas en segundo plano para evitar que la interfaz se congele."
    )

    st.divider()

    with st.expander("Consulta rápida", expanded=True):
        default_sql = """
SELECT
    SYSDATE AS FECHA_SERVIDOR,
    USER AS USUARIO_DB
FROM DUAL
""".strip()

        sql = st.text_area(
            "SQL",
            value=default_sql,
            height=180,
        )

        max_rows = st.number_input(
            "Máximo de filas",
            min_value=1,
            max_value=10000,
            value=get_default_max_rows(),
            step=100,
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            run_query = st.button("Ejecutar consulta", use_container_width=True)

        with col2:
            clear_result = st.button("Limpiar resultado", use_container_width=True)

    if clear_result:
        for key in [
            "current_future",
            "current_job_name",
            "current_result",
            "current_error",
        ]:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()

    if run_query:
        submit_job(
            "Consulta Oracle",
            query_dataframe,
            st.session_state.oracle_user,
            st.session_state.oracle_password,
            sql,
            None,
            int(max_rows),
        )

        st.rerun()

    result = render_current_job()

    if result is None:
        result = st.session_state.get("current_result")

    if result is not None:
        st.subheader("Resultado")
        st.dataframe(result, use_container_width=True)

        csv = result.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "Descargar CSV",
            data=csv,
            file_name="resultado_oracle.csv",
            mime="text/csv",
            use_container_width=True,
        )

# =========================
# FIN NUEVO
# =========================
