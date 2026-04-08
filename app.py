# --- Na parte da interface principal ---

# 1. Mudança no uploader para aceitar vários arquivos
arquivos_pdf = st.file_uploader(
    "Suba seus materiais de estudo (você pode selecionar vários)", 
    type="pdf", 
    accept_multiple_files=True  # Esta é a chave para múltiplos arquivos
)

if arquivos_pdf: # Verifica se a lista não está vazia
    st.success(f"{len(arquivos_pdf)} arquivo(s) carregado(s) com sucesso!")
    
    # 2. Preparando a lista de documentos para enviar de uma vez só
    documentos_para_ia = []
    for pdf in arquivos_pdf:
        pdf_bytes = pdf.getvalue()
        documentos_para_ia.append({
            "mime_type": "application/pdf",
            "data": pdf_bytes
        })
    
    # --- Abas (Tabs) ---
    tab1, tab2, tab3 = st.tabs(["📝 Gerar Questões", "📑 Fazer Resumo", "💬 Tirar Dúvidas"])
    
    with tab1:
        if st.button("Gerar Questões do Combo de PDFs"):
            with st.spinner("Analisando todos os documentos..."):
                prompt_questoes = """
                Você é um professor especialista. Analise todos os documentos anexados.
                Crie 5 questões de múltipla escolha que cubram os pontos principais de TODOS os arquivos.
                Apresente o gabarito comentado no final.
                """
                # Enviamos a lista completa (prompt + todos os PDFs)
                conteudo_envio = [prompt_questoes] + documentos_para_ia
                resposta = model.generate_content(conteudo_envio)
                st.session_state['respostas_ia']['questoes'] = resposta.text
        
        if st.session_state['respostas_ia']['questoes']:
            st.markdown("---")
            st.write(st.session_state['respostas_ia']['questoes'])

    with tab2:
        if st.button("Criar Resumo Integrado"):
            with st.spinner("Sintetizando os materiais..."):
                prompt_resumo = "Faça um resumo comparativo e estruturado de todos os PDFs anexados, conectando os temas entre eles."
                conteudo_envio = [prompt_resumo] + documentos_para_ia
                resposta = model.generate_content(conteudo_envio)
                st.session_state['respostas_ia']['resumo'] = resposta.text
        
        if st.session_state['respostas_ia']['resumo']:
            st.markdown("---")
            st.write(st.session_state['respostas_ia']['resumo'])

    with tab3:
        st.write("Sua pergunta será respondida com base em todos os PDFs carregados.")
        duvida_usuario = st.text_input("Sua dúvida:")
        
        if st.button("Enviar Pergunta"):
            if duvida_usuario:
                with st.spinner("Buscando a resposta nos materiais..."):
                    prompt_duvida = f"Com base nos documentos em anexo, responda: {duvida_usuario}"
                    conteudo_envio = [prompt_duvida] + documentos_para_ia
                    resposta = model.generate_content(conteudo_envio)
                    st.session_state['respostas_ia']['pergunta'] = resposta.text
            else:
                st.warning("Digite sua pergunta.")

        if st.session_state['respostas_ia']['pergunta']:
            st.markdown("---")
            st.write(st.session_state['respostas_ia']['pergunta'])
