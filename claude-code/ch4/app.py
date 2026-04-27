"""製造設備モニタリング"""

import streamlit as st

st.set_page_config(page_title="設備モニタリング", page_icon="🏭", layout="wide")

pg = st.navigation([
    st.Page("pages/01_equipment_dashboard.py", title="設備ダッシュボード", icon="🔧"),
])
pg.run()
