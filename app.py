import streamlit as st
import uuid
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página e CSS Institucional
# ----------------------------------------------------
st.set_page_config(
    page_title="JusAssist MPMS",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Botões Primários (Azul Marinho Institucional) */
    div[data-testid="stSidebar"] button[kind="primary"],
    div.stButton > button[kind="primary"] {
        border-radius: 8px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        background-color: #1e3a8a !important;
        border: 1px solid #1e3a8a !important;
        color: #ffffff !important;
    }
    div[data-testid="stSidebar"] button[kind="primary"]:hover,
    div.stButton > button[kind="primary"]:hover {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
    }

    /* Botões Secundários */
    div[data-testid="stSidebar"] button[kind="secondary"],
    div.stButton > button[kind="secondary"] {
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
    }
    div[data-testid="stSidebar"] button[kind="secondary"]:hover,
    div.stButton > button[kind="secondary"]:hover {
        border-color: #94a3b8 !important;
        background-color: #f8fafc !important;
    }

    .sidebar-label {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-top: 18px;
        margin-bottom: 6px;
    }

    .help-section {
        margin-top: 25px;
        padding-top: 15px;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Carregamento Seguro de Chaves (Secrets)
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
Apresente hipóteses em que a tese é rejeitada.

### 📋 Critérios Objetivos Extraídos dos Julgados
Lista com os requisitos práticos exigidos pelos magistrados.

### 🏛️ Precedentes Vinculantes
Indique Súmulas, Temas Repetitivos (STJ) ou Repercussão Geral (STF), se existentes.

### 📝 Sugestão de Ementa para Cópia
Disponibilize o trecho mais relevante de um acórdão representativo em bloco formatado pronto para citação.
"""

SUPERPROMPT_PARECER = """
Atue como o Assessor Jurídico Sênior da 4ª Procuradoria de Justiça Cível do MPMS, auxiliando diretamente a Procuradora de Justiça, Dra. Luciana Moreira Schenk. Seu objetivo é elaborar minutas de PARECER DO MINISTÉRIO PÚBLICO EM SEGUNDO GRAU completas, densas e exaustivamente fundamentadas (meta real de 6 a 10 páginas / 2.500 a 4.000 palavras), com tom formal, erudito, sóbrio e cerebral.

### 🛡️ BLINDAGEM E REGRAS ESTRITAS:
1. ADERÊNCIA ESTRITA AOS AUTOS: Baseie sua análise EXCLUSIVAMENTE nos fatos e documentos do caso concreto anexado pelo usuário. É PROIBIDO inventar ou misturar matérias fáticas estranhas ao processo (ex: não cite saúde se o caso for imobiliário/tributário).
2. TRAVA ANTI-ALUCINAÇÃO: Utilize a ferramenta de busca do Google para localizar precedentes, números de REsps, Temas e acórdãos REAIS do STF, STJ e TJMS aplicáveis à matéria específica dos autos[cite: 1]. Proibido inventar números ou ementas[cite: 1].
3. TRAVA DE HIERARQUIA: Precedentes das Turmas do STJ e teses vinculantes do STF prevalecem sobre atos administrativos ou pareceres técnicos[cite: 1].
4. RELATÓRIO SUCINTO INSTITUCIONAL: Máximo 500 palavras, fluido em parágrafos encadeados por verbos de ligação ("Alega o apelante que..."), SEM TÓPICOS/BULLETS, finalizando com a fórmula padrão de admissibilidade[cite: 1].
5. ESTILO: Expressões latinas em itálico (*in re ipsa*, *tempus regit actum*)[cite: 1]. Jurisprudências citadas em bloco recuado (`>`), em itálico[cite: 1].

### 🔄 FLUXO PROGRESSIVO OBRIGATÓRIO EM 3 ETAPAS:

- ETAPA 1 (Diagnóstico & Consulta de Precedentes):
  Apresente o Raio-X dos autos (Fatos reais do processo, Preliminares mapeadas, Dispositivos legais)[cite: 1].
  Faça uma busca na internet pelos precedentes reais mais recentes do STJ/STF/TJMS sobre a matéria e apresente-os[cite: 1].
  Ao final, faça a PERGUNTA OBRIGATÓRIA: "Deseja aplicar os precedentes acima sugeridos ou indicar outro julgado específico?" e PARE AQUI[cite: 1].

- ETAPA 2 (Ementa Técnica e Relatório Institucional):
  Quando o analista aprovar ou orientar a tese, elabore a Ementa Técnica Formal (com as palavras-chave da matéria dos autos e opinião final) e o Relatório Sucinto Fluido (máximo 500 palavras, corrido)[cite: 1].
  Ao final, diga: "Aguardando validação da Ementa e Relatório para gerar a Minuta Integral (Etapa 3)." e PARE AQUI[cite: 1].

- ETAPA 3 (Minuta Integral de Alta Densidade - Peça Completa):
  Quando o analista responder "validado", "aprovado" ou "prossiga", REDIJA IMEDIATAMENTE A PEÇA COMPLETA DE SEGUNDO GRAU, sem cortes e sem placeholders[cite: 1]:
  Cabeçalho Oficial (Autos, Classe, Órgão Julgador, Relator, Partes), Ementa Formal, "COLENDA CÂMARA CÍVEL,", Relatório, I – Das Preliminares (se houver), II – Do Mérito (Fundamentação exaustiva e densa de 2.500 a 4.000 palavras, enfrentando todas as teses dos autos com doutrina e precedentes), III – Conclusão (Opinamento formal), Datação (Campo Grande/MS) e Assinatura institucional de Luciana Moreira Schenk[cite: 1]. NÃO REINICIE O FLUXO[cite: 1].
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
            "messages": [],
            "gemini_history": [] # Histórico estruturado para a API
        }
    }
    st.session_state.current_chat_id = primeiro_id

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chats:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

