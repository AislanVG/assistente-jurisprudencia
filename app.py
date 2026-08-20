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
Atue como o Assessor Jurídico Sênior da 4ª Procuradoria de Justiça Cível do MPMS, auxiliando diretamente a Procuradora de Justiça, Dra. Luciana Moreira Schenk[cite: 1]. Seu objetivo é elaborar minutas de PARECER DO MINISTÉRIO PÚBLICO EM SEGUNDO GRAU completas, densas e exaustivamente fundamentadas (meta real de 6 a 10 páginas / 2.500 a 4.000 palavras), com tom formal, erudito, sóbrio e cerebral[cite: 1].

### 🛡️ BLINDAGEM E REGRAS ESTRITAS:
1. TRAVA ANTI-ALUCINAÇÃO: Utilize a ferramenta de busca do Google para localizar precedentes, números de REsps, Temas e acórdãos REAIS do STF, STJ e TJMS[cite: 1]. Proibido inventar números ou ementas[cite: 1].
2. TRAVA DE HIERARQUIA: Precedentes das Turmas de Direito Privado do STJ (3ª e 4ª Turmas) e STF PREVALECEM ABSOLUTAMENTE sobre pareceres de Conselhos de Classe (CREMESP/COFFITO), notas do e-NATJus ou resoluções da ANS[cite: 1].
3. DIRETRIZ PROTETIVA: Em saúde, vida e vulneráveis (TEA, paralisia, oncologia, alimentos), a orientação institucional é pela tutela integral da dignidade humana quando amparada por laudo idôneo[cite: 1].
4. RELATÓRIO SUCINTO INSTITUCIONAL: Máximo 500 palavras, fluido em parágrafos encadeados por verbos de ligação ("Alega o apelante que..."), SEM TÓPICOS/BULLETS, finalizando com a fórmula padrão de admissibilidade[cite: 1].
5. ESTILO: Expressões latinas em itálico (*in re ipsa*, *rebus sic stantibus*)[cite: 1]. Jurisprudências citadas em bloco recuado (`>`), em itálico[cite: 1].

### 🔄 FLUXO INTERATIVO AUTOMATIZADO:
Quando o usuário pedir a análise dos autos (com arquivos PDF anexados ou relato fático):

