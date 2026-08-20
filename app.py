import streamlit as st
import uuid
import tempfile
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página e CSS Avançado (Jus IA Style)
# ----------------------------------------------------
st.set_page_config(
    page_title="JusAssist MPMS",
    page_icon="⚖️",
    layout="wide"
)

# ----------------------------------------------------
# 2. Carregamento Seguro de Chaves (Secrets)
# ----------------------------------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("⚠️ Chave GEMINI_API_KEY não configurada nos Secrets do Streamlit.")
    st.stop()

# ----------------------------------------------------
# 3. Gerenciamento de Sessões
# ----------------------------------------------------
if "chats" not in st.session_state:
    primeiro_id = str(uuid.uuid4())
    st.session_state.chats = {
        primeiro_id: {
            "title": "",
            "mode": "📄 Minuta de Parecer (MPMS)",
            "messages": [],
            "gemini_history": []
        }
    }
    st.session_state.current_chat_id = primeiro_id

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chats:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

chat_atual = st.session_state.chats[st.session_state.current_chat_id]
chat_vazio = len(chat_atual["messages"]) == 0

# ----------------------------------------------------
# 4. Injeção de CSS Dinâmico (Centralização do Input)
# ----------------------------------------------------
css_customizado = """
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Botões Primários Institucionais (Azul Marinho) */
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

    /* Hero Centrado (Jus IA Style) */
    .hero-title {
        font-size: 34px;
        font-weight: 700;
        color: #1e293b;
        text-align: center;
        margin-top: 5vh;
        margin-bottom: 20px;
    }
"""

# Se o chat estiver vazio, reposiciona o chat_input para o centro da tela
if chat_vazio:
    css_customizado += """
    div[data-testid="stChatInput"] {
        position: fixed !important;
        top: 42% !important;
        bottom: auto !important;
        left: calc(50% + 80px) !important;
        transform: translate(-50%, -50%) !important;
        width: 55% !important;
        max-width: 780px !important;
        z-index: 999 !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1) !important;
        border-radius: 14px !important;
    }
    .hero-spacer {
        height: 120px;
    }
    """
else:
    css_customizado += """
    div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 20px !important;
        z-index: 999 !important;
    }
    """

css_customizado += "</style>"
st.markdown(css_customizado, unsafe_allow_html=True)

# ----------------------------------------------------
# 5. Prompts Especializados
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
1. ADERÊNCIA ESTRITA AOS AUTOS: Baseie sua análise EXCLUSIVAMENTE nos fatos e documentos do caso concreto anexado pelo usuário[cite: 1]. É PROIBIDO inventar ou misturar matérias fáticas estranhas ao processo[cite: 1].
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
# 6. Funções Auxiliares: Resiliência contra Erro 503 & Extração
# ----------------------------------------------------
def extrair_texto_resposta(response) -> str:
    if hasattr(response, "text") and response.text:
        return response.text
    if hasattr(response, "candidates") and response.candidates:
        candidato = response.candidates[0]
        if hasattr(candidato, "content") and hasattr(candidato.content, "parts"):
            textos = [p.text for p in candidato.content.parts if hasattr(p, "text") and p.text]
            if textos:
                return "".join(textos)
    return "A análise foi processada, mas a resposta de texto retornou vazia. Por favor, reenvie a mensagem."

def executar_geracao_com_retry(client, contents, instrucao):
    """Executa a chamada com retry exponencial e fallback para mitigar erros 503/429 da API."""
    modelos_disponiveis = ["gemini-2.5-flash", "gemini-2.0-flash"]
    tentativas_max = 3

    for modelo in modelos_disponiveis:
        for tentativa in range(tentativas_max):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=instrucao,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1
                    )
                )
                return extrair_texto_resposta(response)
            except Exception as e:
                erro_str = str(e).lower()
                if "503" in erro_str or "unavailable" in erro_str or "high demand" in erro_str:
                    time.sleep(2 * (tentativa + 1))
                    continue
                else:
                    raise e
    raise Exception("O servidor da API do Google está enfrentando sobrecarga momentânea (503). Por favor, tente novamente em instantes.")

