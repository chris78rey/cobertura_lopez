# =========================
# NUEVO: login contra Oracle
# =========================

import streamlit as st

from src.oracle_jdbc import test_login


def init_auth_state():
    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False

    if "oracle_user" not in st.session_state:
        st.session_state.oracle_user = None

    if "oracle_password" not in st.session_state:
        st.session_state.oracle_password = None

    if "db_user" not in st.session_state:
        st.session_state.db_user = None


def login_screen():
    st.title("Sistema de Consulta Oracle")

    st.caption("Ingreso con credenciales de base de datos Oracle")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuario Oracle").strip()
        password = st.text_input("Contraseña Oracle", type="password")

        submitted = st.form_submit_button("Ingresar", use_container_width=True)

    if submitted:
        if not username or not password:
            st.warning("Debe ingresar usuario y contraseña.")
            return

        with st.spinner("Validando credenciales contra Oracle..."):
            result = test_login(username, password)

        if result["ok"]:
            st.session_state.auth_ok = True
            st.session_state.oracle_user = username
            st.session_state.oracle_password = password
            st.session_state.db_user = result["db_user"]

            st.rerun()

        else:
            st.error("No fue posible ingresar con esas credenciales.")
            st.code(result["error"])


def logout_button():
    with st.sidebar:
        st.caption(f"Usuario conectado: {st.session_state.db_user}")

        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.auth_ok = False
            st.session_state.oracle_user = None
            st.session_state.oracle_password = None
            st.session_state.db_user = None

            clear_jobs_state()

            st.rerun()


def clear_jobs_state():
    keys = [
        "current_future",
        "current_job_name",
        "current_result",
        "current_error",
    ]

    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

# =========================
# FIN NUEVO
# =========================
