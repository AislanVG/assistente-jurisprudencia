import streamlit as st
import uuid
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página
# ----------------------------------------------------
st.set_page_config(
    page_title="JusAssist IA",
    page_icon="⚖️",
    layout="wide"
)

# ----------------------------------------------------
# 2. Carregamento da Chave
# ----------------------------------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("⚠️ Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

# ----------------------------------------------------
# 3. Gerenciamento de Múltiplas Sessões/Conversas
# ----------------------------------------------------
# Estrutura: st.session_state.chats = {chat_id: {"title": str, "messages": list}}
if "chats" not in st.session_state:
    primeiro_id = str(uuid.uuid4())
    st.session_state.chats = {
        primeiro_id: {
            "title": "Nova conversa",
            "messages": []
        }
    }
    st.session_state.current_chat_id = primeiro_id

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chats:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

# ----------------------------------------------------
# 4. Barra Lateral (Estilo Jus IA)
# ----------------------------------------------------
with st.sidebar:
    st.title("⚖️ JusAssist IA")
    
    # Botão de Nova Conversa
    if st.button("📝 Nova conversa", use_container_width=True, type="primary"):
        novo_id = str(uuid.uuid4())
        st.session_state.chats[novo_id] = {
            "title": "Nova conversa",
            "messages": []
        }
        st.session_state.current_chat_id = novo_id
        st.rerun()

    st.divider()
    st.caption("ÚLTIMAS CONVERSAS")

    # Lista todas as conversas salvas na sessão
    for chat_id, chat_data in list(st.session_state.chats.items()):
        titulo_exibicao = chat_data["title"]
        if len(titulo_exibicao) > 28:
            titulo_exibicao = titulo_exibicao[:25] + "..."
            
        # Destaque visual para a conversa selecionada
        is_active = (chat_id == st.session_state.current_chat_id)
        btn_label = f"💬 {titulo_exibicao}" if not is_active else f"👉 {titulo_exibicao}"
        
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.button(btn_label, key=f"chat_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            # Botão para excluir conversa específica (se houver mais de uma)
            if len(st.session_state.chats) > 1:
                if st.button("✕", key=f"del_{chat_id}", help="Excluir conversa"):
                    del st.session_state.chats[chat_id]
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    st.rerun()

# ----------------------------------------------------
# 5. Interface Principal de Chat
# ----------------------------------------------------
chat_atual = st.session_state.chats[st.session_state.current_chat_id]

st.header("⚖️ Consulta Jurisprudencial Inteligente")
st.caption(f"Conversa ativa: **{chat_atual['title']}**")

# Exibe as mensagens da conversa ativa
for msg in chat_atual["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada de nova mensagem
if prompt := st.chat_input("Digite o caso fático, tese ou jurisprudência que procura..."):
    # Atualiza o título da conversa com base na primeira pergunta
    if len(chat_atual["messages"]) == 0:
        chat_atual["title"] = prompt[:30] + ("..." if len(prompt) > 30 else "")

    chat_atual["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pesquisando precedentes nos Tribunais Superiores e Regionais..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                instrucoes = (
                    "Você é um consultor jurídico sênior especializado em pesquisa jurisprudencial analítica brasileira.\n\n"
                    "ESTRATÉGIA DE BUSCA AUTÔNOMA:\n"
                    "1. Realize busca ampla e profunda utilizando o Google Search.\n"
                    "2. Se o usuário mencionar um tribunal específico (ex: TJSP, TJRJ, TRF4, STJ, STF), priorize julgados desse órgão.\n"
                    "3. Se não houver tribunal especificado, busque o entendimento nos Tribunais Superiores (STF/STJ) "
                    "e complemente com acórdãos relevantes dos Tribunais de Justiça/TRFs.\n\n"
                    "ESTRUTURA OBRIGATÓRIA DA RESPOSTA:\n"
                    "### 📌 Tese Jurídica Central\n"
                    "Síntese objetiva da posição predominante e ônus probatório.\n\n"
                    "### ⚖️ Precedentes Favoráveis\n"
                    "Liste de 2 a 4 julgados específicos com:\n"
                    "* **[Tribunal] – [Classe e Número do Processo]**: Resumo fático conciso demonstrando por que o pedido foi acolhido. [Link/Fonte Oficial]\n\n"
                    "### 🛑 Precedentes Desfavoráveis ou Distinções (Distinguishing)\n"
                    "Apresente hipóteses em que a tese é rejeitada.\n\n"
                    "### 📋 Critérios Objetivos Extraídos dos Julgados\n"
                    "Lista com os requisitos práticos exigidos pelos magistrados.\n\n"
                    "### 🏛️ Precedentes Vinculantes\n"
                    "Indique Súmulas, Temas Repetitivos (STJ) ou Repercussão Geral (STF), se existentes.\n\n"
                    "### 📝 Sugestão de Ementa para Cópia\n"
                    "Disponibilize o trecho mais relevante de um acórdão representativo em bloco formatado pronto para citação."
                )

                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=instrucoes,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1
                    )
                )

                response = chat.send_message(prompt)
                texto_resposta = response.text

                st.markdown(texto_resposta)
                chat_atual["messages"].append({"role": "assistant", "content": texto_resposta})

            except Exception as e:
                st.error(f"Erro ao processar a pesquisa: {str(e)}")
