import streamlit as st
import google.generativeai as genai

# 1. Configurando a página
st.set_page_config(page_title="Dashboard de Estudos", layout="wide")

# 2. Configurando a chave da IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("Erro ao conectar com a IA. Verifique os Secrets.")

# ==========================================
# BARRA LATERAL (Registro de Estudos)
# ==========================================
with st.sidebar:
    st.title("📊 Registro de Estudos")
    st.markdown("Preencha seu progresso diário:")
    
    disciplina = st.text_input("Disciplina:")
    horas = st.number_input("Horas Estudadas:", min_value=0.0, step=0.5)
    
    st.markdown("### Desempenho em Questões")
    questoes_feitas = st.number_input("Total de Questões:", min_value=0)
    acertos = st.number_input("Acertos:", min_value=0)
    erros = st.number_input("Erros:", min_value=0)
    
    if st.button("Salvar Registro"):
        st.success(f"Registro de {disciplina} salvo na sessão!")
        # No futuro, podemos conectar este botão a uma planilha do Google

# ==========================================
# ÁREA PRINCIPAL (IA e PDFs)
# ==========================================
st.title("🤖 Tutor Inteligente de PDFs")

arquivo_pdf = st.file_uploader("Suba seu material em PDF aqui", type="pdf")

if arquivo_pdf is not None:
    st.success("Arquivo carregado com sucesso!")
    
    # Preparando o arquivo para a IA
    pdf_bytes = arquivo_pdf.getvalue()
    documento_pdf = {
        "mime_type": "application/pdf",
        "data": pdf_bytes
    }
    
    # Criando as Abas para organizar as funções
    aba_questoes, aba_resumo, aba_duvidas = st.tabs([
        "📝 Gerar Questões", 
        "📑 Fazer Resumo", 
        "💬 Tirar Dúvidas"
    ])
    
    # --- ABA 1: QUESTÕES ---
    with aba_questoes:
        st.markdown("### Treinamento Prático")
        if st.button("Gerar Questões com Gabarito", key="btn_questoes"):
            with st.spinner("Analisando o documento..."):
                prompt_questoes = """
                Você é um professor especialista. Com base EXCLUSIVAMENTE no documento anexo, 
                crie 3 questões de múltipla escolha com 5 alternativas cada. 
                Apresente o gabarito comentado no final.
                """
                resposta = model.generate_content([prompt_questoes, documento_pdf])
                st.write(resposta.text)

    # --- ABA 2: RESUMO ---
    with aba_resumo:
        st.markdown("### Síntese do Material")
        if st.button("Criar Resumo Estruturado", key="btn_resumo"):
            with st.spinner("Sintetizando os pontos principais..."):
                prompt_resumo = """
                Faça um resumo estruturado deste documento. 
                Destaque os conceitos principais, fórmulas importantes (se houver) 
                e crie tópicos que facilitem a revisão rápida para uma prova.
                """
                resposta = model.generate_content([prompt_resumo, documento_pdf])
                st.write(resposta.text)

    # --- ABA 3: TIRAR DÚVIDAS ---
    with aba_duvidas:
        st.markdown("### Pergunte ao Professor")
        pergunta_usuario = st.text_input("Qual a sua dúvida específica sobre este material?")
        
        if st.button("Enviar Pergunta", key="btn_duvida"):
            if pergunta_usuario:
                with st.spinner("Buscando a resposta no material..."):
                    prompt_duvida = f"""
                    O usuário tem a seguinte dúvida sobre o documento em anexo: "{pergunta_usuario}".
                    Responda de forma clara e didática, baseando-se nas informações do PDF. 
                    Se a resposta não estiver no documento, avise o usuário.
                    """
                    resposta = model.generate_content([prompt_duvida, documento_pdf])
                    st.write(resposta.text)
            else:
                st.warning("Por favor, digite uma pergunta antes de enviar.")
