import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_product_card import product_card


def on_button_click(url):
    st.session_state.open_url = url


sheet_url = "https://docs.google.com/spreadsheets/d/13EsNyrFZvw4GNb79eqAql4CMD9ilqtInubcRKbRLLWE/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(spreadsheet=sheet_url)

row1 = st.columns(2, width="stretch")

with row1[0]:
    product_card(
        product_name=data.iloc[0, 4],
        description=data.iloc[0, 5],
        button_text="Sign Up",
        on_button_click=lambda: on_button_click(str(data.iloc[0, 11])),
        styles={"button": {"background-color": "green", "color": "white"}},
    )

with row1[1]:
    product_card(
        product_name=data.iloc[1, 4],
        description=data.iloc[1, 5],
        button_text="Sign Up",
        on_button_click=lambda: on_button_click(str(data.iloc[1, 11])),
    )

if "open_url" in st.session_state:
    target_url = st.session_state.pop("open_url")
    st.link_button(
        "Continue to Sign Up →",
        url=target_url,
        type="primary",
        use_container_width=True,
    )