# ----------------------------------------------------
# 7. Modal Completo de Ajuda e Manual Operacional
# ----------------------------------------------------
@st.dialog("📖 Central de Ajuda & Manual Operacional (MPMS)", width="large")
def exibir_manual_ajuda():
    st.markdown("## ⚖️ Manual Operacional: JusAssist MPMS")
    st.caption("Guia Oficial para Pesquisa Jurisprudencial e Elaboração de Pareceres de 2º Grau")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Minuta de Parecer (MPMS)", 
        "🔍 Pesquisa Jurisprudencial", 
        "🛡️ Diretrizes & Travas", 
        "🛑 Comandos de Ajuste"
    ])
    
    with tab1:
        st.markdown("### 🏛️ Fluxo Integrado em Fases (Parecer de 2º Grau)[cite: 1]")
        st.markdown(
            "O assistente é rigorosamente calibrado para atuar como Assessor Jurídico Sênior da 4ª Procuradoria de Justiça Cível do MPMS, "
            "elaborando peças densas e completas com meta real de **6 a 10 páginas (2.500 a 4.000 palavras)** no corpo da minuta[cite: 1]."
        )
        st.markdown(
            """
1. **Passo 1: Upload dos Autos (Múltiplos PDFs)**[cite: 1]
   * Na barra lateral, selecione **📄 Parecer** e anexe as peças necessárias (Inicial, Sentença, Apelação, Laudos)[cite: 1].
2. **Passo 2: Início da Análise**
   * Clique em `⚡ Iniciar Análise do Processo` ou use o botão central[cite: 1].
3. **Passo 3: Diagnóstico Fático & Precedentes (Fase 2)**[cite: 1]
   * A IA apresentará o raio-x e pesquisará em tempo real acórdãos reais do STJ/STF/TJMS[cite: 1].
4. **Passo 4: Validação da Ementa e Relatório (Fase 3)**[cite: 1]
   * Responda `Aprovado` para gerar a Ementa Técnica e o Relatório Fluido (até 500 palavras, sem marcadores)[cite: 1].
5. **Passo 5: Minuta Final de Alta Densidade (Fase 4)**[cite: 1]
   * Responda `Validado, prossiga` para a IA entregar a minuta completa pronta para exportação[cite: 1].
            """
        )
        st.info("💡 **Dica de Exportação:** Copie o texto da resposta final e cole no Microsoft Word mantendo a formatação de origem (Ctrl + V)[cite: 1].")

    with tab2:
        st.markdown("### 🔍 Pesquisa Jurisprudencial Analítica")
        st.markdown("Varredura em tempo real com Google Search nas bases do STF, STJ, TJMS e TRFs.")
        st.markdown("#### Exemplos Práticos de Pesquisa:")
        st.code("Qual o entendimento do STJ sobre responsabilidade do Estado por erro médico que causa sequelas em menor?", language="text")
        st.code("Pesquise a jurisprudência do TJMS sobre rescisão de contrato imobiliário por culpa da construtora com devolução integral.", language="text")

    with tab3:
        st.markdown("### 🛡️ Mecanismos de Blindagem Institucional")
        st.markdown(
            """
* **Prevalência STJ/STF:** Precedentes de Turmas do STJ e STF sobrepõem-se a notas do e-NATJus ou conselhos[cite: 1].
* **Aderência aos Autos:** Foco restrito aos documentos do processo anexado[cite: 1].
* **Trava Anti-Alucinação:** Pesquisa ativa em bases oficiais, sem inventar julgados[cite: 1].
* **Relatório Padrão Ouro:** Narrativa fluida e encadeada de até 500 palavras, estritamente sem tópicos[cite: 1].
            """
        )

    with tab4:
        st.markdown("### 🛑 Comandos de Ajuste de Rota (Se não aprovar)[cite: 1]")
        st.markdown("**1. Correção de Tese na Fase 2 (Diagnóstico):**")
        st.code("Não está aprovado. Na proposta de mérito, considere que a 3ª Turma do STJ já pacificou o dever de custeio pelo REsp 2.221.399/SP. Reformule a Fase 2 opinando pelo desprovimento do recurso.", language="text")[cite: 1]
        st.markdown("**2. Avanço Direto:**")
        st.code("Aprovado o diagnóstico e os precedentes sugeridos. Prossiga para a emissão da Fase 3 e da Minuta Completa.", language="text")[cite: 1]

# ----------------------------------------------------
# 8. Barra Lateral
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### ⚖️ **JusAssist MPMS**")
    st.caption("4ª Procuradoria de Justiça Cível")
    
    # Novo Chat
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
                st.session_state["trigger_prompt"] = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes."[cite: 1]
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
# 9. Cálculo Preciso de Horário Local (MS / Brasília)
# ----------------------------------------------------
try:
    fuso_ms = ZoneInfo("America/Campo_Grande")
    hora_local = datetime.now(fuso_ms).hour
except Exception:
    hora_local = (datetime.utcnow().hour - 4) % 24  # Fallback UTC-4

if hora_local < 12:
    saudacao = "Qual é o caso da manhã?"
elif hora_local < 18:
    saudacao = "Qual é o caso da tarde?"
else:
    saudacao = "Qual é o caso da noite?"

