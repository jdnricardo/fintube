import os
import hmac
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
PASSWORD = os.getenv("STREAMLIT_PW")

def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], PASSWORD):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False
