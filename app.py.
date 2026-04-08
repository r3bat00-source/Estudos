import streamlit as st
import pandas as pd

st.set_page_config(page_title="Samara - Meta de Estudos", page_icon="📚")

st.title("📚 Meu Ciclo de Estudos")

# Criar a estrutura na memória do navegador
if 'dados' not in st.session_state:
    st.session_state.dados = []

# Formulário para adicionar matérias
with st.expander("➕ Adicionar Nova Matéria", expanded=True):
    materia = st.text_input("Matéria (ex: Português, Raciocínio Lógico)")
    horas_meta = st.number_input("Meta de Horas Semanais", min_value=1)
    questoes = st.number_input("Questões Resolvidas Hoje", min_value=0)
    
    if st.button("Salvar Registro"):
        st.session_state.dados.append({
            "Matéria": materia, 
            "Meta (h)": horas_meta, 
            "Questões": questoes
        })
        st.success("Registrado!")

# Exibir os dados
if st.session_state.dados:
    df = pd.DataFrame(st.session_state.dados)
    st.divider()
    st.subheader("Resumo da Semana")
    st.dataframe(df, use_container_width=True)
    
    # Gráfico de Progresso
    st.bar_chart(df.set_index("Matéria")["Questões"])

    if st.button("Limpar Tudo"):
        st.session_state.dados = []
        st.rerun()
