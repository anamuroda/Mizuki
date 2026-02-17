import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# Conexão Local
engine = create_engine("sqlite:///mizuki.db")

st.set_page_config(page_title="Mizuki Dashboard", layout="wide")
st.title("🎌 Mizuki Intelligence")

df = pd.read_sql("SELECT * FROM scraping_results", engine)

if not df.empty:
    target_ids = df['target_id'].unique()
    selected = st.selectbox("Selecione ID do Produto", target_ids)
    
    data = df[df['target_id'] == selected]
    
    col1, col2 = st.columns(2)
    col1.metric("Preço Atual", f"R$ {data.iloc[-1]['price']:.2f}")
    col2.metric("Status", "Em Estoque" if data.iloc[-1]['available'] else "Esgotado")
    
    fig = px.line(data, x='scraped_at', y='price', title="Evolução de Preço", markers=True)
    st.plotly_chart(fig)
else:
    st.info("Sem dados ainda.")