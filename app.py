import streamlit as st
import google.generativeai as genai
import json # Biblioteca nova para ler as alternativas separadas

# 1. Configuração Inicial e Memória
st.set_page_config(page_title="Dashboard de Estudos Pro", layout="wide")

if 'respostas_ia' not in st.session_state:
    st.session_state['respostas_ia'] = {"questoes_json": "", "resumo": "", "pergunta": ""}
if 'mostrar_gabarito' not in st.session_state:
    st.session_state['mostrar_gabarito'] = False

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
st.info("Faça o upload dos PDFs e teste seus conhecimentos no modo Simulado Interativo.")

# Upload de múltiplos arquivos
arquivos_pdf = st.file_uploader(
    "Selecione seus PDFs de estudo:", 
    type="pdf", 
    accept_multiple_files=True
)

if arquivos_pdf:
    docs_ia = []
    for pdf in arquivos_pdf:
        docs_ia.append({
            "mime_type": "application/pdf",
            "data": pdf.getvalue()
        })
    
    # Abas de Funcionalidades
    t_quest, t_resumo, t_duvida = st.tabs(["📝 Simulado Interativo", "📑 Resumo Integrado", "💬 Chat com PDF"])
    
    # --- ABA 1: SIMULADO INTERATIVO ---
    with t_quest:
        if st.button("Gerar Simulado"):
            # Reseta o gabarito caso você gere um simulado novo
            st.session_state['mostrar_gabarito'] = False 
            
            with st.spinner("Elaborando as questões..."):
                # Pedimos para a IA retornar no formato JSON para criarmos os botões
                prompt = """
                Gere 3 questões de múltipla escolha baseadas nestes documentos.
                Você DEVE retornar APENAS um array JSON válido, sem texto extra, seguindo EXATAMENTE esta estrutura:
                [
                  {
                    "questao": "Texto da pergunta",
                    "opcoes": ["A) opcao 1", "B) opcao 2", "C) opcao 3", "D) opcao 4", "E) opcao 5"],
                    "resposta_correta": "A) opcao 1",
                    "comentario": "Explicação detalhada do gabarito"
                  }
                ]
                """
                resp = model.generate_content([prompt] + docs_ia)
                st.session_state['respostas_ia']['questoes_json'] = resp.text

        # Lógica para desenhar as questões na tela com as caixinhas
        if st.session_state['respostas_ia']['questoes_json']:
            st.markdown("---")
            try:
                # Limpa o texto caso a IA mande com formatação Markdown
                texto_ia = st.session_state['respostas_ia']['questoes_json']
                texto_limpo = texto_ia.replace("```json", "").replace("```", "").strip()
                lista_questoes = json.loads(texto_limpo)
                
                # Guarda o que você marcar
                respostas_marcadas = []
                
                # Desenha cada pergunta com suas opções
                for i, q in enumerate(lista_questoes):
                    st.markdown(f"**{i+1}. {q['questao']}**")
                    # Cria as caixinhas para você escolher (radio buttons)
                    escolha = st.radio("Escolha uma alternativa:", q['opcoes'], key=f"radio_{i}", index=None)
                    respostas_marcadas.append(escolha)
                    st.write("") # Dá um espaço
                
                # O botão mágico de verificar
                if st.button("Verificar Respostas", type="primary"):
                    st.session_state['mostrar_gabarito'] = True
                
                # O que acontece APÓS clicar em Verificar Respostas
                if st.session_state['mostrar_gabarito']:
                    st.markdown("---")
                    st.subheader("🎯 Gabarito Comentado")
                    
                    acertos_simulado = 0
                    for i, q in enumerate(lista_questoes):
                        st.markdown(f"**Questão {i+1}**")
                        
                        if respostas_marcadas[i]:
                            # Compara se a alternativa que você marcou é igual a correta
                            if respostas_marcadas[i] == q['resposta_correta']:
                                st.success(f"Você marcou: {respostas_marcadas[i]} ✅ ACERTOU!")
                                acertos_simulado += 1
                            else:
                                st.error(f"Você marcou: {respostas_marcadas[i]} ❌ ERROU.")
                                st.info(f"Resposta Correta: {q['resposta_correta']}")
                        else:
                            st.warning("⚠️ Você deixou esta em branco.")
                            st.info(f"Resposta Correta: {q['resposta_correta']}")
                        
                        # Mostra a explicação do professor
                        st.write(f"**Comentário:** {q['comentario']}")
                        st.write("")
                    
                    st.markdown(f"### 🏆 Seu resultado: {acertos_simulado} de {len(lista_questoes)}")

            except Exception as e:
                st.error("Ops! A IA não gerou as questões no formato perfeito dessa vez. Clique em Gerar Simulado novamente.")

    # --- ABA 2: RESUMO (MANTIDA IGUAL) ---
    with t_resumo:
        if st.button("Gerar Resumo dos Materiais"):
            with st.spinner("Sintetizando os arquivos..."):
                prompt = "Crie um resumo único e conectado que englobe os pontos principais de todos os PDFs fornecidos."
                resp = model.generate_content([prompt] + docs_ia)
                st.session_state['respostas_ia']['resumo'] = resp.text
        if st.session_state['respostas_ia']['resumo']:
            st.write(st.session_state['respostas_ia']['resumo'])

    # --- ABA 3: CHAT (MANTIDA IGUAL) ---
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