- ETAPA 1 (Diagnóstico & Consulta Ativa de Precedentes):
  Apresente o Raio-X dos autos considerando o conjunto de todas as peças anexadas (Fatos, Preliminares mapeadas, Dispositivos legais)[cite: 1].
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
@st.dialog("📖 Central de Ajuda & Manual Operacional (MPMS)", width="large")
def exibir_manual_ajuda():
    st.markdown("## ⚖️ Manual Operacional: JusAssist MPMS")
    st.caption("Guia Prático para Pesquisa Jurisprudencial e Emissão de Pareceres de 2º Grau")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Minuta de Parecer", 
        "🔍 Pesquisa Jurisprudencial", 
        "🛡️ Diretrizes & Travas", 
        "📝 Comandos de Ajuste"
    ])
    
    with tab1:
        st.markdown("### 🏛️ Fluxo Integrado em Fases (Parecer de 2º Grau)[cite: 1]")
        st.markdown(
            "O assistente é calibrado para atuar como Assessor Jurídico Sênior da 4ª Procuradoria de Justiça Cível do MPMS, "
            "elaborando peças densas e completas com meta real de **6 a 10 páginas (2.500 a 4.000 palavras)**[cite: 1]."
        )
        st.markdown(
            """
1. **Passo 1: Upload dos Autos (Múltiplos PDFs)**[cite: 1]
   * Na barra lateral, selecione **📄 Parecer** e anexe todos os arquivos necessários juntos (Inicial, Sentença, Apelação, Laudos)[cite: 1].
2. **Passo 2: Início da Análise**
   * Clique no botão **`⚡ Iniciar Análise do Processo`** ou digite no chat: `Analise os autos e gere o parecer`[cite: 1].
3. **Passo 3: Diagnóstico & Precedentes (Fase 2)**[cite: 1]
   * A IA apresentará o raio-x consolidando todas as peças e **pesquisará ativamente na internet** acórdãos reais recentes do STJ/STF/TJMS[cite: 1].
4. **Passo 4: Validação da Ementa e Relatório (Fase 3)**[cite: 1]
   * Ao aprovar a tese, a IA redigirá a **Ementa Técnica Formal** e o **Relatório Sucinto Fluido** (até 500 palavras, sem tópicos)[cite: 1].
5. **Passo 5: Minuta Integral de Alta Densidade (Fase 4)**[cite: 1]
   * A IA entrega o parecer pronto para exportação com fundamentação exaustiva e conclusão[cite: 1].
            """
        )

    with tab2:
        st.markdown("### 🔍 Pesquisa Jurisprudencial Analítica")
        st.markdown("No modo **🔍 Pesquisa**, a IA realiza varredura com o Google Search nas bases do STF, STJ, TJMS e TRFs.")
        st.markdown("#### Exemplos Práticos de Pesquisa:")
        st.code("Qual o entendimento do STJ sobre responsabilidade do Estado por erro médico que causa sequelas permanentes em menor?", language="text")
        st.code("Pesquise a jurisprudência do TJMS sobre rescisão de contrato imobiliário por culpa da construtora com devolução integral.", language="text")

    with tab3:
        st.markdown("### 🛡️ Mecanismos de Blindagem Institucional")
        st.markdown(
            """
* **Prevalência Absoluta do STJ / STF:** Precedentes das Turmas de Direito Privado (3ª e 4ª Turmas) e teses vinculantes do STF sobrepõem-se a pareceres técnicos e resoluções administrativas[cite: 1].
* **Diretriz Protetiva (Saúde e Vulneráveis):** Orientação pela tutela integral da dignidade humana quando amparada por laudo idôneo[cite: 1].
* **Trava Anti-Alucinação:** Busca em tempo real no índice oficial, sem inventar julgados[cite: 1].
* **Relatório Padrão Ouro:** Narrativa contínua e fluida de até 500 palavras, estritamente sem bullets[cite: 1].
            """
        )

    with tab4:
        st.markdown("### 🛑 Comandos de Ajuste de Rota (Se não aprovar)[cite: 1]")
        st.markdown("**Exemplo 1: Ajuste de Tese na Fase 2**[cite: 1]")
        st.code("Não está aprovado. Na tese de mérito, considere que a 3ª Turma do STJ já pacificou o custeio pelo REsp 2.221.399/SP. Reformule a Fase 2 opinando pelo desprovimento do recurso.", language="text")[cite: 1]
        st.markdown("**Exemplo 2: Avanço Direto**[cite: 1]")
        st.code("Aprovado o diagnóstico e os precedentes sugeridos. Prossiga para a Fase 3 e 4.", language="text")[cite: 1]

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

    # Upload de Múltiplos Arquivos PDF
    uploaded_files = []
    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
        st.markdown('<div class="sidebar-label">Autos do Processo (PDFs)</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload dos Processos",
            type=["pdf"],
            accept_multiple_files=True,
            help="Selecione ou arraste Petição Inicial, Sentença, Apelação e Laudos juntos",
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
                            st.session_state.chats[st.session_state.current_chat_id] = {"title": "", "mode": chat_atual["mode"], "messages": []}
                    st.rerun()

    st.markdown('<div class="help-section"></div>', unsafe_allow_html=True)
    if st.button("❓ Guia Operacional & Ajuda", use_container_width=True):
        exibir_manual_ajuda()

# ----------------------------------------------------
# 7. Área Central de Chat
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
    auto_prompt = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Fase 2 com a pesquisa de precedentes."[cite: 1]

prompt_input = st.chat_input("Digite sua orientação sobre o caso ou envie uma tese jurídica...")
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
        with st.spinner("Lendo todas as peças processuais e pesquisando precedentes oficiais..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                instrucao = (
                    SUPERPROMPT_PARECER
                    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
                    else PROMPT_JURISPRUDENCIA
                )

                conteudos = []
                # Ingestão de múltiplos PDFs anexados
                if uploaded_files and len(chat_atual["messages"]) <= 1:
                    for f in uploaded_files:
                        conteudos.append(types.Part.from_bytes(data=f.getvalue(), mime_type="application/pdf"))
                        conteudos.append(f"[Documento Anexado: {f.name}]")[cite: 1]

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
