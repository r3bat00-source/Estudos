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

# 2. Configurações de API e Conexão
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("Erro na API Key do Gemini. Verifique os Secrets.")

def conectar_planilha():
    try:
        cred_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
        escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(cred_dict, scopes=escopos)
        client = gspread.authorize(creds)
        return client.open("Banco de Estudos")
    except Exception as e:
        st.sidebar.error(f"Erro na conexão: {e}")
        return None

def salvar_estado(questoes=None, resumo=None):
    gc = conectar_planilha()
    if gc:
        try:
            aba_estado = gc.worksheet("Estado_Atual")
            if questoes is not None:
                aba_estado.update_acell('A1', json.dumps(questoes))
            if resumo is not None:
                aba_estado.update_acell('B1', resumo)
        except:
            st.error("Aba 'Estado_Atual' não encontrada na planilha.")

def carregar_estado():
    gc = conectar_planilha()
    if gc:
        try:
            aba_estado = gc.worksheet("Estado_Atual")
            questoes_raw = aba_estado.acell('A1').value
            resumo_raw = aba_estado.acell('B1').value
            
            questoes = json.loads(questoes_raw) if questoes_raw else []
            resumo = resumo_raw if resumo_raw else ""
            return questoes, resumo
        except:
            return [], ""
    return [], ""

# --- Inicialização da Memória (Tenta carregar da Planilha se o Session State estiver vazio) ---
if 'questoes_lista' not in st.session_state or not st.session_state['questoes_lista']:
    q, r = carregar_estado()
    st.session_state['questoes_lista'] = q
    st.session_state['resumo_texto'] = r

if 'mostrar_gabarito' not in st.session_state:
    st.session_state['mostrar_gabarito'] = False

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
    
    if st.button("☁️ Salvar Registro Final", use_container_width=True):
        if disciplina:
            with st.spinner("Enviando dados..."):
                gc = conectar_planilha()
                if gc:
                    planilha_log = gc.sheet1 # Primeira aba (Registro)
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    data_hora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                    planilha_log.append_row([data_hora, disciplina, horas, total_q, acertos, erros])
                    st.success("Progresso salvo!")
        else:
            st.warning("Informe a Disciplina.")

    st.divider()
    if st.button("🗑️ Limpar Tudo (App e Nuvem)", use_container_width=True):
        st.session_state['questoes_lista'] = []
        st.session_state['resumo_texto'] = ""
        st.session_state['mostrar_gabarito'] = False
        salvar_estado([], "") # Limpa a planilha de estado também
        st.rerun()

# ==========================================
# 🚀 ÁREA PRINCIPAL
# ==========================================
st.title("📚 Sistema de Estudos com Memória")

arquivos = st.file_uploader("Suba seus arquivos", type="pdf", accept_multiple_files=True)

if arquivos:
    docs_ia = [{"mime_type": "application/pdf", "data": f.getvalue()} for f in arquivos]
    
    aba1, aba2, aba3 = st.tabs(["📝 Simulado", "📑 Resumo", "💬 Chat"])

    with aba1:
        col1, col2 = st.columns([1, 2])
        with col1:
            qtd = st.number_input("Quantas questões?", min_value=1, max_value=10, value=3)
        with col2:
            st.write("")
            st.write("")
            if st.button("🚀 GERAR NOVO SIMULADO", type="primary", use_container_width=True):
                st.session_state['mostrar_gabarito'] = False
                with st.spinner("Gerando questões..."):
                    prompt = f"Gere {qtd} questões de múltipla escolha baseadas nos PDFs em JSON puro: pergunta, opcoes (lista A-E), correta, explica."
                    resp = model.generate_content([prompt] + docs_ia)
                    match = re.search(r'\[.*\]', resp.text, re.DOTALL)
                    if match:
                        dados = json.loads(match.group())
                        st.session_state['questoes_lista'] = dados
                        salvar_estado(questoes=dados) # SALVA NA PLANILHA
                        st.rerun()

        if st.session_state['questoes_lista']:
            st.info("💡 Estas questões estão salvas na sua nuvem. Você pode fechar o app e elas continuarão aqui.")
            for i, item in enumerate(st.session_state['questoes_lista']):
                st.markdown(f"**{i+1}. {item['pergunta']}**")
                st.radio("Alternativas:", item['opcoes'], key=f"q_{i}", index=None)
            
            if st.button("✅ CONFERIR GABARITO"):
                st.session_state['mostrar_gabarito'] = True
            
            if st.session_state['mostrar_gabarito']:
                for i, item in enumerate(st.session_state['questoes_lista']):
                    escolha = st.session_state.get(f"q_{i}")
                    if escolha == item['correta']:
                        st.success(f"{i+1}: Correta!")
                    else:
                        st.error(f"{i+1}: Incorreta. Resposta: {item['correta']}")
                    st.caption(f"Explicação: {item['explica']}")

    with aba2:
        if st.button("Gerar/Atualizar Resumo"):
            with st.spinner("Escrevendo..."):
                res = model.generate_content(["Resuma estes documentos:", docs_ia])
                st.session_state['resumo_texto'] = res.text
                salvar_estado(resumo=res.text) # SALVA NA PLANILHA
        
        if st.session_state['resumo_texto']:
            st.markdown(st.session_state['resumo_texto'])

    with aba3:
        p = st.text_input("Dúvida:")
        if st.button("Perguntar"):
            res = model.generate_content([p, docs_ia])
            st.write(res.text)
