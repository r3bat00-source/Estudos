import streamlit as st
import google.generativeai as genai
import json
import re
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# 1. Configuração de Página
st.set_page_config(page_title="Dashboard de Estudos Pro", layout="wide")

# Inicialização de Memória (Session State)
if 'questoes_lista' not in st.session_state:
    st.session_state['questoes_lista'] = []
if 'mostrar_gabarito' not in st.session_state:
    st.session_state['mostrar_gabarito'] = False
if 'resumo_texto' not in st.session_state:
    st.session_state['resumo_texto'] = ""

# 2. Configurações de API
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("Erro na API Key do Gemini. Verifique os Secrets.")

def conectar_planilha():
    try:
        # Puxa o JSON que você colou nos Secrets
        cred_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
        escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(cred_dict, scopes=escopos)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo nome exato
        sheet = client.open("Banco de Estudos").sheet1
        return sheet
    except Exception as e:
        st.sidebar.error(f"Erro no Sheets: {e}")
        return None

# ==========================================
# 📊 BARRA LATERAL
# ==========================================
with st.sidebar:
    st.title("🎯 Painel de Controle")
    disciplina = st.text_input("Matéria:")
    horas = st.number_input("Horas de Foco:", min_value=0.0, step=0.5)
    
    st.divider()
    st.subheader("Desempenho da Sessão")
    total_q = st.number_input("Total de Questões:", min_value=0)
    col_a, col_e = st.columns(2)
    with col_a:
        acertos = st.number_input("Acertos:", min_value=0)
    with col_e:
        erros = st.number_input("Erros:", min_value=0)
    
    if st.button("☁️ Salvar na Planilha", use_container_width=True):
        if disciplina:
            with st.spinner("Enviando dados..."):
                planilha = conectar_planilha()
                if planilha:
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    data_hora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                    planilha.append_row([data_hora, disciplina, horas, total_q, acertos, erros])
                    st.success("Dados salvos no Google Sheets!")
        else:
            st.warning("Informe a Disciplina.")

    st.divider()
    if st.button("🗑️ Limpar Questões", use_container_width=True):
        st.session_state['questoes_lista'] = []
        st.session_state['mostrar_gabarito'] = False
        st.rerun()

# ==========================================
# 🚀 ÁREA PRINCIPAL
# ==========================================
st.title("📚 Tutor Inteligente (Multimodal)")

arquivos = st.file_uploader("Selecione seus PDFs", type="pdf", accept_multiple_files=True)

if arquivos:
    docs_ia = [{"mime_type": "application/pdf", "data": f.getvalue()} for f in arquivos]
    
    aba1, aba2, aba3 = st.tabs(["📝 Simulado", "📑 Resumo", "💬 Chat"])

    # --- ABA 1: SIMULADO ---
    with aba1:
        col1, col2 = st.columns([1, 2])
        with col1:
            qtd = st.number_input("Número de questões:", min_value=1, max_value=10, value=3)
        with col2:
            st.write("") # Alinhamento
            st.write("")
            if st.button("🚀 GERAR SIMULADO", type="primary", use_container_width=True):
                st.session_state['mostrar_gabarito'] = False
                with st.spinner("A IA está analisando seus PDFs..."):
                    prompt = f"""
                    Gere {qtd} questões de múltipla escolha baseadas nos PDFs.
                    Retorne APENAS um JSON puro (sem markdown) neste formato:
                    [{{"pergunta": "...", "opcoes": ["A) ..", "B) ..", "C) ..", "D) ..", "E) .."], "correta": "A) ..", "explica": ".."}}]
                    """
                    resp = model.generate_content([prompt] + docs_ia)
                    match = re.search(r'\[.*\]', resp.text, re.DOTALL)
                    if match:
                        st.session_state['questoes_lista'] = json.loads(match.group())
                        st.rerun()

        if st.session_state['questoes_lista']:
            st.divider()
            for i, item in enumerate(st.session_state['questoes_lista']):
                st.markdown(f"**{i+1}. {item['pergunta']}**")
                st.radio("Escolha a alternativa:", item['opcoes'], key=f"q_{i}", index=None, label_visibility="collapsed")
                st.write("")

            if st.button("✅ VERIFICAR RESPOSTAS", use_container_width=True):
                st.session_state['mostrar_gabarito'] = True

            if st.session_state['mostrar_gabarito']:
                st.subheader("📊 Gabarito Comentado")
                for i, item in enumerate(st.session_state['questoes_lista']):
                    escolha = st.session_state.get(f"q_{i}")
                    if escolha == item['correta']:
                        st.success(f"Questão {i+1}: Correta! ✅")
                    else:
                        st.error(f"Questão {i+1}: Errada. Você marcou {escolha}. A correta é {item['correta']}")
                    st.info(f"💡 Explicação: {item['explica']}")

    # --- ABA 2: RESUMO ---
    with aba2:
        if st.button("Criar Resumo dos PDFs"):
            with st.spinner("Sintetizando..."):
                res = model.generate_content(["Crie um resumo estruturado desses PDFs:", docs_ia])
                st.session_state['resumo_texto'] = res.text
        if st.session_state['resumo_texto']:
            st.markdown(st.session_state['resumo_texto'])

    # --- ABA 3: CHAT ---
    with aba3:
        pergunta = st.text_input("Sua dúvida:")
        if st.button("Enviar Pergunta"):
            if pergunta:
                with st.spinner("Pensando..."):
                    res = model.generate_content([f"Baseado no PDF, responda: {pergunta}", docs_ia])
                    st.write(res.text)
