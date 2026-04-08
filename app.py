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

# 2. Configurações de API e "Radar de Modelos"
modelo_ativo = "Buscando..."
lista_modelos = []

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Rastreia todos os modelos que a sua chave tem acesso real
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            lista_modelos.append(m.name.replace("models/", ""))
            
    # MUDANÇA AQUI: Prioridade TOTAL para o 1.5-flash (O Trator da cota gratuita)
    opcoes_ideais = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    modelo_escolhido = None
    
    for ideal in opcoes_ideais:
        if ideal in lista_modelos:
            modelo_escolhido = ideal
            break
            
    if not modelo_escolhido and lista_modelos:
        modelo_escolhido = lista_modelos[0]
        
    if modelo_escolhido:
        model = genai.GenerativeModel(modelo_escolhido)
        modelo_ativo = modelo_escolhido
    else:
        modelo_ativo = "Erro: Nenhum modelo encontrado para esta chave."

except Exception as e:
    st.error(f"Erro na conexão com a IA: {e}")

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

def obter_aba_estado(gc):
    titulos_abas = [aba.title for aba in gc.worksheets()]
    if "Estado_Atual" not in titulos_abas:
        return gc.add_worksheet(title="Estado_Atual", rows="10", cols="10")
    return gc.worksheet("Estado_Atual")

def salvar_estado(questoes=None, resumo=None, revisar=None):
    gc = conectar_planilha()
    if gc:
        try:
            aba_estado = obter_aba_estado(gc)
            if questoes is not None:
                aba_estado.update_acell('A1', json.dumps(questoes))
            if resumo is not None:
                aba_estado.update_acell('B1', resumo)
            if revisar is not None:
                aba_estado.update_acell('C1', json.dumps(revisar))
        except Exception as e:
            st.error(f"Erro ao salvar estado: {e}")

def carregar_estado():
    gc = conectar_planilha()
    if gc:
        try:
            aba_estado = obter_aba_estado(gc)
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
    
    with st.expander("📚 Assuntos para Revisar", expanded=True):
        if st.session_state['revisar_lista']:
            for assunto in st.session_state['revisar_lista']:
                st.write(f"• {assunto}")
            if st.button("Limpar Lista de Revisão"):
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
            st.warning("Preencha a Disciplina antes de salvar.")

    if st.button("🗑️ Limpar Tudo do App", use_container_width=True):
        st.session_state['questoes_lista'] = []
        st.session_state['resumo_texto'] = ""
        st.session_state['revisar_lista'] = []
        st.session_state['mostrar_gabarito'] = False
        salvar_estado([], "", [])
        st.rerun()

    st.divider()
    st.subheader("🛠️ Diagnóstico da IA")
    st.caption(f"**Motor Escolhido:** {modelo_ativo}")

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
                    Retorne ESTRITAMENTE um array JSON. NÃO inclua a formatação ```json.
                    FORMATO: [{{"topico": "Assunto curto", "pergunta": "...", "opcoes": ["A) ...", "B) ...", "C) ...", "D) ...", "E) ..."], "correta": "A", "explica": "Explique detalhadamente POR QUE a opção correta está certa e POR QUE as outras alternativas estão erradas."}}]
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
                                st.error("⚠️ A IA se atrapalhou no formato. Tente gerar novamente!")
                        else:
                            st.error("⚠️ Formato inesperado. Tente gerar novamente.")
                    except Exception as e:
                        # Filtro Anti-Tela Vermelha para limites de leitura
                        if "429" in str(e) or "ResourceExhausted" in str(e):
                            st.warning("⏳ Limite rápido de leituras atingido (ou seu PDF é muito grande). Aguarde 1 minutinho e tente gerar novamente!")
                        else:
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
                        st.warning(f"Questão {i+1}: Sem resposta.")
                        st.info(f"💡 **Explicação:** {item.get('explica', 'Sem explicação.')}")
                        st.write("")
                        continue
                    
                    letra_user = escolha[0].upper()
                    letra_correta = item['correta'][0].upper()
                    
                    if letra_user == letra_correta:
                        st.success(f"Questão {i+1}: Correta! ✅ Você marcou {letra_user}.")
                    else:
                        st.error(f"Questão {i+1}: Errada. Você marcou {letra_user}, mas a correta é {letra_correta}.")
                        topico = item.get('topico', 'Assunto Geral')
                        if topico not in novos_erros:
                            novos_erros.append(topico)
                    
                    st.info(f"💡 **Por que essa é a resposta?**\n\n{item.get('explica', 'Sem explicação.')}")
                    st.write("")
                
                st.session_state['revisar_lista'] = novos_erros
                salvar_estado(revisar=novos_erros)
                st.caption("Verifique a barra lateral para ver os tópicos adicionados à sua lista de revisão.")

    with aba2:
        if st.button("Gerar Resumo"):
            with st.spinner("Escrevendo..."):
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
