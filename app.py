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
        
        # URL fixa para não ter erro de busca
        url_planilha = "https://docs.google.com/spreadsheets/d/1tZmD5U2DLXXT1te4R7OLfaQKR78eHhAJmpn2WwnUO70/edit?usp=drivesdk"
        return client.open_by_url(url_planilha)
    except Exception as e:
        st.sidebar.error(f"Erro na conexão com o Sheets: {e}")
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
            st.error("Aba 'Estado_Atual' não encontrada. Verifique o nome na sua planilha.")

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

# --- Inicialização da Memória ---
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
            with st.spinner("Enviando dados para a nuvem..."):
                gc = conectar_planilha()
                if gc:
                    planilha_log = gc.sheet1
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    data_hora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                    planilha_log.append_row([data_hora, disciplina, horas, total_q, acertos, erros])
                    st.success("Progresso salvo com sucesso!")
        else:
            st.warning("Preencha o campo Disciplina.")

    st.divider()
    if st.button("🗑️ Limpar Tudo", use_container_width=True):
        st.session_state['questoes_lista'] = []
        st.session_state['resumo_texto'] = ""
        st.session_state['mostrar_gabarito'] = False
        salvar_estado([], "") 
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
                with st.spinner("A IA está analisando seus materiais..."):
                    prompt = f"""
                    Gere {qtd} questões de múltipla escolha baseadas nos PDFs.
                    Retorne ESTRITAMENTE um array JSON válido. NÃO inclua nenhum texto antes ou depois.
                    Formato: [{{"pergunta": "...", "opcoes": ["A...", "B...", "C...", "D...", "E..."], "correta": "A...", "explica": "..."}}]
                    """
                    
                    try:
                        resp = model.generate_content([prompt] + docs_ia)
                        
                        texto_limpo = resp.text.strip()
                        if texto_limpo.startswith("```json"):
                            texto_limpo = texto_limpo[7:]
                        elif texto_limpo.startswith("```"):
                            texto_limpo = texto_limpo[3:]
                        if texto_limpo.endswith("```"):
                            texto_limpo = texto_limpo[:-3]
                            
                        match = re.search(r'\[.*\]', texto_limpo, re.DOTALL)
                        
                        if match:
                            try:
                                dados = json.loads(match.group())
                                st.session_state['questoes_lista'] = dados
                                salvar_estado(questoes=dados)
                                st.rerun()
                            except json.JSONDecodeError:
                                st.error("⚠️ A IA gerou as questões, mas se atrapalhou na formatação do código. Clique em gerar novamente!")
                        else:
                            st.error("⚠️ A IA não retornou o formato esperado. Tente novamente.")
                            
                    except Exception as e:
                        if "ResourceExhausted" in str(e) or "429" in str(e):
                            st.error("⚠️ Limite de leituras da IA atingido. Espere 1 minutinho e tente novamente.")
                        else:
                            st.error(f"⚠️ Erro ao comunicar com a IA: {e}")

        if st.session_state['questoes_lista']:
            st.info("💡 Estas questões estão sincronizadas com sua planilha.")
            for i, item in enumerate(st.session_state['questoes_lista']):
                st.markdown(f"**{i+1}. {item['pergunta']}**")
                st.radio("Selecione a resposta:", item['opcoes'], key=f"q_{i}", index=None, label_visibility="collapsed")
                st.write("")
            
            if st.button("✅ VERIFICAR RESPOSTAS", use_container_width=True):
                st.session_state['mostrar_gabarito'] = True
            
            if st.session_state['mostrar_gabarito']:
                st.divider()
                for i, item in enumerate(st.session_state['questoes_lista']):
                    escolha = st.session_state.get(f"q_{i}")
                    if escolha == item['correta']:
                        st.success(f"Questão {i+1}: Correta! ✅")
                    else:
                        st.error(f"Questão {i+1}: Errada. Você marcou {escolha}. A correta é {item['correta']}")
                    st.info(f"💡 Explicação: {item['explica']}")

    with aba2:
        if st.button("Gerar ou Atualizar Resumo"):
            with st.spinner("Criando resumo estruturado..."):
                res = model.generate_content(["Faça um resumo detalhado e estruturado destes documentos:", docs_ia])
                st.session_state['resumo_texto'] = res.text
                salvar_estado(resumo=res.text)
        
        if st.session_state['resumo_texto']:
            st.markdown(st.session_state['resumo_texto'])

    with aba3:
        duvida = st.text_input("Digite sua dúvida sobre o conteúdo:")
        if st.button("Enviar Pergunta"):
            if duvida:
                with st.spinner("Consultando materiais..."):
                    res = model.generate_content([duvida, docs_ia])
                    st.write(res.text)
