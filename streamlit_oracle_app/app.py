# =========================
# NUEVO: punto de entrada Streamlit
# =========================

import streamlit as st

from src.auth import init_auth_state, login_screen, logout_button
from src.pages.dashboard import dashboard_page


st.set_page_config(
    page_title="Oracle Streamlit App",
    page_icon="🗄️",
    layout="wide",
)


def main():
    init_auth_state()

    if not st.session_state.auth_ok:
        login_screen()
        return

    logout_button()
    dashboard_page()


if __name__ == "__main__":
    main()

# =========================
# FIN NUEVO
# =========================
