import streamlit as st
from scr.components.heat_map import render_heatmap
from scr.components.auth_form import render_auth, render_logout


st.set_page_config(layout="wide")

co1, co2 = st.columns([1, 2])

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

with co1:
    if not st.session_state["authenticated"]:
        render_auth()
    else:
        st.write(f"Hello, {st.session_state.get('account_id', 'user')}")
        render_logout()

with co2:    
    if st.session_state["authenticated"]:
        render_heatmap()
    else:
        st.info("Login to access heatmap")