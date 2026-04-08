import streamlit as st
import pandas as pd

# Configuração da página e Título (Já corrigi seu nome aqui!)
st.set_page_config(page_title="Dashboard do Renatinho", layout="wide")

st.title("🚀 Painel de Controle de Estudos - Renatinho")

# --- BARRA LATERAL (Interface mais limpa) ---
st.sidebar.header("📥 Registrar Progresso")
with st.sidebar.form("formulario"):
    materia = st.sidebar.text_input("Nome da Matéria")
    horas = st.sidebar.number_input("Horas Estudadas", min_value=0.5, step=0.5)
    questoes = st.sidebar.number_input("Questões Feitas", min_value=0)
    enviar = st.sidebar.form_submit_button("Atualizar Dashboard")

# Memória do App
if 'dados' not in st.session_state:
    st.session_state.dados = []

if enviar and materia:
    st.session_state.dados.append({"Matéria": materia, "Horas": horas, "Questões": questoes})
    st.sidebar.success("Dados salvos!")

# --- CORPO PRINCIPAL ---
if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    
    # Métricas no topo
    col1, col2 = st.columns(2)
    col1.metric("Total de Horas", f"{df['Horas'].sum()}h")
    col2.metric("Total de Questões", df['Questões'].sum())

    st.divider()

    # Gráficos Lado a Lado
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Horas por Matéria")
        st.bar_chart(df.set_index("Matéria")["Horas"])
    with c2:
        st.subheader("🎯 Desempenho em Questões")
        st.line_chart(df.set_index("Matéria")["Questões"])

    st.table(df)
else:
    st.info("Aguardando seu primeiro registro na barra lateral ao lado! 👈")
