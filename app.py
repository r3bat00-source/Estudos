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
        cred_dict = dict(st.secrets["gcp_service_account"])
        escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(cred_dict, scopes=escopos)
        client = gspread.authorize(creds)
        url_planilha = "https://docs.google.com/spreadsheets/d/1tZmD5U2DLXXT1te4R7OLfaQKR78eHhAJmpn2WwnUO70/edit?usp=drivesdk"
        return client.open_by_url(url_planilha)
    except Exception as e:
        st.sidebar.error(f"Erro na conexão com o Sheets: {e}")
        return None

def salvar_estado(questoes=None, resumo=None, revisar=None):
    gc = conectar_planilha()
    if gc:
        try:
            aba_estado = gc.worksheet("Estado_Atual")
            if questoes is not None:
                aba_estado.update_acell('A1', json.dumps(questoes))
            if resumo is not None:
                aba_estado.update_acell('B1', resumo)
            if revisar is not None:
                aba_estado.update_acell('C1', json.dumps(revisar))
        except:
            st.error("Aba 'Estado_Atual' não encontrada.")

def carregar_estado():
    gc = conectar_planilha()
    if gc:
        try:
            aba_estado = gc.worksheet("Estado_Atual")
            q_raw = aba_estado.acell('A1').value
            r_raw = aba_estado.acell('B1').value
            rev_raw = aba_estado.acell('C1').value
            
            return (json.loads(q_raw) if q_raw else [], 
                    r_raw if r_raw else "", 
                    json.loads(rev_raw) if rev_raw else [])
        except:
            return [], "", []
    return [], "", []

# --- Inicialização da Memória ---
if 'questoes_lista' not in st.session_state:
    q, r, rev = carregar_estado()
    st.session_state['questoes_lista'] = q
    st.session_state['resumo_texto'] = r
    st.session_state['revisar_lista'] = rev

if 'mostrar_gabarito' not in st.session_state:
    st.session_state['mostrar_gabarito'] = False

# ==========================================
# 📊 BARRA LATERAL
# ==========================================
with st.sidebar:
    st.title("🎯 Painel de Controle")
    disciplina = st.text_input("Matéria:")
    horas = st.number_input("Horas de Foco:", min_value=0.0, step=0.5)
    
    # NOVO: Aba de Assuntos para Revisar
    with st.expander("📚 Assuntos para Revisar", expanded=True):
        if st.session_state['revisar_lista']:
            for assunto in st.session_state['revisar_lista']:
                st.write(f"• {assunto}")
            if st.button("Clear Review List"):
                st.session_state['revisar_lista'] = []
                salvar_estado(revisar=[])
                st.rerun()
        else:
            st.write("Nenhum tópico pendente. Bom trabalho!")

    st.divider()
    st.subheader("Registro de Sessão")
    total_q = st.number_input("Total Questões:", min_value=0)
    col_a, col_e = st.columns(2)
    with col_a:
        acertos = st.number_input("Acertos:", min_value=0)
    with col_e:
        erros = st.number_input("Erros:", min_value=0)
    
    if st.button("☁️ Salvar Registro Final", use_container_width=True):
        if disciplina:
            gc = conectar_planilha()
            if gc:
                planilha_log = gc.sheet1
                fuso_br = pytz.timezone('America/Sao_Paulo')
                data_hora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                planilha_log.append_row([data_hora, disciplina, horas, total_q, acertos, erros])
                st.success("Salvo!")
        else:
            st.warning("Preencha a Disciplina.")

    if st.button("🗑️ Limpar Tudo", use_container_width=True):
        st.session_state['questoes_lista'] = []
        st.session_state['resumo_texto'] = ""
        st.session_state['revisar_lista'] = []
        salvar_estado([], "", [])
        st.rerun()

# ==========================================
# 🚀 ÁREA PRINCIPAL
# ==========================================
st.title("📚 Sistema de Estudos Profissional")

arquivos = st.file_uploader("Suba seus materiais em PDF", type="pdf", accept_multiple_files=True)

if arquivos:
    docs_ia = [{"mime_type": "application/pdf", "data": f.getvalue()} for f in arquivos]
    aba1, aba2, aba3 = st.tabs(["📝 Simulado", "📑 Resumo", "💬 Chat"])

    with aba1:
        col1, col2 = st.columns([1, 2])
        with col1:
            qtd = st.number_input("Quantas questões?", min_value=1, max_value=15, value=3)
        with col2:
            st.write("")
            st.write("")
            if st.button("🚀 GERAR NOVO SIMULADO", type="primary", use_container_width=True):
                st.session_state['mostrar_gabarito'] = False
                with st.spinner("Analisando conteúdos..."):
                    prompt = f"""
                    Gere {qtd} questões de múltipla escolha baseadas nos PDFs.
                    Retorne ESTRITAMENTE um array JSON. 
                    FORMATO: [{{"topico": "Assunto curto", "pergunta": "...", "opcoes": ["A...", "B...", "C...", "D...", "E..."], "correta": "Letra e texto", "explica": "..."}}]
                    """
                    try:
                        resp = model.generate_content([prompt] + docs_ia)
                        match = re.search(r'\[.*\]', resp.text, re.DOTALL)
                        if match:
                            dados = json.loads(match.group())
                            st.session_state['questoes_lista'] = dados
                            salvar_estado(questoes=dados)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao gerar: {e}")

        if st.session_state['questoes_lista']:
            for i, item in enumerate(st.session_state['questoes_lista']):
                st.markdown(f"**{i+1}. [{item.get('topico', 'Geral')}]** {item['pergunta']}")
                st.radio("Escolha:", item['opcoes'], key=f"q_{i}", index=None, label_visibility="collapsed")
            
            if st.button("✅ VERIFICAR RESPOSTAS", use_container_width=True):
                st.session_state['mostrar_gabarito'] = True

            if st.session_state['mostrar_gabarito']:
                st.divider()
                novos_erros = list(st.session_state['revisar_lista'])
                
                for i, item in enumerate(st.session_state['questoes_lista']):
                    escolha = st.session_state.get(f"q_{i}")
                    if not escolha:
                        st.warning(f"Q{i+1}: Sem resposta.")
                        continue
                    
                    # Lógica de comparação blindada (apenas primeira letra)
                    letra_user = escolha[0].upper()
                    letra_correta = item['correta'][0].upper()
                    
                    if letra_user == letra_correta:
                        st.success(f"Questão {i+1}: Correta! ✅")
                    else:
                        st.error(f"Questão {i+1}: Errada. Marcou {letra_user}, era {letra_correta}")
                        # Adiciona o tópico aos erros para revisão se já não estiver lá
                        topico = item.get('topico', 'Assunto Geral')
                        if topico not in novos_erros:
                            novos_erros.append(topico)
                
                # Salva a nova lista de revisão na memória e no Sheets
                st.session_state['revisar_lista'] = novos_erros
                salvar_estado(revisar=novos_erros)
                st.info("💡 Tópicos de questões erradas foram adicionados à sua lista de revisão na barra lateral.")

    with aba2:
        if st.button("Gerar Resumo"):
            res = model.generate_content(["Resuma estes documentos:", docs_ia])
            st.session_state['resumo_texto'] = res.text
            salvar_estado(resumo=res.text)
        if st.session_state['resumo_texto']:
            st.markdown(st.session_state['resumo_texto'])

    with aba3:
        p = st.text_input("Dúvida:")
        if st.button("Perguntar"):
            res = model.generate_content([p, docs_ia])
            st.write(res.text)
