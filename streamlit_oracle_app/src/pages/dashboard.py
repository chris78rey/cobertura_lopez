# =========================
# REEMPLAZAR COMPLETO
# src/pages/dashboard.py
# =========================

import streamlit as st

from src.config import get_default_max_rows
from src.oracle_jdbc import query_dataframe
from src.async_jobs import submit_job, render_current_job
from src.ui import hero, metric_card, badge_ok, badge_warn


QUERY_TEMPLATES = {
    "Servidor y usuario actual": """
SELECT
    SYSDATE AS FECHA_SERVIDOR,
    USER AS USUARIO_DB
FROM DUAL
""".strip(),
    "Fecha del servidor": """
SELECT SYSDATE AS FECHA_SERVIDOR
FROM DUAL
""".strip(),
    "Versión de Oracle": """
SELECT * 
FROM PRODUCT_COMPONENT_VERSION
""".strip(),
    "Prueba simple": """
SELECT 1 AS VALOR
FROM DUAL
""".strip(),
    "Consulta libre": "",
}


def dashboard_page():
    hero(
        "Panel de consultas Oracle 11gR2",
        "Interfaz ligera, ordenada y preparada para ejecutar consultas en segundo plano sin congelar la pantalla.",
    )

    top_col1, top_col2, top_col3 = st.columns(3)

    with top_col1:
        metric_card("Usuario Oracle", str(st.session_state.db_user or "-"))

    with top_col2:
        metric_card("Modo de ejecución", "Background")

    with top_col3:
        metric_card("Estado UI", "Estable")

    st.write("")

    tab1, tab2, tab3 = st.tabs(["Consulta", "Resultado", "Ayuda rápida"])

    with tab1:
        left, right = st.columns([2.2, 1])

        with left:
            st.subheader("Editor de consulta")

            template_name = st.selectbox(
                "Plantilla",
                list(QUERY_TEMPLATES.keys()),
                index=0,
            )

            template_sql = QUERY_TEMPLATES[template_name]

            if "sql_editor_value" not in st.session_state:
                st.session_state.sql_editor_value = template_sql

            if template_sql and st.session_state.get("last_template") != template_name:
                st.session_state.sql_editor_value = template_sql
                st.session_state.last_template = template_name

            sql = st.text_area(
                "SQL",
                key="sql_editor_value",
                height=260,
                placeholder="Escriba aquí su consulta SQL...",
            )

        with right:
            st.subheader("Parámetros")
            max_rows = st.number_input(
                "Máximo de filas",
                min_value=1,
                max_value=100000,
                value=get_default_max_rows(),
                step=100,
            )

            st.markdown("### Estado actual")
            future = st.session_state.get("current_future")

            if future is None:
                badge_warn("Sin proceso activo")
            else:
                if future.running():
                    badge_warn("Consulta en ejecución")
                elif future.done():
                    badge_ok("Última consulta finalizada")
                else:
                    badge_warn("Estado no determinado")

            st.write("")
            st.caption(
                "Sugerencia: para producción, limitar las consultas libres y ofrecer solo plantillas controladas."
            )

        btn1, btn2, btn3 = st.columns([1, 1, 1])

        with btn1:
            run_query = st.button(
                "Ejecutar consulta",
                key="dashboard_run_query_button",
                use_container_width=True,
            )

        with btn2:
            refresh_status = st.button(
                "Actualizar estado",
                key="dashboard_refresh_status_button",
                use_container_width=True,
            )

        with btn3:
            clear_result = st.button(
                "Limpiar resultado",
                key="dashboard_clear_result_button",
                use_container_width=True,
            )

        if run_query:
            if not sql.strip():
                st.warning("Debe ingresar una consulta SQL.")
            else:
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

        if refresh_status:
            st.rerun()

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

    with tab2:
        st.subheader("Resultado de la ejecución")

        result = render_current_job()

        if result is None:
            result = st.session_state.get("current_result")

        if result is not None:
            rows_count = len(result.index)
            cols_count = len(result.columns)

            c1, c2, c3 = st.columns(3)

            with c1:
                metric_card("Filas", str(rows_count))

            with c2:
                metric_card("Columnas", str(cols_count))

            with c3:
                metric_card("Exportación", "CSV")

            st.write("")
            st.dataframe(result, use_container_width=True, height=460)

            csv = result.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                "Descargar CSV",
                data=csv,
                file_name="resultado_oracle.csv",
                mime="text/csv",
                use_container_width=False,
            )
        else:
            st.info("Aún no hay resultados para mostrar.")

            current_error = st.session_state.get("current_error")
            if current_error:
                st.error("La última consulta terminó con error.")
                st.code(current_error)

    with tab3:
        st.subheader("Ayuda rápida")
        st.markdown(
            """
            **Buenas prácticas recomendadas**
            - Empiece con consultas pequeñas.
            - Use límite de filas para evitar cargas innecesarias.
            - Prefiera plantillas predefinidas en usuarios finales.
            - Si la consulta tarda, use **Actualizar estado** en lugar de repetir el envío.

            **Notas**
            - La app valida credenciales directamente contra Oracle.
            - La ejecución corre en segundo plano para reducir riesgo de freeze.
            - La conexión RAC sigue usando failover manual.
            """
        )
