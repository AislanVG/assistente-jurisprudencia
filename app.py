import streamlit as st
import uuid
import time
import json
import re
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client, Client
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página e CSS Avançado
# ----------------------------------------------------
st.set_page_config(
    page_title="JurisPrime AI",
    page_icon="⚖️",
    layout="wide"
)

# ----------------------------------------------------
# 2. Carregamento Seguro de Chaves (Secrets)
# ----------------------------------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
CNJ_API_KEY = st.secrets.get("CNJ_API_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if not GEMINI_API_KEY:
    st.error("⚠️ Chave GEMINI_API_KEY não configurada nos Secrets do Streamlit.")
    st.stop()

# ----------------------------------------------------
# 3. Inicialização do Cliente Supabase
# ----------------------------------------------------
@st.cache_resource
def get_supabase_client() -> Client:
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = get_supabase_client()

# ----------------------------------------------------
# 4. Injeção de CSS Dinâmico (Design Corporativo Sóbrio)
# ----------------------------------------------------
css_customizado = """
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc !important;
    }
    
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100% !important;
    }
    
    .sidebar-brand-container {
        text-align: center;
        padding-top: 6px;
        padding-bottom: 12px;
    }
    .sidebar-brand-icon {
        font-size: 36px;
        display: inline-block;
        margin-bottom: 4px;
    }
    .sidebar-brand-title {
        font-size: 22px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    .sidebar-user-badge {
        font-size: 13px;
        color: #475569;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        padding: 4px 10px;
        border-radius: 6px;
        display: inline-block;
        margin-top: 6px;
        margin-bottom: 14px;
        word-break: break-all;
    }

    div[data-testid="stSidebar"] button[kind="primary"],
    div.stButton > button[kind="primary"] {
        border-radius: 8px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 10px 14px !important;
        background-color: #1e3a8a !important;
        border: 1px solid #1e3a8a !important;
        color: #ffffff !important;
        white-space: nowrap !important;
        text-align: left !important;
    }
    div[data-testid="stSidebar"] button[kind="primary"]:hover,
    div.stButton > button[kind="primary"]:hover {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
    }

    div[data-testid="stSidebar"] button[kind="secondary"] {
        border-radius: 8px !important;
        font-size: 14.5px !important;
        font-weight: 500 !important;
        padding: 10px 14px !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
        background-color: #ffffff !important;
        white-space: nowrap !important;
        text-align: left !important;
    }
    div[data-testid="stSidebar"] button[kind="secondary"]:hover {
        border-color: #94a3b8 !important;
        background-color: #f1f5f9 !important;
    }

    div[data-testid="stStatusWidget"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        margin-bottom: 14px !important;
    }

    .sidebar-label {
        font-size: 13px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-top: 18px;
        margin-bottom: 8px;
    }

    .help-section {
        margin-top: 25px;
        padding-top: 15px;
        border-top: 1px solid #e2e8f0;
    }

    .hero-title {
        font-size: 35px;
        font-weight: 800;
        color: #1e293b;
        text-align: center;
        margin-top: 1vh;
        margin-bottom: 18px;
    }

    .main-chat-container {
        padding-bottom: 100px;
    }

    .action-bar {
        margin-top: 8px;
        margin-bottom: 16px;
    }

    .auth-unified-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 32px 36px 24px 36px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.06), 0 8px 10px -6px rgba(15, 23, 42, 0.03);
        text-align: center;
        max-width: 530px;
        margin: 2vh auto 0 auto;
    }
    
    .auth-badge {
        display: inline-block;
        background: #eff6ff;
        color: #1e3a8a;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        padding: 5px 14px;
        border-radius: 20px;
        margin-bottom: 12px;
        border: 1px solid #dbeafe;
    }
    
    .auth-title {
        font-size: 29px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    
    .auth-subtitle {
        font-size: 15px;
        color: #475569;
        margin-bottom: 16px;
        line-height: 1.45;
    }
    
    .feature-pills {
        display: flex;
        justify-content: center;
        flex-wrap: nowrap;
        gap: 10px;
        margin-bottom: 22px;
    }
    
    .pill {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        color: #334155;
        font-size: 13px;
        font-weight: 600;
        padding: 6px 12px;
        border-radius: 6px;
        white-space: nowrap !important;
    }
    
    div[data-testid="stWidgetLabel"] label p {
        font-size: 15.5px !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        margin-bottom: 4px !important;
        text-align: left !important;
    }
    
    div[data-testid="stTextInput"] input {
        font-size: 15px !important;
        padding: 10px 14px !important;
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
    }
    
    div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    div[data-testid="stForm"] button[kind="primary"],
    div[data-testid="stForm"] button {
        background-color: #1e3a8a !important;
        border-color: #1e3a8a !important;
        color: #ffffff !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        height: 48px !important;
        border-radius: 8px !important;
        margin-top: 14px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stForm"] button:hover {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
    }
    
    .auth-security-footer {
        text-align: center !important;
        font-size: 12.5px !important;
        font-weight: 500 !important;
        color: #64748b !important;
        margin-top: 20px !important;
        margin-bottom: 0px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 6px !important;
        border-top: 1px solid #f1f5f9;
        padding-top: 14px;
    }
</style>
"""
st.markdown(css_customizado, unsafe_allow_html=True)

# ----------------------------------------------------
# 5. Fluxo de Autenticação Seguro
# ----------------------------------------------------
if "user_session" not in st.session_state:
    st.session_state.user_session = None

def exibir_tela_autenticacao():
    col_l1, col_l2, col_l3 = st.columns([1, 1.45, 1])
    with col_l2:
        st.markdown(
            """
            <div class="auth-unified-card">
                <div class="auth-badge">Ecossistema de Inteligência Jurídica</div>
                <div class="auth-title">⚖️ JurisPrime AI</div>
                <div class="auth-subtitle">
                    Pesquisa de Precedentes, Minutas e Auditoria Agêntica de Peças de 2º Grau
                </div>
                <div class="feature-pills">
                    <span class="pill">🔍 Jurisprudência STF/STJ</span>
                    <span class="pill">🛡️ Auditoria & Mentoria</span>
                    <span class="pill">📄 Minutas&nbsp;(6-10&nbsp;págs)</span>
                </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("form_login"):
            email = st.text_input("E-mail cadastrado", placeholder="usuario@dominio.com")
            senha = st.text_input("Senha de Acesso", type="password", placeholder="••••••••")
            btn_entrar = st.form_submit_button("Acessar Plataforma", type="primary", use_container_width=True)
            
            if btn_entrar:
                if not email or not senha:
                    st.warning("Por favor, preencha o e-mail e a senha.")
                elif not supabase:
                    st.error("Credenciais do Supabase não configuradas nos Secrets.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                        if res.user:
                            st.session_state.user_session = res.user
                            st.rerun()
                    except Exception:
                        st.error("Acesso não autorizado. Verifique seu e-mail e senha.")

        st.markdown(
            """
                <div class="auth-security-footer">
                    🔒 <strong>Acesso Restrito & Criptografado</strong> • Ambiente Corporativo Seguro
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

if not st.session_state.user_session:
    exibir_tela_autenticacao()
    st.stop()

# ----------------------------------------------------
# 6. Modal de Alteração de Senha
# ----------------------------------------------------
@st.dialog("🔒 Alterar Minha Senha", width="medium")
def modal_alterar_senha():
    st.markdown("### Defina sua nova senha pessoal")
    st.caption("A nova senha será salva diretamente no seu usuário.")
    
    with st.form("form_troca_senha"):
        nova_senha = st.text_input("Nova Senha (mínimo 6 dígitos)", type="password", placeholder="••••••••")
        confirma_senha = st.text_input("Confirme a Nova Senha", type="password", placeholder="••••••••")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            btn_atualizar = st.form_submit_button("Salvar Senha", type="primary", use_container_width=True)
        with col_t2:
            btn_cancelar = st.form_submit_button("Cancelar", use_container_width=True)
            
        if btn_atualizar:
            if not nova_senha or not confirma_senha:
                st.warning("Preencha ambos os campos de senha.")
            elif nova_senha != confirma_senha:
                st.error("As senhas digitadas não coincidem.")
            elif len(nova_senha) < 6:
                st.warning("A nova senha deve ter no mínimo 6 caracteres.")
            elif not supabase:
                st.error("Erro de conexão com o banco de dados.")
            else:
                try:
                    supabase.auth.update_user({"password": nova_senha})
                    st.success("Senha alterada com sucesso!")
                    time.sleep(1.2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao alterar a senha: {str(e)}")
                    
        if btn_cancelar:
            st.rerun()

# ----------------------------------------------------
# 7. Gerenciamento de Sessões do Assistente
# ----------------------------------------------------
if "chats" not in st.session_state:
    primeiro_id = str(uuid.uuid4())
    st.session_state.chats = {
        primeiro_id: {
            "title": "",
            "mode": "📄 Minuta de Parecer Cível",
            "messages": [],
            "gemini_history": []
        }
    }
    st.session_state.current_chat_id = primeiro_id

if "feedbacks_coletados" not in st.session_state:
    st.session_state.feedbacks_coletados = []

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chats:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

chat_atual = st.session_state.chats[st.session_state.current_chat_id]
chat_vazio = len(chat_atual["messages"]) == 0

# ----------------------------------------------------
# 8. Módulo de Integração com API DataJud (CNJ)
# ----------------------------------------------------
def consultar_datajud_por_numero(numero_processo: str, tribunal: str = "tjsp"):
    if not CNJ_API_KEY:
        return None
    
    num_limpo = re.sub(r"\D", "", numero_processo)
    if len(num_limpo) != 20:
        return None

    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal}/_search"
    headers = {
        "Authorization": f"APIKey {CNJ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": {
            "match": {
                "numeroProcesso": num_limpo
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            hits = dados.get("hits", {}).get("hits", [])
            if hits:
                proc = hits[0].get("_source", {})
                classe = proc.get("classe", {}).get("nome", "Não informada")
                orgao = proc.get("orgaoJulgador", {}).get("nome", "Não informado")
                assuntos = [a.get("nome", "") for a in proc.get("assuntos", [])]
                movs = proc.get("movimentos", [])
                ultimas_movs = [f"{m.get('dataHora', '')[:10]}: {m.get('nome', '')}" for m in movs[-3:]] if movs else []
                
                return (
                    f"**[Dados Oficiais do DataJud/CNJ - {tribunal.upper()}]**\n"
                    f"* **Processo:** {numero_processo}\n"
                    f"* **Classe:** {classe}\n"
                    f"* **Órgão Julgador:** {orgao}\n"
                    f"* **Assuntos:** {', '.join(assuntos)}\n"
                    f"* **Últimas Movimentações:**\n  - " + "\n  - ".join(ultimas_movs)
                )
    except Exception:
        return None
    return None

# ----------------------------------------------------
# 9. Prompts Especializados
# ----------------------------------------------------
PROMPT_JURISPRUDENCIA = """
Você é um consultor jurídico sênior especializado em pesquisa jurisprudencial analítica brasileira.
Sua missão é realizar buscas exatas e verificáveis no STF, STJ e Tribunais Estaduais/Regionais.

### 🚫 TRAVA DE TOLERÂNCIA ZERO À ALUCINAÇÃO JURISPRUDENCIAL:
1. É TERMINANTEMENTE PROIBIDO inventar, supor ou deduzir números de processos, números de REsp, relatores, datas de julgamento ou ementas.
2. Utilize a ferramenta de busca Google Search integrada para verificar a existência real e o teor exato de cada precedente citado.
3. Se não encontrar o número exato de um acórdão específico sobre a matéria, cite expressamente a Súmula, o Tema Vinculante/Repetitivo aplicável ou enuncie a tese consolidada do tribunal sem inventar numerações fictícias.

ESTRUTURA OBRIGATÓRIA DA RESPOSTA:
### 📌 Tese Jurídica Central
Síntese objetiva da posição predominante e ônus probatório.

### ⚖️ Precedentes Favoráveis (Verificados e Reais)
Liste de 2 a 4 julgados específicos com:
* **[Tribunal] – [Classe e Número do Processo Real]**: Resumo fático conciso demonstrando por que o pedido foi acolhido. [Link/Fonte Oficial]

### 🛑 Precedentes Desfavoráveis ou Distinções (Distinguishing)
Apresente hipóteses em que a tese é rejeitada.

### 📋 Critérios Objetivos Extraídos dos Julgados
Lista com os requisitos práticos exigidos pelos magistrados.

### 🏛️ Precedentes Vinculantes (Súmulas e Temas)
Indique Súmulas, Temas Repetitivos (STJ) ou Repercussão Geral (STF) com sua numeração oficial.

### 📝 Sugestão de Ementa para Cópia
Disponibilize o trecho oficial de um acórdão representativo em bloco formatado pronto para citação.
"""

SUPERPROMPT_PARECER = """
Atue como Assessor Jurídico Sênior com atuação em Segundo Grau de Jurisdição (Cível). Seu objetivo é elaborar minutas de PARECER CÍVEL EM SEGUNDO GRAU completas, densas, fluidas e exaustivamente fundamentadas (meta real de 6 a 10 páginas / 2.500 a 4.000 palavras), com tom formal, erudito, sóbrio e cerebral, seguindo o padrão vernáculo e estilístico das manifestações de segundo grau[cite: 1, 2, 3].

### 🏛️ PADRÃO VERNÁCULO FORENSE, URBANIDADE E DECORO PROCESSUAL:
1. É TERMINANTEMENTE PROIBIDO O USO DE LINGUAGEM COLOQUIAL, RASTEIRA OU PERSONALISTA CONTRA O MAGISTRADO DE PRIMEIRO GRAU.
   - NUNCA escreva frases como: "o juiz cometeu um erro", "o magistrado se equivocou", "a decisão está errada", "o juiz não analisou os documentos".
   - A crítica deve ser IMPESSOAL, direcionada à DECISÃO/SENTENÇA[cite: 2, 3]:
     * Utilize fórmulas consagradas: "A r. sentença recorrida comporta reforma..."[cite: 2, 3], "Com a devida vênia ao entendimento esposado pelo d. Juízo singular..."[cite: 2, 3], "O decisum de piso merece reparo..."[cite: 2, 3], "O Apelante/Município parte da premissa correta, mas extrai consequência jurídica incorreta ao sustentar que..."[cite: 2].
2. TRATAMENTO FORENSE: Trate o órgão de origem como "d. Juízo a quo", "d. Juízo singular", "r. sentença combatida/recorrida", e a instância recursal como "Colenda Câmara Cível"[cite: 2, 3], "E. Tribunal de Justiça"[cite: 2, 3], "ínclito Relator".

### 🎯 REGRA DE OURO: SOBERANIA DAS DIRETRIZES DO ASSESSOR (OBEDIÊNCIA ESTRITA)
1. DISTINÇÃO ENTRE 1º GRAU E 2º GRAU:
   - **Decisão do Juiz (1º Grau):** É a decisão ou sentença originária recorrida (objeto do recurso)[cite: 2, 3].
   - **Decisão do Desembargador Relator (2º Grau):** É a decisão monocrática liminar, tutela antecipada recursal ou efeito suspensivo deferido/indeferido no Tribunal de Justiça[cite: 3].
   - **COMANDO DO USUÁRIO:** Se o usuário responder "pelo desprovimento", "pelo provimento", "acompanhe o relator", ADOTE IMEDIATAMENTE essa orientação de mérito e avance sem pedir novas confirmações da mesma pergunta[cite: 1].
2. SOBERANIA TOTAL: A tese e orientação definidas pelo usuário no chat são ABSOLUTAS e VINCULANTES.

### 🛡️ ESTRUTURAÇÃO E REGRAS ESTRITAS DE REDAÇÃO FORENSE:
1. CABEÇALHO E EMENTA TÉCNICA:
   - Cabeçalho formal com: N.º MP, Autos n.º, Classe do Processo, Órgão Julgador, Relator(a), Apelante(s), Apelado(s)[cite: 2, 3].
   - Ementa Técnica Formal: Palavras-chave em CAIXA ALTA separadas por pontos, citando precedentes vinculantes (STF/STJ) e finalizando com o desfecho formal em negrito: "PARECER PELO CONHECIMENTO E PROVIMENTO / DESPROVIMENTO / PARCIAL PROVIMENTO DO RECURSO."[cite: 2, 3]
2. RELATÓRIO DO RECURSO:
   - Inicie com: "Trata-se de Apelação Cível / Agravo de Instrumento interposto por..."[cite: 2, 3].
   - Resuma as alegações do RECORRENTE em parágrafos corridos interligados por verbos técnicos ("Sustenta o apelante que...", "Alega que...", "Nesse sentido, afirma que...", "Argumenta que...", "Ao final, requer...")[cite: 2, 3].
   - Fecho obrigatório do relatório:
     "É o relatório.
     O presente recurso é tempestivo e preenche os demais requisitos de admissibilidade, razão pela qual merece ser conhecido."[cite: 2, 3]
3. CAPÍTULOS OBRIGATÓRIOS DO PARECER:
   - "I – Da controvérsia recursal" (1 a 2 parágrafos delimitando o litígio: "A controvérsia recursal cinge-se a verificar/definir se...")[cite: 2, 3].
   - "II – Da impugnação à justiça gratuita" (se houver)[cite: 3].
   - "II/III – Do mérito" (Fundamentação jurídica densa, exaustiva e contínua de 2.500 a 4.000 palavras, articulando fatos, laudos, leis federais e precedentes vinculantes do STF e STJ)[cite: 1, 2, 3].
   - "III/IV – Conclusão": "Ante o exposto, esta Procuradoria de Justiça manifesta-se pelo conhecimento e provimento / desprovimento / parcial provimento do recurso."[cite: 2, 3]

### 🔄 FLUXO PROGRESSIVO EM 3 ETAPAS:
- **ETAPA 1:** Apresente o Raio-X dos autos e a Pergunta de Validação da tese. PARE e aguarde a resposta do assessor.
- **ETAPA 2:** Quando o usuário responder com o sentido do parecer (ex: "pelo desprovimento", "sim", "confirmado", "prosseguir"), GERE IMEDIATAMENTE a Ementa Técnica Formal e o Relatório do Recurso completo[cite: 1]. PARE e aguarde o comando para gerar a Minuta Integral (Etapa 3)[cite: 1].
- **ETAPA 3:** Quando o usuário autorizar ("prosseguir", "validado", "minuta final"), GERE A PEÇA COMPLETA DE SEGUNDO GRAU integralmente (2.500 a 4.000 palavras) sem qualquer placeholder[cite: 1].
"""

SUPERPROMPT_AUDITORIA = """
Atue como o Assessor Jurídico Sênior Auditor e Mentor Especializado em Segundo Grau de Jurisdição Cível[cite: 1]. Seu objetivo é AUDITAR, AVALIAR e REVISAR exaustivamente as minutas de pareceres elaboradas por estagiários e assessores em formação, fornecendo um parecer técnico de revisão pedagógico, rigoroso, construtivo e totalmente livre de alucinações[cite: 1].

### 🏛️ PADRÃO VERNÁCULO FORENSE E DECORO PROCESSUAL
- Aponte como vício grave de redação qualquer linguagem coloquial, agressiva ou personalista que ataque a figura do magistrado (ex: "o juiz errou", "o juiz cometeu um erro").
- Recomende sempre construções jurídicas impessoais e eruditas (ex: "com a devida vênia ao entendimento firmado na origem, a r. decisão comporta reforma")[cite: 2, 3].

### 🛡️ TRAVA DE HIGIENE DE CONTEXTO E PREVENÇÃO DE CONTAMINAÇÃO PROCESSUAL
- Esta sessão destina-se EXCLUSIVAMENTE à análise, auditoria e redação do PROCESSO ATUAL[cite: 1].
- Se em qualquer momento o usuário tentar iniciar a análise de um NOVO PROCESSO dentro desta mesma conversa, PARE IMEDIATAMENTE e emita o aviso de abertura de Novo Atendimento[cite: 1].

### 🔄 FLUXO DE TRABALHO AGÊNTICO EM 3 FASES:
#### FASE 1: Identificação dos Autos e da Minuta Anexada nos arquivos[cite: 1].
#### FASE 2: Relatório de Auditoria, Nota (0 a 10), Tabela Gramatical de Português e Detecção de Alucinações de IA[cite: 1].
#### FASE 3: Minuta Integral Reestruturada (6 a 10 páginas / 2.500 a 4.000 palavras)[cite: 1].
"""

# ----------------------------------------------------
# 10. Modais de Ajuda
# ----------------------------------------------------
@st.dialog("📖 Central de Ajuda & Manual Operacional", width="large")
def exibir_manual_ajuda():
    st.markdown("## ⚖️ Manual Operacional: JurisPrime AI")
    st.caption("Guia Oficial para Pesquisa Jurisprudencial, Elaboração e Auditoria de Peças de 2º Grau")
    
    tab1, tab2, tab3 = st.tabs(["📄 Minuta de Parecer", "🛡️ Auditoria & Mentoria", "🔍 Pesquisa Jurisprudencial"])
    
    with tab1:
        st.markdown("### 🏛️ Fluxo de Pareceres de 2º Grau[cite: 1]")
        st.markdown("1. Anexe os PDFs na barra lateral e inicie a análise[cite: 1].\n2. Valide a tese jurídica respondendo na Fase 1[cite: 1].\n3. Receba a Ementa/Relatório e depois a Minuta Integral (6-10 páginas)[cite: 1].")

    with tab2:
        st.markdown("### 🛡️ Auditoria Agêntica e Mentoria[cite: 1]")
        st.markdown("Audita minutas de estagiários confrontando-as com as provas dos autos reais, gerando nota, tabela gramatical e peça reestruturada[cite: 1].")

    with tab3:
        st.markdown("### 🔍 Pesquisa Jurisprudencial Analítica")
        st.markdown("Varredura em tempo real integrada ao Google Search e à API do DataJud (CNJ).")

# ----------------------------------------------------
# 11. Barra Lateral (Menu Vertical Limpo e Otimizado)
# ----------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand-container">
            <div class="sidebar-brand-icon">⚖️</div>
            <div class="sidebar-brand-title">JurisPrime AI</div>
            <div class="sidebar-user-badge">👤 {st.session_state.user_session.email}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_u1, col_u2 = st.columns([1.35, 0.85])
    with col_u1:
        if st.button("🔑 Trocar Senha", key="btn_troca_senha_side", use_container_width=True):
            modal_alterar_senha()
    with col_u2:
        if st.button("🚪 Sair", key="btn_sair_side", use_container_width=True):
            if supabase:
                supabase.auth.sign_out()
            st.session_state.user_session = None
            st.rerun()
        
    st.markdown("---")
    
    if st.button("➕ Novo Atendimento", use_container_width=True, type="primary"):
        novo_id = str(uuid.uuid4())
        st.session_state.chats[novo_id] = {
            "title": "",
            "mode": chat_atual["mode"],
            "messages": [],
            "gemini_history": []
        }
        st.session_state.current_chat_id = novo_id
        st.rerun()

    st.markdown('<div class="sidebar-label">Modo de Operação</div>', unsafe_allow_html=True)
    
    is_parecer = chat_atual["mode"] == "📄 Minuta de Parecer Cível"
    if st.button("📄 Parecer Cível (2º Grau)", key="btn_mode_parecer", type="primary" if is_parecer else "secondary", use_container_width=True):
        chat_atual["mode"] = "📄 Minuta de Parecer Cível"
        st.rerun()

    is_audit = chat_atual["mode"] == "🛡️ Auditoria & Mentoria"
    if st.button("🛡️ Auditoria & Mentoria", key="btn_mode_audit", type="primary" if is_audit else "secondary", use_container_width=True):
        chat_atual["mode"] = "🛡️ Auditoria & Mentoria"
        st.rerun()

    is_juris = chat_atual["mode"] == "🔍 Pesquisa de Jurisprudência"
    if st.button("🔍 Pesquisa Jurisprudencial", key="btn_mode_pesquisa", type="primary" if is_juris else "secondary", use_container_width=True):
        chat_atual["mode"] = "🔍 Pesquisa de Jurisprudência"
        st.rerun()

    uploaded_files = []
    
    if chat_atual["mode"] in ["📄 Minuta de Parecer Cível", "🛡️ Auditoria & Mentoria"]:
        rotulo_upload = "Documentos dos Autos e Minuta (PDFs)" if chat_atual["mode"] == "🛡️ Auditoria & Mentoria" else "Autos do Processo (PDFs)"
        st.markdown(f'<div class="sidebar-label">{rotulo_upload}</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload dos Processos",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key=f"uploader_{st.session_state.current_chat_id}"
        )

        if len(chat_atual["messages"]) == 0 and uploaded_files:
            if chat_atual["mode"] == "📄 Minuta de Parecer Cível":
                if st.button("⚡ Iniciar Análise do Processo", use_container_width=True, type="primary"):
                    st.session_state["trigger_prompt"] = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes verificados."
                    st.rerun()
            elif chat_atual["mode"] == "🛡️ Auditoria & Mentoria":
                if st.button("🛡️ Iniciar Auditoria dos Autos e Minuta", use_container_width=True, type="primary"):
                    st.session_state["trigger_prompt"] = "Execute a FASE 2 da Auditoria Agêntica: realize o cruzamento minucioso das peças processuais com a minuta do estagiário/assessor anexadas nos arquivos."
                    st.rerun()

    conversas_com_historico = {
        cid: cdata for cid, cdata in st.session_state.chats.items() if len(cdata["messages"]) > 0
    }

    if conversas_com_historico:
        st.markdown('<div class="sidebar-label">Histórico de Sessões</div>', unsafe_allow_html=True)
        for chat_id, chat_data in list(conversas_com_historico.items()):
            modo_icon = "📄" if chat_data.get("mode") == "📄 Minuta de Parecer Cível" else ("🛡️" if chat_data.get("mode") == "🛡️ Auditoria & Mentoria" else "🔍")
            titulo = chat_data["title"] if chat_data["title"] else "Atendimento"
            if len(titulo) > 20:
                titulo = titulo[:18] + "..."
            
            is_active = (chat_id == st.session_state.current_chat_id)
            rotulo = f"{modo_icon} {titulo}" if not is_active else f"👉 **{titulo}**"
            
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
# 12. Área Principal: Telas Iniciais vs. Chat
# ----------------------------------------------------
if chat_vazio:
    st.markdown("<div class='hero-title'>Qual é o caso de hoje?</div>", unsafe_allow_html=True)
    col_c1, col_c2, col_c3 = st.columns([0.5, 3.5, 0.5])
    with col_c2:
        if uploaded_files:
            if st.button("⚡ Analisar autos e gerar parecer completo", use_container_width=True, type="primary"):
                st.session_state["trigger_prompt"] = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes verificados."
                st.rerun()
        else:
            st.info("📂 Anexe os arquivos PDF na barra lateral para iniciar a análise dos autos.")

else:
    st.subheader(chat_atual["mode"])
    if chat_atual["title"]:
        st.caption(f"Processo / Atendimento: **{chat_atual['title']}**")
    
    st.markdown("<div class='main-chat-container'>", unsafe_allow_html=True)
    for i, msg in enumerate(chat_atual["messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                st.download_button(
                    label="📥 Baixar",
                    data=msg["content"],
                    file_name=f"Manifestacao_{i}.txt",
                    mime="text/plain",
                    key=f"dl_{i}"
                )
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# 13. Processamento com Status e Escrita Externa Imediata
# ----------------------------------------------------
prompt_placeholder = "Digite sua mensagem, orientação de ajuste ou comando..." if not chat_vazio else "Digite sua matéria jurídica ou orientação..."
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
        # 1. Box de Status com Raciocínio (Executa e fecha antes da escrita)
        with st.status("🧠 Analisando autos e raciocinando...", expanded=True) as status_box:
            st.write("📂 **Lendo acervo probatório dos autos...**")
            st.write("🔍 **Consultando jurisprudência e teses vinculantes no STF e STJ...**")
            st.write("✍️ **Estruturando fundamentação jurídica de Segundo Grau...**")
            status_box.update(label="✅ Análise concluída", state="complete", expanded=False)

        # 2. Renderização da Resposta FORA do status, diretamente no corpo da mensagem
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            if chat_atual["mode"] == "🛡️ Auditoria & Mentoria":
                instrucao = SUPERPROMPT_AUDITORIA
            elif chat_atual["mode"] == "📄 Minuta de Parecer Cível":
                instrucao = SUPERPROMPT_PARECER
            else:
                instrucao = PROMPT_JURISPRUDENCIA

            user_parts = []
            
            # Ingestão binária dos PDFs apenas na 1ª mensagem da sessão
            if len(chat_atual["gemini_history"]) == 0 and uploaded_files:
                for f in uploaded_files:
                    pdf_bytes = f.getvalue()
                    user_parts.append(
                        types.Part.from_bytes(
                            data=pdf_bytes,
                            mime_type="application/pdf"
                        )
                    )
                    user_parts.append(types.Part.from_text(text=f"[Documento Anexado: {f.name}]"))

            user_parts.append(types.Part.from_text(text=prompt_final))

            chat_atual["gemini_history"].append(
                types.Content(role="user", parts=user_parts)
            )

            config_params = {
                "system_instruction": instrucao,
                "temperature": 0.0,
                "max_output_tokens": 8192,
                "tools": [types.Tool(google_search=types.GoogleSearch())]
            }

            def stream_generator():
                for tentativa in range(3):
                    try:
                        response_stream = client.models.generate_content_stream(
                            model="gemini-2.5-flash",
                            contents=chat_atual["gemini_history"],
                            config=types.GenerateContentConfig(**config_params)
                        )
                        for chunk in response_stream:
                            if chunk.text:
                                yield chunk.text
                        return
                    except Exception as err:
                        err_msg = str(err).lower()
                        if "429" in err_msg or "resource_exhausted" in err_msg or "503" in err_msg:
                            time.sleep(2 * (tentativa + 1))
                            if tentativa == 2:
                                raise Exception("Cota temporariamente excedida. Tente novamente em alguns segundos.")
                            continue
                        else:
                            raise err

            texto_resposta = st.write_stream(stream_generator())

            chat_atual["gemini_history"].append(
                types.Content(role="model", parts=[types.Part.from_text(text=texto_resposta)])
            )
            chat_atual["messages"].append({"role": "assistant", "content": texto_resposta})
            st.rerun()

        except Exception as e:
            st.error(f"Erro no processamento da análise: {str(e)}")
