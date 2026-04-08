import streamlit as st
import google.generativeai as genai

# 1. Configurando a página e a memória
st.set_page_config(page_title="App de Estudos", layout="wide")

if 'questoes_geradas' not in st.session_state:
    st.session_state['questoes_geradas'] = ""

# 2. Configurando a chave da IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("Erro ao conectar com a IA. Verifique se a chave está correta no Secrets.")

# 3. Interface Principal
st.title("🤖 Sabatina com IA (Visão de Raio-X)")
st.write("Suba seu PDF de Cálculo ou Exatas. A IA agora consegue ler fórmulas matemáticas e gráficos perfeitamente!")

arquivo_pdf = st.file_uploader("Arraste ou selecione seu PDF aqui", type="pdf")

if arquivo_pdf is not None:
    st.success("Arquivo carregado com sucesso!")
    
    if st.button("Gerar Questões com Gabarito"):
        with st.spinner("Analisando fórmulas e textos do seu material..."):
            
            # Lendo o arquivo original em formato bruto (bytes)
            pdf_bytes = arquivo_pdf.getvalue()
            
            # Empacotando o arquivo do jeito que o Gemini exige
            documento_pdf = {
                "mime_type": "application/pdf",
                "data": pdf_bytes
            }
            
            # O comando (prompt)
            prompt = """
            Você é um professor especialista em preparação para provas e concursos.
            Analise o documento em anexo (ele contém fórmulas matemáticas e cálculos).
            Com base EXCLUSIVAMENTE neste documento, crie 3 questões de múltipla escolha.
            Cada questão deve ter 5 alternativas (A, B, C, D, E).
            Apresente o gabarito comentado, explicando a resolução passo a passo, apenas no final.
            """
            
            # Enviando o prompt E o documento juntos para a IA
            resposta = model.generate_content([prompt, documento_pdf])
            st.session_state['questoes_geradas'] = resposta.text

# 4. Exibindo as questões na tela
if st.session_state['questoes_geradas']:
    st.markdown("---")
    st.markdown("### 📝 Suas Questões:")
    st.write(st.session_state['questoes_geradas'])
    
    if st.button("Limpar Questões"):
        st.session_state['questoes_geradas'] = ""
        st.rerun()