chat_atual = st.session_state.chats[st.session_state.current_chat_id]

# ----------------------------------------------------
# 5. Modal Completo de Ajuda
# ----------------------------------------------------
@st.dialog("📖 Central de Ajuda & Manual Operacional (MPMS)", width="large")
def exibir_manual_ajuda():
    st.markdown("## ⚖️ Manual Operacional: JusAssist MPMS")
    st.caption("Guia Prático para Pesquisa Jurisprudencial e Emissão de Pareceres de 2º Grau")
    
    tab1, tab2, tab3 = st.tabs(["📄 Minuta de Parecer", "🔍 Pesquisa Jurisprudencial", "🛡️ Diretrizes MPMS"])
    
    with tab1:
        st.markdown(
            """
### 🏛️ Fluxo em 3 Etapas Integradas:[cite: 1]
1. **Etapa 1 (Upload & Raio-X):** Anexe os PDFs dos autos e clique em `⚡ Iniciar Análise do Processo`[cite: 1]. A IA lerá as peças e apresentará o diagnóstico com os precedentes reais sugeridos[cite: 1].
2. **Etapa 2 (Ementa & Relatório):** Digite `Aprovado` (ou indique uma diretriz específica)[cite: 1]. A IA gerará a Ementa Técnica e o Relatório Fluido de até 500 palavras[cite: 1].
3. **Etapa 3 (Minuta Completa):** Digite `Validado, gere a minuta`[cite: 1]. A IA redigirá o parecer integral de alta densidade (6 a 10 páginas / 2.500 a 4.000 palavras) pronto para cópia e colagem no Word[cite: 1].
            """
        )

    with tab2:
        st.markdown("### 🔍 Pesquisa de Jurisprudência:")
        st.markdown("Digite qualquer tese jurídica no chat para receber precedentes favoráveis, desfavoráveis, súmulas e sugestão de ementa.")
        st.code("Pesquise precedentes do STJ sobre tempus regit actum e indisponibilidade CNIB em escritura de 2010.", language="text")

    with tab3:
        st.markdown(
            """
* **Prevalência STJ/STF:** Precedentes superiores sobrepõem-se a normas administrativas[cite: 1].
* **Aderência aos Autos:** Cada parecer respeita estritamente a matéria e os fatos do processo analisado[cite: 1].
            """
        )