# ----------------------------------------------------
# 10. Área Principal: Estado Inicial vs. Conversação
# ----------------------------------------------------
if chat_vazio:
    st.markdown(f"<div class='hero-title'>{saudacao}</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-spacer'></div>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 2.8, 1])
    with col_c2:
        if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
            if uploaded_files:
                if st.button("⚡ Analise os autos desse processo e gere o parecer", key="sug_parecer", use_container_width=True, type="primary"):
                    st.session_state["trigger_prompt"] = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes."[cite: 1]
                    st.rerun()
            else:
                st.info("📂 Anexe os arquivos PDF na barra lateral para iniciar a análise dos autos.")
            
            if st.button("💬 Mapeie preliminares e teses recursais deste caso", key="sug_teses", use_container_width=True):
                st.session_state["trigger_prompt"] = "Faça um mapeamento analítico das preliminares e das principais teses recursais cabíveis para o caso."[cite: 1]
                st.rerun()
        else:
            if st.button("🔍 Pesquisar teses de responsabilidade civil do Estado", key="sug_resp", use_container_width=True):
                st.session_state["trigger_prompt"] = "Qual o entendimento consolidado do STJ sobre responsabilidade do Estado por erro médico que causa sequelas em menor?"
                st.rerun()
            if st.button("🔍 Pesquisar obrigatoriedade de cobertura pelo plano de saúde", key="sug_saude", use_container_width=True):
                st.session_state["trigger_prompt"] = "Qual a jurisprudência do STJ sobre o dever do plano de saúde em custear tratamento multidisciplinar para menor com TEA?"
                st.rerun()

else:
    st.subheader(chat_atual["mode"])
    if chat_atual["title"]:
        st.caption(f"Processo: **{chat_atual['title']}**")
        
    for i, msg in enumerate(chat_atual["messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            if msg["role"] == "assistant":
                col_act1, col_act2, col_act3, _ = st.columns([0.15, 0.15, 0.15, 0.55])
                with col_act1:
                    st.download_button(
                        label="📥 Baixar",
                        data=msg["content"],
                        file_name=f"Parecer_MPMS_{i}.txt",
                        mime="text/plain",
                        key=f"dl_{i}",
                        help="Baixar o texto desta resposta"
                    )
                with col_act2:
                    if st.button("👍", key=f"like_{i}", help="Aprovar resposta"):
                        st.toast("Feedback positivo registrado!", icon="✅")
                with col_act3:
                    if st.button("👎", key=f"dislike_{i}", help="Sinalizar ajuste"):
                        st.toast("Feedback registrado para melhoria.", icon="📝")

# ----------------------------------------------------
# 11. Processamento de Mensagens com Memória e Retry
# ----------------------------------------------------
prompt_placeholder = "Digite sua mensagem ou use / para habilidades..." if chat_vazio else "Digite sua resposta ou orientação..."
prompt_digitado = st.chat_input(prompt_placeholder)
prompt_final = st.session_state.pop("trigger_prompt", None) or prompt_digitado

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
        with st.spinner("Processando fundamentação jurídica e pesquisando precedentes oficiais..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                instrucao = (
                    SUPERPROMPT_PARECER
                    if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
                    else PROMPT_JURISPRUDENCIA
                )

                user_parts = []
                
                # Upload seguro dos PDFs para a Files API na 1ª mensagem
                if len(chat_atual["gemini_history"]) == 0 and uploaded_files:
                    for f in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(f.getvalue())
                            tmp_path = tmp.name
                        
                        try:
                            uploaded_gemini_file = client.files.upload(file=tmp_path)
                            user_parts.append(uploaded_gemini_file)
                            user_parts.append(types.Part.from_text(text=f"[Documento dos Autos: {f.name}]"))[cite: 1]
                        finally:
                            if os.path.exists(tmp_path):
                                os.remove(tmp_path)

                user_parts.append(types.Part.from_text(text=prompt_final))

                # Registra a mensagem do usuário no histórico estruturado
                chat_atual["gemini_history"].append(
                    types.Content(role="user", parts=user_parts)
                )

                # Chamada com Retry automático e proteção contra 503
                texto_resposta = executar_geracao_com_retry(client, chat_atual["gemini_history"], instrucao)

                # Salva resposta no histórico estruturado
                chat_atual["gemini_history"].append(
                    types.Content(role="model", parts=[types.Part.from_text(text=texto_resposta)])
                )

                st.markdown(texto_resposta)
                chat_atual["messages"].append({"role": "assistant", "content": texto_resposta})
                st.rerun()

            except Exception as e:
                st.error(f"Erro no processamento da análise: {str(e)}")
