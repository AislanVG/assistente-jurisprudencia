import streamlit as st
import uuid
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página e CSS Profissional
# ----------------------------------------------------
st.set_page_config(
    page_title="JusAssist MPMS",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
<style>
    /* Tipografia e Base */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Botão Principal Novo Chat (Azul Institucional) */
    div[data-testid="stSidebar"] button[kind="primary"] {
        border-radius: 8px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        background-color: #1e3a8a !important; /* Navy Blue Institucional */
        border: none !important;
        color: #ffffff !important;
    }
    div[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }
    
    /* Títulos de Seções da Barra Lateral */
    .sidebar-label {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-top: 18px;
        margin-bottom: 6px;
    }

    /* Cards de Atalho no Centro da Tela */
    .prompt-card {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        background-color: #ffffff;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .prompt-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Carregamento Seguro de Chave
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
Atue como o Assessor Jurídico Sênior da 4ª Procuradoria de Justiça Cível do MPMS, auxiliando diretamente a Procuradora de Justiça, Dra. Luciana Moreira Schenk[cite: 1]. Seu objetivo é elaborar minutas de PARECER DO MINISTÉRIO PÚBLICO EM SEGUNDO GRAU completas, densas e exaustivamente fundamentadas (meta real de 6 a 10 páginas / 2.500 a 4.000 palavras), com tom formal, erudito, sóbrio e cerebral[cite: 1].

### 🛡️ BLINDAGEM E REGRAS ESTRITAS:
1. TRAVA ANTI-ALUCINAÇÃO: Utilize a ferramenta de busca do Google para localizar precedentes, números de REsps, Temas e acórdãos REAIS do STF, STJ e TJMS[cite: 1]. Proibido inventar números ou ementas[cite: 1].
2. TRAVA DE HIERARQUIA: Precedentes das Turmas de Direito Privado do STJ (3ª e 4ª Turmas) e STF PREVALECEM ABSOLUTAMENTE sobre pareceres de Conselhos de Classe (CREMESP/COFFITO), notas do e-NATJus ou resoluções da ANS[cite: 1].
3. DIRETRIZ PROTETIVA: Em saúde, vida e vulneráveis (TEA, paralisia, oncologia, alimentos), a orientação institucional é pela tutela integral da dignidade humana quando amparada por laudo idôneo[cite: 1].
4. RELATÓRIO SUCINTO INSTITUCIONAL: Máximo 500 palavras, fluido em parágrafos encadeados por verbos de ligação ("Alega o apelante que..."), SEM TÓPICOS/BULLETS, finalizando com a fórmula padrão de admissibilidade[cite: 1].
5. ESTILO: Expressões latinas em itálico (*in re ipsa*, *rebus sic stantibus*)[cite: 1]. Jurisprudências citadas em bloco recuado (`>`), em itálico[cite: 1].

### 🔄 FLUXO INTERATIVO AUTOMATIZADO:
- ETAPA 1 (Diagnóstico & Consulta Ativa de Precedentes):
  Apresente o Raio-X dos autos (Fatos, Preliminares mapeadas, Dispositivos legais)[cite: 1].
  EXECUTE UMA BUSCA NA INTERNET por precedentes recentes do STJ/STF/TJMS aderentes ao caso e APRESENTE[cite: 1]:
  "🔍 Precedentes localizados para o caso: [Liste 2 a 3 acórdãos/Temas reais encontrados com número e tese].
  👉 PERGUNTA OBRIGATÓRIA: Deseja aplicar os precedentes acima sugeridos ou a Procuradoria deseja indicar outro acórdão específico para este parecer?"[cite: 1]
  PARE AQUI e aguarde a confirmação do analista[cite: 1].

- ETAPA 2 (Ementa Técnica e Relatório Institucional):
  Após o "de acordo" do analista, gere a Ementa Técnica Formal e o Relatório Sucinto Fluido (até 500 palavras, sem tópicos)[cite: 1]. PARE AQUI e aguarde validação[cite: 1].

- ETAPA 3 (Minuta Integral de Alta Densidade - 6 a 10 páginas):
  Redija a peça completa: Cabeçalho institucional, Ementa, "COLENDA CÂMARA CÍVEL,", Relatório, I – Da controvérsia recursal (ou Preliminares), II – Do mérito (Fundamentação exaustiva de 2.500 a 4.000 palavras), III – Conclusão (Opinamento expresso), Datação (Campo Grande/MS) e Assinatura de Luciana Moreira Schenk[cite: 1].
"""

# ----------------------------------------------------
# 4. Gestão de Sessões
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
    st.markdown("### ⚖️ Guia de Utilização do JusAssist")
    st.markdown(
        """
| Modo | Finalidade | Como Iniciar |
| :--- | :--- | :--- |
| **📄 Minuta de Parecer (MPMS)** | Elaboração de parecer institucional denso (6 a 10 páginas)[cite: 1]. | Anexe o PDF do processo e clique em *Iniciar Análise*[cite: 1]. |
| **🔍 Pesquisa de Jurisprudência** | Varredura de teses, acórdãos e súmulas no STF, STJ e TJs. | Digite livremente a tese jurídica no chat. |
        """
    )
    st.divider()
    st.markdown("### 🚀 Fluxo de Elaboração de Parecer:")
    st.markdown("1. **Upload:** Faça o upload do arquivo PDF dos autos na lateral.")
    st.markdown("2. **Diagnóstico:** A IA apresentará o relatório preliminar com os acórdãos reais encontrados na internet[cite: 1].")
    st.markdown("3. **Aprovação:** Responda no chat com `Aprovado, prossiga` para a IA redigir a Ementa, o Relatório e a Minuta Final[cite: 1].")

# ----------------------------------------------------
# 6. Barra Lateral
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### ⚖️ **JusAssist MPMS**")
    st.caption("4ª Procuradoria de Justiça Cível")
    
    # Ação Principal
    if st.button("➕ Novo Atendimento", use_container_width=True, type="primary"):
        if len(chat_atual["messages"]) > 0:
            novo_id = str(uuid.uuid4())
            st.session_state.chats[novo_id] = {
                "title": "",
                "mode": chat_atual["mode"],
                "messages": []
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

    # Upload Condicional de PDF
    uploaded_file = None
    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
        st.markdown('<div class="sidebar-label">Autos do Processo (PDF)</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload do Processo",
            type=["pdf"],
            help="Petição Inicial, Sentença, Apelação ou Laudos",
            label_visibility="collapsed"
        )
        if uploaded_file and len(chat_atual["messages"]) == 0:
            if st.button("⚡ Iniciar Análise do Processo", use_container_width=True):
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
                            st.session_state.chats[st.session_state.current_chat_id] = {"title": "", "mode": chat_atual["mode"], "messages": []}
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("❓ Guia Operacional", use_container_width=True):
        exibir_manual_ajuda()

# ----------------------------------------------------
# 7. Área Principal de Conteúdo
# ----------------------------------------------------
st.subheader(chat_atual["mode"])

# Exibição do Empty State com Sugestões
if len(chat_atual["messages"]) == 0:
    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
        st.info("💡 **Fluxo de Trabalho:** Anexe o PDF da Apelação ou Sentença na barra lateral e clique no botão de início ou envie orientações abaixo.")
    else:
        st.info("💡 **Pesquisa Unificada:** Digite a matéria jurídica, Tema Repetitivo ou número de recurso a pesquisar nos Tribunais.")

# Exibição das Mensagens
for msg in chat_atual["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Verificação de Disparo Automático pós-upload
auto_prompt = None
if st.session_state.get("trigger_auto_start", False):
    st.session_state["trigger_auto_start"] = False
    auto_prompt = "Analise integralmente as peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes."[cite: 1]

prompt_input = st.chat_input(
    "Digite sua orientação sobre o caso ou envie uma tese jurídica..."
)

prompt_final = auto_prompt or prompt_input

if prompt_final:
    if not chat_atual["title"]:
        chat_atual["title"] = (uploaded_file.name[:25] + "...") if uploaded_file else (prompt_final[:30] + "...")

    chat_atual["messages"].append({"role": "user", "content": prompt_final})
    with st.chat_message("user"):
        st.markdown(prompt_final)

    with st.chat_message("assistant"):
        with st.spinner("Processando fundamentação e pesquisando jurisprudência oficial..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                instrucao = (
                    SUPERPROMPT_PARECER
                    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
                    else PROMPT_JURISPRUDENCIA
                )

                conteudos = []
                if uploaded_file is not None and len(chat_atual["messages"]) <= 1:
                    conteudos.append(types.Part.from_bytes(data=uploaded_file.getvalue(), mime_type="application/pdf"))
                    conteudos.append(f"[Autos Processuais: {uploaded_file.name}]")

                conteudos.append(prompt_final)

                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=instrucao,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1
                    )
                )

                response = chat.send_message(conteudos)
                texto = response.text

                st.markdown(texto)
                chat_atual["messages"].append({"role": "assistant", "content": texto})
                st.rerun()

            except Exception as e:
                st.error(f"Erro na execução da análise: {str(e)}")
