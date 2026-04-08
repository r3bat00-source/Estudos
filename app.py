import streamlit as st
import google.generativeai as genai

# 1. Configuração Inicial e Memória
st.set_page_config(page_title="Dashboard de Estudos Pro", layout="wide")

if 'respostas_ia' not in st.session_state:
    st.session_state['respostas_ia'] = {"questoes": "", "resumo": "", "pergunta": ""}

# 2. Configuração da IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("Erro na API Key. Verifique os Secrets do Streamlit.")

# ==========================================
# 📊 BARRA LATERAL
# ==========================================
with st.sidebar:
    st.title("🎯 Meu Desempenho")
    disciplina = st.text_input("Matéria atual:")
    horas = st.number_input("Horas de foco:", min_value=0.0, step=0.5)
    
    st.markdown("---")
    st.subheader("Questões do Dia")
    total = st.number_input("Total feitas:", min_value=0)
    col_a, col_e = st.columns(2)
    with col_a:
        acertos = st.number_input("Acertos:", min_value=0)
    with col_e:
        erros = st.number_input("Erros:", min_value=0)
    
    if st.button("Salvar Progresso"):
        st.sidebar.success(f"Dados de {disciplina} registrados!")

# ==========================================
# 🤖 ÁREA PRINCIPAL
# ==========================================
st.title("📚 Tutor Inteligente Multimatérias")
st.info("Agora você pode subir vários PDFs ao mesmo tempo para estudar o combo completo!")

# Upload de múltiplos arquivos
arquivos_pdf = st.file_uploader(
    "Selecione seus PDFs de estudo:", 
    type="pdf", 
    accept_multiple_files=True
)

if arquivos_pdf:
    st.success(f"Analisando {len(arquivos_pdf)} material(is).")
    
    # Preparando a lista de arquivos para a IA
    docs_ia = []
    for pdf in arquivos_pdf:
        docs_ia.append({
            "mime_type": "application/pdf",
            "data": pdf.getvalue()
        })
    
    # Abas de Funcionalidades
    t_quest, t_resumo, t_duvida = st.tabs(["📝 Simulado", "📑 Resumo Integrado", "💬 Chat com PDF"])
    
    with t_quest:
        if st.button("Gerar Questões do Combo"):
            with st.spinner("Criando questões baseadas em todos os arquivos..."):
                prompt = "Gere 3 questões de múltipla escolha baseadas nestes documentos, com gabarito comentado ao final."
                resp = model.generate_content([prompt] + docs_ia)
                st.session_state['respostas_ia']['questoes'] = resp.text
        if st.session_state['respostas_ia']['questoes']:
            st.write(st.session_state['respostas_ia']['questoes'])

    with t_resumo:
        if st.button("Gerar Resumo dos Materiais"):
            with st.spinner("Sintetizando os arquivos..."):
                prompt = "Crie um resumo único e conectado que englobe os pontos principais de todos os PDFs fornecidos."
                resp = model.generate_content([prompt] + docs_ia)
                st.session_state['respostas_ia']['resumo'] = resp.text
        if st.session_state['respostas_ia']['resumo']:
            st.write(st.session_state['respostas_ia']['resumo'])

    with t_duvida:
        user_ask = st.text_input("O que você quer saber sobre esses materiais?")
        if st.button("Perguntar à IA"):
            if user_ask:
                with st.spinner("Buscando resposta..."):
                    prompt = f"Com base nos PDFs fornecidos, responda: {user_ask}"
                    resp = model.generate_content([prompt] + docs_ia)
                    st.session_state['respostas_ia']['pergunta'] = resp.text
        if st.session_state['respostas_ia']['pergunta']:
            st.write(st.session_state['respostas_ia']['pergunta'])