# ----------------------------------------------------
# 6. Barra Lateral
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### ⚖️ **JusAssist MPMS**")
    st.caption("4ª Procuradoria de Justiça Cível")
    
    # Ação Primária
    if st.button("➕ Novo Atendimento", use_container_width=True, type="primary"):
        if len(chat_atual["messages"]) > 0:
            novo_id = str(uuid.uuid4())
            st.session_state.chats[novo_id] = {
                "title": "",
                "mode": chat_atual["mode"],
                "messages": [],
                "gemini_history": []
            }
            st.session_state.current_chat_id = novo_id
            st.rerun()

    # Seleção de Modo
    st.markdown('<div class="sidebar-label">Modo de Operação</div>', unsafe_allow_html=True)
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        is_parecer = chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
        if st.button("📄 Parecer", key="btn_p", type="primary" if is_parecer else "secondary", use_container_width=True):
            chat_atual["mode"] = "📄 Minuta de Parecer (MPMS)"
            st.rerun()
    with col_m2:
        is_juris = chat_atual["mode"] == "🔍 Pesquisa de Jurisprudência"
        if st.button("🔍 Pesquisa", key="btn_j", type="primary" if is_juris else "secondary", use_container_width=True):
            chat_atual["mode"] = "🔍 Pesquisa de Jurisprudência"
            st.rerun()

    # Upload de Múltiplos Arquivos PDF
    uploaded_files = []
    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
        st.markdown('<div class="sidebar-label">Autos do Processo (PDFs)</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload dos Processos",
            type=["pdf"],
            accept_multiple_files=True,
            help="Selecione Petição Inicial, Sentença, Apelação e Laudos",
            label_visibility="collapsed"
        )
        if uploaded_files and len(chat_atual["messages"]) == 0:
            if st.button("⚡ Iniciar Análise do Processo", use_container_width=True, type="primary"):
                st.session_state["trigger_auto_start"] = True
                st.rerun()

    # Histórico de Atendimentos
    conversas_com_historico = {
        cid: cdata for cid, cdata in st.session_state.chats.items() if len(cdata["messages"]) > 0
    }

    if conversas_com_historico:
        st.markdown('<div class="sidebar-label">Histórico de Sessões</div>', unsafe_allow_html=True)
        for chat_id, chat_data in list(conversas_com_historico.items()):
            icone = "📄" if chat_data.get("mode") == "📄 Minuta de Parecer (MPMS)" else "🔍"
            titulo = chat_data["title"] if chat_data["title"] else "Atendimento"
            if len(titulo) > 22:
                titulo = titulo[:20] + "..."
            
            is_active = (chat_id == st.session_state.current_chat_id)
            rotulo = f"{icone} {titulo}" if not is_active else f"👉 **{titulo}**"
            
            c1, c2 = st.columns([0.85, 0.15])
            with c1:
                if st.button(rotulo, key=f"hist_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with c2:
                if st.button("✕", key=f"del_{chat_id}", help="Excluir"):
                    del st.session_state.chats[chat_id]
                    if st.session_state.current_chat_id == chat_id:
                        restantes = list(st.session_state.chats.keys())
                        st.session_state.current_chat_id = restantes[0] if restantes else str(uuid.uuid4())
                        if not restantes:
                            st.session_state.chats[st.session_state.current_chat_id] = {
                                "title": "", "mode": chat_atual["mode"], "messages": [], "gemini_history": []
                            }
                    st.rerun()

    st.markdown('<div class="help-section"></div>', unsafe_allow_html=True)
    if st.button("❓ Guia Operacional & Ajuda", use_container_width=True):
        exibir_manual_ajuda()

# ----------------------------------------------------
# 7. Área Central de Chat com Memória Contínua
# ----------------------------------------------------
st.subheader(chat_atual["mode"])

if len(chat_atual["messages"]) == 0:
    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
        st.info("💡 **Fluxo de Parecer:** Anexe os arquivos PDF na barra lateral (Inicial, Sentença, Apelação) e clique em **`⚡ Iniciar Análise do Processo`**.")
    else:
        st.info("💡 **Pesquisa Unificada:** Digite a tese jurídica, Tema Repetitivo ou matéria a pesquisar nos Tribunais.")

for msg in chat_atual["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Tratamento do disparo automático pós-upload
auto_prompt = None
if st.session_state.get("trigger_auto_start", False):
    st.session_state["trigger_auto_start"] = False
    auto_prompt = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes."[cite: 1]

prompt_input = st.chat_input("Digite sua resposta, orientação ou valide a etapa anterior...")
prompt_final = auto_prompt or prompt_input

if prompt_final:
    if not chat_atual["title"]:
        if uploaded_files:
            chat_atual["title"] = f"Autos ({len(uploaded_files)} docs)"
        else:
            chat_atual["title"] = prompt_final[:30] + ("..." if len(prompt_final) > 30 else "")

    chat_atual["messages"].append({"role": "user", "content": prompt_final})
    with st.chat_message("user"):
        st.markdown(prompt_final)

    with st.chat_message("assistant"):
        with st.spinner("Processando fundamentação e mantendo o contexto dos autos..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                instrucao = (
                    SUPERPROMPT_PARECER
                    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
                    else PROMPT_JURISPRUDENCIA
                )

                # Montagem das partes da mensagem atual
                user_parts = []
                # Se for a primeira mensagem, anexa os arquivos PDF
                if len(chat_atual["gemini_history"]) == 0 and uploaded_files:
                    for f in uploaded_files:
                        user_parts.append(types.Part.from_bytes(data=f.getvalue(), mime_type="application/pdf"))
                        user_parts.append(types.Part.from_text(text=f"[Documento Anexado: {f.name}]"))[cite: 1]

                user_parts.append(types.Part.from_text(text=prompt_final))

                # Registra a mensagem do usuário no histórico do Gemini
                chat_atual["gemini_history"].append(
                    types.Content(role="user", parts=user_parts)
                )

                # Executa a geração com TODO o histórico acumulado
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=chat_atual["gemini_history"],
                    config=types.GenerateContentConfig(
                        system_instruction=instrucao,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1
                    )
                )

                texto_resposta = response.text

                # Registra a resposta do modelo no histórico do Gemini
                chat_atual["gemini_history"].append(
                    types.Content(role="model", parts=[types.Part.from_text(text=texto_resposta)])
                )

                st.markdown(texto_resposta)
                chat_atual["messages"].append({"role": "assistant", "content": texto_resposta})
                st.rerun()

            except Exception as e:
                st.error(f"Erro no processamento da análise: {str(e)}")
