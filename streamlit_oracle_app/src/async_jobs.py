# =========================
# NUEVO: ejecución en segundo plano para evitar freeze
# =========================

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, Future

import streamlit as st

from src.config import get_max_workers


@st.cache_resource
def get_executor() -> ThreadPoolExecutor:
    """
    Executor global.

    Nota:
    - El executor sí se puede compartir.
    - Las conexiones Oracle NO se comparten.
    - Cada tarea abre y cierra su propia conexión.
    """
    return ThreadPoolExecutor(max_workers=get_max_workers())


def submit_job(job_name: str, func, *args, **kwargs) -> Future:
    executor = get_executor()
    future = executor.submit(func, *args, **kwargs)

    st.session_state.current_future = future
    st.session_state.current_job_name = job_name
    st.session_state.current_result = None
    st.session_state.current_error = None

    return future


def render_current_job():
    """
    Renderiza el estado de la tarea actual.
    No bloquea la pantalla esperando el resultado.
    """

    future: Future | None = st.session_state.get("current_future")

    if not future:
        return None

    job_name = st.session_state.get("current_job_name", "Proceso")

    if future.running():
        st.info(f"{job_name} en ejecución. La pantalla no está bloqueada.")
        st.caption("Puede presionar 'Actualizar estado' para revisar si ya terminó.")

        if st.button("Actualizar estado", use_container_width=True):
            st.rerun()

        return None

    if future.done():
        try:
            result = future.result()
            st.session_state.current_result = result
            st.session_state.current_error = None
            st.success(f"{job_name} finalizado correctamente.")
            return result

        except Exception as exc:
            st.session_state.current_result = None
            st.session_state.current_error = str(exc)
            st.error(f"{job_name} terminó con error.")
            st.code(str(exc))
            return None

    return None

# =========================
# FIN NUEVO
# =========================
