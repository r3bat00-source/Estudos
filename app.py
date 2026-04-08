import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. Configurando a página e criando a "Memória Curta"
st.set_page_config(page_title="App de Estudos", layout="wide")

if 'questoes_geradas' not in st.session_state:
    st.session_state['questoes_geradas'] = ""

# 2. Configurando a chave da IA (puxando do Secrets do Streamlit Cloud)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Erro ao conectar com a IA. Verifique se a chave está correta no Secrets.")

# 3. Função para extrair o texto do PDF
def extrair_texto_pdf(arquivo):
    leitor = PdfReader(arquivo)
    texto = ""
    for pagina in leitor.pages:
        conteudo = pagina.extract_text()
        if conteudo:
            texto += conteudo
    return texto

# 4. Interface Principal
st.title("🤖 Sabatina Inteligente com IA")
st.write("Suba seu material em PDF e deixe a IA criar questões exclusivas para você.")

arquivo_pdf = st.file_uploader("Arraste ou selecione seu PDF aqui", type="pdf")

if arquivo_pdf is not None:
    st.success("Arquivo carregado com sucesso!")
    
    # Botão para acionar o Gemini
    if st.button("Gerar Questões com Gabarito"):
        with st.spinner("Lendo o PDF e elaborando as perguntas..."):
            texto_extraido = extrair_texto_pdf(arquivo_pdf)
            
            # Limitamos o tamanho do texto enviado para a IA não travar
            texto_limite = texto_extraido[:15000] 
            
            # O comando (prompt) para a IA agir como professor
            prompt = f"""
            Você é um professor especialista em preparação para provas.
            Com base no texto abaixo, crie 3 questões de múltipla escolha (nível médio/difícil).
            Cada questão deve ter 5 alternativas (A, B, C, D, E).
            Apresente o gabarito comentado apenas no final de todas as questões.
            
            Texto base:
            {texto_limite}
            """
            
            # Chamando a IA e salvando o resultado na memória do site
            resposta = model.generate_content(prompt)
            st.session_state['questoes_geradas'] = resposta.text

# 5. Exibindo as questões na tela
# Como está salvo no session_state, não vai sumir se você clicar em outra coisa
if st.session_state['questoes_geradas']:
    st.markdown("---")
    st.markdown("### 📝 Suas Questões:")
    st.write(st.session_state['questoes_geradas'])
    
    # Botão extra para limpar a tela quando quiser subir outro PDF
    if st.button("Limpar Questões"):
        st.session_state['questoes_geradas'] = ""
        st.rerun()
