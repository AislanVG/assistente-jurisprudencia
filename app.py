import streamlit as st
import uuid
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página e CSS Customizado
# ----------------------------------------------------
st.set_page_config(
    page_title="JusAssist MPMS",
    page_icon="⚖️",
    layout="wide"
)

# Estilização para aumentar fontes, botões e dar o tom sóbrio (Estilo Inner AI / Jus IA)
st.markdown("""
<style>
    /* Estilização dos Botões de Modo */
    div[data-testid="stSidebar"] button[kind="secondary"] {
        border-radius: 8px;
        font-size: 15px !important;
        font-weight: 500;
        padding: 10px 14px;
        text-align: left;
        margin-bottom: 6px;
    }
    
    /* Destaque do Botão Principal (Novo Chat) */
    div[data-testid="stSidebar"] button[kind="primary"] {
        border-radius: 8px;
        font-size: 16px !important;
        font-weight: 600;
        padding: 12px 14px;
        background-color: #3b82f6 !important;
        border: none;
    }
    
    /* Títulos da Barra Lateral */
    .sidebar-section-title {
        font-size: 12px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 18px;
        margin-bottom: 8px;
    }
    
    /* Ajuste do botão de ajuda fixo no rodapé */
    .help-button-container {
        margin-top: 30px;
        padding-top: 15px;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Carregamento da Chave
# ----------------------------------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("⚠️ Chave GEMINI_API_KEY não configurada nos Secrets do Streamlit.")
    st.stop()

# ----------------------------------------------------
# 3. Prompts Especializados
# ----------------------------------------------------
PROMPT_JURISPRUDENCIA = """
Você é um consultor jurídico sênior especializado em pesquisa jurisprudencial analítica brasileira.
Sua missão é realizar buscas amplas no STF, STJ, TJMS e Tribunais Regionais, entregando resultados objetivos e prontos para citação.

ESTRUTURA OBRIGATÓRIA DA RESPOSTA:
### 📌 Tese Jurídica Central
Síntese objetiva da posição predominante e ônus probatório.

### ⚖️ Precedentes Favoráveis
Liste de 2 a 4 julgados específicos com:
* **[Tribunal] – [Classe e Número do Processo]**: Resumo fático conciso demonstrando por que o pedido foi acolhido. [Link/Fonte Oficial]

### 🛑 Precedentes Desfavoráveis ou Distinções (Distinguishing)
Apresente hipóteses em que a tese é rejeitada (ex: ausência de prova pericial, culpa exclusiva).

### 📋 Critérios Objetivos Extraídos dos Julgados
Lista com os requisitos práticos exigidos pelos magistrados.

### 🏛️ Precedentes Vinculantes
Indique Súmulas, Temas Repetitivos (STJ) ou Repercussão Geral (STF), se existentes.

### 📝 Sugestão de Ementa para Cópia
Disponibilize o trecho mais relevante de um acórdão representativo em bloco formatado pronto para citação.
"""

SUPERPROMPT_PARECER = """
Atue como o Assessor Jurídico Sênior da 4ª Procuradoria de Justiça Cível do MPMS, auxiliando diretamente a Procuradora de Justiça, Dra. Luciana Moreira Schenk[cite: 1]. Seu objetivo é elaborar minutas de PARECER DO MINISTÉRIO PÚBLICO EM SEGUNDO GRAU completas, densas e exaustivamente fundamentadas (meta real de 6 a 10 páginas / 2.500 a 4.000 palavras), com tom formal, erudito, sóbrio e cerebral[cite: 1].

### 🛡️ BLINDAGEM E REGRAS ESTRITAS:
1. TRAVA ANTI-ALUCINAÇÃO: Utilize a ferramenta de busca do Google para localizar precedentes, números de REsps, Temas e acórdãos REAIS do STF, STJ e TJMS[cite: 1]. Proibido inventar números ou ementas[cite: 1].
2. TRAVA DE HIERARQUIA: Precedentes das Turmas de Direito Privado do STJ (3ª e 4ª Turmas) e STF PREVALECEM ABSOLUTAMENTE sobre pareceres de Conselhos de Classe (CREMESP/COFFITO), notas do e-NATJus ou resoluções da ANS[cite: 1].
3. DIRETRIZ PROTETIVA: Em saúde, vida e vulneráveis (TEA, paralisia, oncologia, alimentos), a orientação institucional é pela tutela integral da dignidade humana quando amparada por laudo idôneo[cite: 1].
4. RELATÓRIO SUCINTO INSTITUCIONAL: Máximo 500 palavras, fluido em parágrafos encadeados por verbos de ligação ("Alega o apelante que..."), SEM TÓPICOS/BULLETS, finalizando com a fórmula padrão de admissibilidade[cite: 1].
5. ESTILO: Expressões latinas em itálico (*in re ipsa*, *rebus sic stantibus*)[cite: 1]. Jurisprudências citadas em bloco recuado (`>`), em itálico[cite: 1].

### 🔄 FLUXO INTERATIVO AUTOMATIZADO:
Quando o usuário pedir "Analise os autos e gere o parecer" (com arquivo PDF ou texto anexado):

- ETAPA 1 (Diagnóstico & Consulta Ativa de Precedentes):
  Apresente o Raio-X dos autos (Fatos, Preliminares mapeadas, Dispositivos legais)[cite: 1].
  EXECUTE UMA BUSCA NA INTERNET por precedentes recentes do STJ/STF/TJMS aderentes ao caso e APRESENTE[cite: 1]:
  "🔍 Precedentes localizados para o caso: [Liste 2 a 3 acórdãos/Temas reais encontrados com número e tese].
  👉 PERGUNTA OBRIGATÓRIA: Deseja aplicar os precedentes acima sugeridos ou a Procuradoria deseja indicar outro acórdão específico para este parecer?"[cite: 1]
  PARE AQUI e aguarde a confirmação do analista[cite: 1].

- ETAPA 2 (Ementa Técnica e Relatório Institucional):
  Após o "de acordo" do analista, gere a Ementa Técnica Formal e o Relatório Sucinto Fluido (até 500 palavras, sem tópicos)[cite: 1]. PARE AQUI e aguarde validação[cite: 1].

- ETAPA 3 (Minuta Integral de Alta Densidade - 6 a 10 páginas):
  Redija a peça completa: Cabeçalho institucional, Ementa, "COLENDA CÂMARA CÍVEL,", Relatório, I – Da controvérsia recursal (ou Preliminares), II – Do mérito (Fundamentação exaustiva de 2.500 a 4.000 palavras, rebatendo todos os argumentos), III – Conclusão (Opinamento expresso), Datação (Campo Grande/MS) e Assinatura de Luciana Moreira Schenk[cite: 1].
"""

# ----------------------------------------------------
# 4. Gerenciamento de Sessões
# ----------------------------------------------------
if "chats" not in st.session_state:
    primeiro_id = str(uuid.uuid4())
    st.session_state.chats = {
        primeiro_id: {
            "title": "",
            "mode": "📄 Minuta de Parecer (MPMS)",
            "messages": []
        }
    }
    st.session_state.current_chat_id = primeiro_id

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chats:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

chat_atual = st.session_state.chats[st.session_state.current_chat_id]

# ----------------------------------------------------
# 5. Modal de Ajuda
# ----------------------------------------------------
@st.dialog("❓ Central de Ajuda & Guia Operacional", width="large")
def exibir_manual_ajuda():
    st.markdown("### ⚖️ Modos de Atuação do Assistente")
    st.markdown(
        """
| Modo de Trabalho | Objetivo Principal | Como a IA Responde | Entrada da Assessora |
| :--- | :--- | :--- | :--- |
| **📄 Minuta de Parecer (MPMS)** | Elaboração de parecer de 2º Grau (6 a 10 páginas)[cite: 1]. | Lê o PDF, faz o diagnóstico, pesquisa acórdãos reais e gera a peça institucional[cite: 1]. | Anexa o PDF dos autos e digita: *'Analise os autos e gere o parecer'*. |
| **🔍 Pesquisa de Jurisprudência** | Busca de teses, súmulas e julgados do STF, STJ e TJs. | Resumo analítico: Tese Central, Precedentes Favoráveis, Contrapontos e Ementa para Cópia. | Digite livremente a dúvida no chat. |
        """
    )
    st.divider()
    st.markdown("### 💡 Como Operar no Dia a Dia")
    st.markdown("**Para emitir um Parecer do MPMS:**")
    st.markdown("1. Clique no botão **📄 Minuta de Parecer (MPMS)** na barra lateral.")
    st.markdown("2. Anexe a apelação, sentença ou inicial no campo de upload.")
    st.markdown("3. Digite `Analise os autos e gere o parecer` e envie.")
    st.markdown("4. A IA apresentará o raio-x e os acórdãos reais sugeridos[cite: 1]. Responda com `Aprovado` para receber a ementa, o relatório e a minuta completa[cite: 1].")

# ----------------------------------------------------
# 6. Barra Lateral (Layout Sóbrio e Estruturado)
# ----------------------------------------------------
with st.sidebar:
    st.markdown("## ⚖️ **JusAssist MPMS**")
    st.caption("Assessoria Jurídica de Segundo Grau")
    
    # SEÇÃO 1: AÇÃO PRINCIPAL E MODO
    if st.button("➕ Novo Chat", use_container_width=True, type="primary"):
        if len(chat_atual["messages"]) > 0:
            novo_id = str(uuid.uuid4())
            st.session_state.chats[novo_id] = {
                "title": "",
                "mode": chat_atual["mode"],
                "messages": []
            }
            st.session_state.current_chat_id = novo_id
            st.rerun()

    st.markdown('<div class="sidebar-section-title">Modo de Trabalho</div>', unsafe_allow_html=True)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        is_parecer = chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
        btn_parecer_label = "📄 Parecer" if not is_parecer else "🔹 **Parecer**"
        if st.button(btn_parecer_label, key="btn_mode_parecer", use_container_width=True):
            chat_atual["mode"] = "📄 Minuta de Parecer (MPMS)"
            st.rerun()
            
    with col_m2:
        is_juris = chat_atual["mode"] == "🔍 Pesquisa de Jurisprudência"
        btn_juris_label = "🔍 Pesquisa" if not is_juris else "🔹 **Pesquisa**"
        if st.button(btn_juris_label, key="btn_mode_juris", use_container_width=True):
            chat_atual["mode"] = "🔍 Pesquisa de Jurisprudência"
            st.rerun()

    # Upload condicional para o modo parecer
    uploaded_file = None
    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
        st.markdown('<div class="sidebar-section-title">Anexar Processo (PDF)</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload dos autos processuais",
            type=["pdf"],
            help="Inicial, Sentença, Apelação ou Laudos Técnicos",
            label_visibility="collapsed"
        )

    # SEÇÃO 2: HISTÓRICO DE CONVERSAS
    conversas_com_historico = {
        cid: cdata for cid, cdata in st.session_state.chats.items() if len(cdata["messages"]) > 0
    }

    if conversas_com_historico:
        st.markdown('<div class="sidebar-section-title">Histórico Recente</div>', unsafe_allow_html=True)
        for chat_id, chat_data in list(conversas_com_historico.items()):
            icone = "📄" if chat_data.get("mode") == "📄 Minuta de Parecer (MPMS)" else "🔍"
            titulo_exibicao = chat_data["title"] if chat_data["title"] else "Consulta"
            if len(titulo_exibicao) > 22:
                titulo_exibicao = titulo_exibicao[:20] + "..."
            
            is_active = (chat_id == st.session_state.current_chat_id)
            btn_style = f"{icone} {titulo_exibicao}" if not is_active else f"👉 **{titulo_exibicao}**"
            
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(btn_style, key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                if st.button("✕", key=f"del_{chat_id}", help="Excluir"):
                    del st.session_state.chats[chat_id]
                    if st.session_state.current_chat_id == chat_id:
                        restantes = list(st.session_state.chats.keys())
                        if restantes:
                            st.session_state.current_chat_id = restantes[0]
                        else:
                            novo_id = str(uuid.uuid4())
                            st.session_state.chats[novo_id] = {"title": "", "mode": chat_atual["mode"], "messages": []}
                            st.session_state.current_chat_id = novo_id
                    st.rerun()

    # SEÇÃO 3: RODAPÉ / AJUDA
    st.markdown('<div class="help-button-container"></div>', unsafe_allow_html=True)
    if st.button("❓ Ajuda & Guia", use_container_width=True):
        exibir_manual_ajuda()

# ----------------------------------------------------
# 7. Interface Principal de Chat
# ----------------------------------------------------
st.subheader(f"⚖️ {chat_atual['mode']}")
if chat_atual["title"]:
    st.caption(f"Caso em análise: **{chat_atual['title']}**")
else:
    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
        st.caption("Anexe o PDF do processo na barra lateral e digite: 'Analise os autos e gere o parecer'.")
    else:
        st.caption("Pesquise teses, acórdãos e súmulas dos Tribunais Superiores e Estaduais.")

# Exibição do histórico de mensagens
for msg in chat_atual["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Placeholder contextual
placeholder_texto = (
    "Ex.: Analise os autos anexados e gere o parecer..."
    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
    else "Ex.: Qual o entendimento do STJ sobre responsabilidade por erro médico em menor?"
)

if prompt := st.chat_input(placeholder_texto):
    if not chat_atual["title"]:
        chat_atual["title"] = prompt[:35] + ("..." if len(prompt) > 35 else "")

    chat_atual["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processando fundamentação e pesquisando precedentes oficiais..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                instrucao_ativa = (
                    SUPERPROMPT_PARECER
                    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
                    else PROMPT_JURISPRUDENCIA
                )

                conteudos = []
                if uploaded_file is not None and len(chat_atual["messages"]) <= 1:
                    bytes_data = uploaded_file.getvalue()
                    conteudos.append(types.Part.from_bytes(data=bytes_data, mime_type="application/pdf"))
                    conteudos.append(f"[Documento Processual Anexado: {uploaded_file.name}]")

                conteudos.append(prompt)

                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=instrucao_ativa,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1
                    )
                )

                response = chat.send_message(conteudos)
                texto_resposta = response.text

                st.markdown(texto_resposta)
                chat_atual["messages"].append({"role": "assistant", "content": texto_resposta})
                st.rerun()

            except Exception as e:
                st.error(f"Erro no processamento: {str(e)}")
