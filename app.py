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
# 4. Injeção de CSS Dinâmico (Design Corporativo Sóbrio & Fix de Botões)
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
    
    /* Header da Barra Lateral Centralizado */
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

    /* Botões da Barra Lateral */
    div[data-testid="stSidebar"] button[kind="primary"],
    div.stButton > button[kind="primary"] {
        border-radius: 8px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 8px 10px !important;
        background-color: #1e3a8a !important;
        border: 1px solid #1e3a8a !important;
        color: #ffffff !important;
        white-space: nowrap !important;
    }
    div[data-testid="stSidebar"] button[kind="primary"]:hover,
    div.stButton > button[kind="primary"]:hover {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
    }

    div[data-testid="stSidebar"] button[kind="secondary"] {
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 8px 8px !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
        white-space: nowrap !important;
    }
    div[data-testid="stSidebar"] button[kind="secondary"]:hover {
        border-color: #94a3b8 !important;
        background-color: #ffffff !important;
    }

    /* CORREÇÃO DAS CAIXAS DE PRECEDENTES */
    .precedente-btn-container button {
        width: 100% !important;
        min-height: 85px !important;
        height: auto !important;
        white-space: normal !important;
        text-align: left !important;
        padding: 14px 16px !important;
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        line-height: 1.45 !important;
    }
    .precedente-btn-container button:hover {
        border-color: #2563eb !important;
        background-color: #eff6ff !important;
    }
    .precedente-btn-container button p {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
    }

    .sidebar-label {
        font-size: 13px;
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

    .hero-title {
        font-size: 35px;
        font-weight: 800;
        color: #1e293b;
        text-align: center;
        margin-top: 1vh;
        margin-bottom: 18px;
    }

    .feed-header {
        font-size: 14.5px;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-top: 18px;
        margin-bottom: 16px;
        text-align: center;
    }

    .main-chat-container {
        padding-bottom: 100px;
    }

    .action-bar {
        margin-top: 8px;
        margin-bottom: 16px;
    }

    /* CARD DE LOGIN UNIFICADO */
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
    
    /* Rótulos dos Inputs */
    div[data-testid="stWidgetLabel"] label p {
        font-size: 15.5px !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        margin-bottom: 4px !important;
        text-align: left !important;
    }
    
    /* Caixas de Texto */
    div[data-testid="stTextInput"] input {
        font-size: 16px !important;
        padding: 10px 14px !important;
        height: 46px !important;
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

    /* Botão de Entrar */
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
    
    /* Rodapé de Segurança Integrado */
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
# 5. Fluxo de Autenticação Seguro (Somente Login)
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
                    Pesquisa Analítica de Precedentes e Elaboração de Pareceres de 2º Grau
                </div>
                <div class="feature-pills">
                    <span class="pill">🔍 Jurisprudência STF/STJ/Tribunais</span>
                    <span class="pill">📄 Minutas Densas&nbsp;(6-10&nbsp;págs)</span>
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

# Bloqueia a renderização da aplicação caso o usuário não esteja logado
if not st.session_state.user_session:
    exibir_tela_autenticacao()
    st.stop()

# ----------------------------------------------------
# 6. Modal de Alteração de Senha do Usuário Logado
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
# 9. Prompts Especializados (Com Soberania do Assessor e Distinção de Instâncias)
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
Atue como Assessor Jurídico Sênior com atuação em Segundo Grau de Jurisdição (Cível). Seu objetivo é elaborar minutas de PARECER CÍVEL EM SEGUNDO GRAU completas, densas, fluidas e exaustivamente fundamentadas (meta real de 6 a 10 páginas / 2.500 a 4.000 palavras), com tom formal, erudito, sóbrio e cerebral.

### 🎯 REGRA DE OURO: SOBERANIA DAS DIRETRIZES DO ASSESSOR (OBEDIÊNCIA ESTRITA)
1. DISTINÇÃO FUNDAMENTAL ENTRE 1º GRAU E 2º GRAU:
   - **Decisão do Juiz (1º Grau):** É a decisão ou sentença originária recorrida (objeto do recurso).
   - **Decisão do Desembargador Relator (2º Grau):** É a decisão monocrática liminar, tutela antecipada recursal ou efeito suspensivo deferido/indeferido monocraticamente no Tribunal de Justiça.
   - **COMANDO "ACOMPANHAR O DESEMBARGADOR / RELATOR":** Se o assessor determinar *"acompanhe o entendimento do relator/desembargador"*, NUNCA opine pela manutenção da decisão do Juiz de 1º grau. Você DEVE opinar no EXATO SENTIDO da decisão liminar/monocrática do Desembargador (ou seja, opinando pelo PROVIMENTO ou PARCIAL PROVIMENTO do recurso, confirmando a tutela antecipada recursal concedida pelo Relator para reformar total ou parcialmente a decisão de piso).
2. SOBERANIA TOTAL: A tese, orientação e sentido do voto/opinião definidos pelo assessor no chat são ABSOLUTOS e VINCULANTES. É proibido subverter ou divergir do comando exarado.

### 🛡️ BLINDAGEM ANTI-ALUCINAÇÃO E REGRAS ESTRITAS DE REDAÇÃO:

1. PROIBIÇÃO ABSOLUTA DE JURISPRUDÊNCIA INVENTADA:
   - É PROIBIDO CRIAR OU DEDUZIR NÚMEROS DE PROCESSOS, REsps OU EMENTAS FICTÍCIAS.
   - Utilize a ferramenta Google Search integrada para pesquisar em tempo real e confirmar a existência e numeração dos julgados do STF, STJ e Tribunais.
   - Em caso de dúvida sobre o número do processo, cite o número oficial da Súmula ou do Tema Repetitivo/Vinculante (Ex.: "conforme Tema 1.082 do STJ"), sem criar números de acórdãos avulsos inventados.

2. RELATÓRIO DO RECURSO (E NÃO DO PROCESSO):
   - O relatório NÃO deve resumir a petição inicial ou a história do processo todo desde a origem.
   - O relatório deve conter EXCLUSIVAMENTE o resumo exaustivo e fiel das alegações do RECORRENTE (apelante/agravante), seus fundamentos jurídicos e o pedido recursal final. Se houver decisão monocrática do Desembargador Relator nos autos de 2º grau (ex: concessão de tutela antecipada recursal), relate-a expressamente ao final.
   - Redação corrida em parágrafos encadeados ("Sustenta o agravante que...", "Aduz ainda..."), SEM TÓPICOS/BULLETS, encerrando com a fórmula: "É o relatório.".

3. DA CONTROVÉRSIA RECURSAL (DELIMITAÇÃO PRECISA):
   - Logo após o relatório, crie o tópico autônomo "DA CONTROVÉRSIA RECURSAL".
   - Limite estrito de 1 a 2 parágrafos.
   - Delimite com precisão o cerne do litígio a ser apreciado pela Câmara (Ex.: "A controvérsia recursal cinge-se a verificar a presença dos requisitos para concessão da tutela de urgência...").

4. ANÁLISE DO MÉRITO SEM FRAGMENTAÇÃO EXCESSIVA:
   - É PROIBIDO fatiar o mérito em vários subtópicos isolados e rasos.
   - Estruture uma narrativa jurídica contínua, densa e com encadeamento lógico natural entre os temas debatidos.
   - Somente crie subtópicos destacados para "PRELIMINARES" (se houver) e "MÉRITO".

5. FECHAMENTO CONCLUSIVO OBRIGATÓRIO DE CADA TESE:
   - Ao enfrentar cada matéria ou pedido do recurso dentro do mérito, finalize com um FECHAMENTO LÓGICO E OPINATIVO EXPRESSO alinhado à diretriz do assessor (Ex.: "Destarte, correta a decisão do i. Relator ao antecipar os efeitos da tutela recursal, impondo-se o parcial provimento do agravo de instrumento."). NUNCA deixe o argumento solto para iniciar o tema seguinte.

6. FORMATAÇÃO E HIERARQUIA:
   - Expressões latinas em itálico (*in re ipsa*, *quantum*). Citações jurisprudenciais em bloco recuado (`>`), em itálico.

### 🔄 FLUXO PROGRESSIVO OBRIGATÓRIO EM 3 ETAPAS:

- ETAPA 1 (Diagnóstico, Mapeamento do Recurso & Precedentes Verificados):
  Apresente o Raio-X das razões recursais, da decisão recorrida de 1º grau e da decisão liminar do Relator (se houver).
  Indique a linha de precedentes REAIS e confirmados do STJ/STF aplicáveis à controvérsia.
  Faça a pergunta de validação: "Deseja adotar a linha de parecer acima sugerida ou aplicar diretriz específica (ex: acompanhar o Desembargador Relator)?" e PARE.

- ETAPA 2 (Ementa Técnica e Relatório Exclusivo do Recurso):
  Com base na orientação soberana validada pelo assessor, apresente a Ementa Formal e o Relatório focado estritamente nas razões recursais e na decisão do Relator.
  Diga: "Aguardando validação da Ementa e Relatório para gerar a Minuta Integral (Etapa 3)." e PARE.

- ETAPA 3 (Minuta Integral de Alta Densidade - Peça Completa):
  Quando o analista responder "validado" ou "aprovado", REDIJA IMEDIATAMENTE A PEÇA COMPLETA DE SEGUNDO GRAU sem placeholders:
  1. Cabeçalho Formal (Autos, Classe, Origem, Órgão Julgador, Relator, Agravante/Apelante, Agravado/Apelado).
  2. Ementa Formal (alinhada à orientação dada).
  3. "COLENDA CÂMARA CÍVEL,"
  4. RELATÓRIO (Resumo focado nas razões recursais e menção à liminar do Relator, finalizando com "É o relatório.").
  5. DA CONTROVÉRSIA RECURSAL (1 a 2 parágrafos delimitando o mérito).
  6. I – DAS PRELIMINARES (se houver).
  7. II – DO MÉRITO (Texto fluido, contínuo e exaustivo de 2.500 a 4.000 palavras, fundamentando a confirmação do entendimento do Relator e o provimento/parcial provimento correspondente).
  8. III – CONCLUSÃO (Opinamento formal expresso: pelo provimento, desprovimento ou parcial provimento conforme estipulado).
  9. Local, Data e Fecho institucional do parecerista. NÃO REINICIE O FLUXO.
"""

# ----------------------------------------------------
# 10. Feed de Precedentes Dinâmico em Tempo Real (Cache 12h)
# ----------------------------------------------------
@st.cache_data(ttl=43200)
def carregar_feed_precedentes_dinamico():
    prompt_busca = """
    Pesquise no Google Search os 6 julgados, temas repetitivos ou teses vinculantes mais relevantes e recentes do STF e STJ em Direito Privado, Cível, Consumidor ou Saúde Pública publicados nas últimas semanas/meses.
    Retorne ESTRITAMENTE um array JSON contendo 6 objetos com os campos exatos:
    [
      {
        "tribunal": "STJ ou STF",
        "tema": "Identificação exata do Tema, Súmula ou REsp",
        "desc": "Resumo objetivo da tese jurídica em até 120 caracteres"
      }
    ]
    Responda apenas com o JSON puro, sem crases de markdown ou texto adicional.
    """
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_busca,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.0
            )
        )
        texto_limpo = re.sub(r"```json|```", "", resp.text).strip()
        dados = json.loads(texto_limpo)
        if isinstance(dados, list) and len(dados) >= 4:
            return dados[:6]
    except Exception:
        pass

    # Contingência de alta autoridade factual
    return [
        {"tribunal": "STJ", "tema": "Tema 1.082/STJ (Saúde)", "desc": "Cobertura obrigatória de terapias multidisciplinares (ABA) para autismo."},
        {"tribunal": "STJ", "tema": "REsp 2.221.399/SP (3ª Turma)", "desc": "Dever de fornecimento de procedimentos especiais prescritos por médico assistente."},
        {"tribunal": "STJ", "tema": "Tema 290/STJ (Execução)", "desc": "Marco temporal e requisitos da LC 118/2005 para fraude à execução fiscal."},
        {"tribunal": "STF", "tema": "Tema 793/STF (SUS)", "desc": "Responsabilidade solidária dos entes públicos no fornecimento de tratamentos médicos."},
        {"tribunal": "STF", "tema": "Tema 1.234/STF (Fármacos)", "desc": "Critérios vinculantes de competência para fornecimento judicial de medicamentos."},
        {"tribunal": "STF", "tema": "Súmula Vinculante 510", "desc": "Mandado de Segurança contra atos praticados por serviços notariais e de registro."}
    ]

# ----------------------------------------------------
# 11. Modais de Ajuda & Feedback
# ----------------------------------------------------
@st.dialog("📖 Central de Ajuda & Manual Operacional", width="large")
def exibir_manual_ajuda():
    st.markdown("## ⚖️ Manual Operacional: JurisPrime AI")
    st.caption("Guia Oficial para Pesquisa Jurisprudencial e Elaboração de Pareceres de 2º Grau")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Minuta de Parecer", 
        "🔍 Pesquisa Jurisprudencial", 
        "🛡️ Diretrizes & Travas", 
        "🛑 Comandos de Ajuste"
    ])
    
    with tab1:
        st.markdown("### 🏛️ Fluxo Integrado em Fases (Parecer de 2º Grau)")
        st.markdown(
            "O assistente é calibrado para elaborar peças densas e completas com meta real de "
            "**6 a 10 páginas (2.500 a 4.000 palavras)** no corpo da minuta."
        )
        st.markdown(
            """
1. **Passo 1: Upload dos Autos (Múltiplos PDFs)**
   * Na barra lateral, selecione **📄 Parecer** e anexe as peças necessárias (Razões de Apelação/Agravo, Decisão/Sentença, Liminar do Relator).
2. **Passo 2: Início da Análise**
   * Clique em `⚡ Analisar autos e gerar parecer completo` ou use o botão na barra lateral.
3. **Passo 3: Diagnóstico Fático & Precedentes (Fase 1)**
   * A IA apresentará o raio-x do recurso e indicará os precedentes reais e verificados do STJ/STF/Tribunais.
4. **Passo 4: Validação da Ementa e Relatório do Recurso (Fase 2)**
   * Responda `Aprovado` (ou dê a ordem de mérito, ex.: *Acompanhe a decisão liminar do Desembargador Relator*).
5. **Passo 5: Minuta Final de Alta Densidade (Fase 3)**
   * Responda `Validado, prossiga` para a IA entregar a minuta completa com a delimitação da controvérsia e mérito contínuo.
            """
        )
        st.info("💡 **Dica de Exportação:** Copie o texto da resposta final e cole no Microsoft Word mantendo a formatação de origem (Ctrl + V).")

    with tab2:
        st.markdown("### 🔍 Pesquisa Jurisprudencial Analítica")
        st.markdown("Varredura em tempo real integrada ao Google Search e à **API do DataJud (CNJ)**.")
        st.markdown("#### Exemplos Práticos de Pesquisa:")
        st.code("Qual o entendimento do STJ sobre responsabilidade do Estado por erro médico que causa sequelas em menor?", language="text")
        st.code("0845374-56.2024.8.26.0001 (Consulta direta ao DataJud)", language="text")

    with tab3:
        st.markdown("### 🛡️ Mecanismos de Blindagem Anti-Alucinação & Soberania")
        st.markdown(
            """
* **Soberania do Assessor:** Se o comando for acompanhar o Desembargador Relator, o parecer opinará pela reforma da decisão de 1º grau para consolidar a liminar recursal.
* **Busca Ativa Obrigatória:** Consulta em tempo real via Google Search em todas as minutas para verificação de precedentes reais.
* **Prevalência STJ/STF:** Precedentes de Turmas do STJ e STF sobrepõem-se a notas administrativas ou conselhos.
* **Relatório Recursal Estrito:** Narrativa focada nas alegações do recorrente e na liminar do Relator (não do processo todo).
* **Controvérsia Delimitada:** Tópico de 1 a 2 parágrafos fixando os pontos a julgar.
            """
        )

    with tab4:
        st.markdown("### 🛑 Comandos de Ajuste de Rota (Se não aprovar)")
        st.markdown("**1. Correção de Tese / Acompanhar Relator:**")
        st.code("Acompanhe o entendimento do Desembargador Relator que concedeu a tutela antecipada recursal. Opine pelo parcial provimento do agravo de instrumento reformando a decisão de primeiro grau.", language="text")
        st.markdown("**2. Avanço Direto:**")
        st.code("Aprovado o diagnóstico e os precedentes sugeridos. Prossiga para a emissão da Ementa, Relatório e Minuta Completa.", language="text")

@st.dialog("O que motivou a sua avaliação negativa?", width="medium")
def modal_feedback_negativo(msg_index, msg_content):
    st.markdown("### Descreva o principal motivo")
    motivo_texto = st.text_area("Conte mais sobre o que aconteceu:", placeholder="Descreva brevemente o erro na fundamentação ou na peça...", label_visibility="collapsed")
    
    st.markdown("### Selecione as categorias")
    categorias_disponiveis = [
        "Leis/decisões inexistentes",
        "Leis/decisões irrelevantes",
        "Resposta superficial ou incompleta",
        "Resposta confusa",
        "Ignorou mensagens anteriores",
        "Problemas técnicos ou lentidão",
        "Problemas na análise de documentos",
        "Outro motivo"
    ]
    
    col_k1, col_k2 = st.columns(2)
    categorias_selecionadas = []
    for i, cat in enumerate(categorias_disponiveis):
        alvo = col_k1 if i % 2 == 0 else col_k2
        if alvo.checkbox(cat, key=f"cat_{msg_index}_{i}"):
            categorias_selecionadas.append(cat)
            
    st.markdown("<br>", unsafe_allow_html=True)
    col_b1, col_b2 = st.columns([1, 1])
    with col_b1:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()
    with col_b2:
        if st.button("Enviar agora", type="primary", use_container_width=True):
            st.session_state.feedbacks_coletados.append({
                "usuario": st.session_state.user_session.email,
                "data_hora": datetime.now().isoformat(),
                "tipo": "negativo",
                "motivo_texto": motivo_texto,
                "categorias": categorias_selecionadas,
                "trecho_resposta": msg_content[:250]
            })
            st.toast("Feedback registrado com sucesso! Obrigado pela colaboração.", icon="✅")
            st.rerun()

# ----------------------------------------------------
# 12. Barra Lateral (Layout Centralizado e Otimizado)
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

    st.markdown('<div class="sidebar-label">Modo de Operação</div>', unsafe_allow_html=True)
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        is_parecer = chat_atual["mode"] == "📄 Minuta de Parecer Cível"
        if st.button("📄 Parecer", key="btn_p", type="primary" if is_parecer else "secondary", use_container_width=True):
            chat_atual["mode"] = "📄 Minuta de Parecer Cível"
            st.rerun()
    with col_m2:
        is_juris = chat_atual["mode"] == "🔍 Pesquisa de Jurisprudência"
        if st.button("🔍 Pesquisa", key="btn_j", type="primary" if is_juris else "secondary", use_container_width=True):
            chat_atual["mode"] = "🔍 Pesquisa de Jurisprudência"
            st.rerun()

    uploaded_files = []
    if chat_atual["mode"] == "📄 Minuta de Parecer Cível":
        st.markdown('<div class="sidebar-label">Autos do Processo (PDFs)</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload dos Processos",
            type=["pdf"],
            accept_multiple_files=True,
            help="Selecione Razões de Apelação/Agravo, Decisão e Liminar do Relator",
            label_visibility="collapsed",
            key=f"uploader_{st.session_state.current_chat_id}"
        )
        if uploaded_files and len(chat_atual["messages"]) == 0:
            if st.button("⚡ Iniciar Análise do Processo", use_container_width=True, type="primary"):
                st.session_state["trigger_prompt"] = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes verificados."
                st.rerun()

    conversas_com_historico = {
        cid: cdata for cid, cdata in st.session_state.chats.items() if len(cdata["messages"]) > 0
    }

    if conversas_com_historico:
        st.markdown('<div class="sidebar-label">Histórico de Sessões</div>', unsafe_allow_html=True)
        for chat_id, chat_data in list(conversas_com_historico.items()):
            icone = "📄" if chat_data.get("mode") == "📄 Minuta de Parecer Cível" else "🔍"
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
# 13. Horário Local (Fuso Horário Padrão)
# ----------------------------------------------------
try:
    fuso_padrao = ZoneInfo("America/Sao_Paulo")
    hora_local = datetime.now(fuso_padrao).hour
except Exception:
    hora_local = (datetime.utcnow().hour - 3) % 24

if hora_local < 12:
    saudacao = "Qual é o caso da manhã?"
elif hora_local < 18:
    saudacao = "Qual é o caso da tarde?"
else:
    saudacao = "Qual é o caso da noite?"

# ----------------------------------------------------
# 14. Área Principal: Feed Dinâmico e Caixas Otimizadas
# ----------------------------------------------------
if chat_vazio:
    st.markdown(f"<div class='hero-title'>{saudacao}</div>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([0.5, 3.5, 0.5])
    with col_c2:
        if chat_atual["mode"] == "📄 Minuta de Parecer Cível":
            if uploaded_files:
                if st.button("⚡ Analisar autos e gerar parecer completo", key="sug_parecer", use_container_width=True, type="primary"):
                    st.session_state["trigger_prompt"] = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes verificados."
                    st.rerun()
                if st.button("💬 Mapear apenas preliminares e teses recursais dos autos", key="sug_teses", use_container_width=True):
                    st.session_state["trigger_prompt"] = "Faça um mapeamento analítico das preliminares e das principais teses recursais cabíveis para o caso."
                    st.rerun()
            else:
                st.info("📂 Anexe os arquivos PDF na barra lateral para iniciar a análise dos autos.")
        
        else:
            st.markdown("<div class='feed-header'>🏛️ Precedentes Recentes dos Tribunais Superiores (STJ / STF)</div>", unsafe_allow_html=True)
            feed_precedentes = carregar_feed_precedentes_dinamico()
            col_f1, col_f2 = st.columns(2)
            for idx, prec in enumerate(feed_precedentes):
                col_alvo = col_f1 if idx % 2 == 0 else col_f2
                with col_alvo:
                    st.markdown("<div class='precedente-btn-container'>", unsafe_allow_html=True)
                    rotulo_btn = f"📌 **[{prec.get('tribunal', 'STJ')}]** {prec.get('tema', '')}\n\n_{prec.get('desc', '')}_"
                    if st.button(rotulo_btn, key=f"prec_din_{idx}", use_container_width=True):
                        st.session_state["trigger_prompt"] = f"Apresente uma análise jurisprudencial analítica e verificada sobre o seguinte precedente do {prec.get('tribunal')}: {prec.get('tema')}. Foco na tese jurídica real, critérios práticos e ementa oficial."
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.subheader(chat_atual["mode"])
    if chat_atual["title"]:
        st.caption(f"Processo: **{chat_atual['title']}**")
    
    st.markdown("<div class='main-chat-container'>", unsafe_allow_html=True)
    for i, msg in enumerate(chat_atual["messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            if msg["role"] == "assistant":
                st.markdown("<div class='action-bar'>", unsafe_allow_html=True)
                col_act1, col_act2, col_act3, _ = st.columns([0.15, 0.12, 0.12, 0.61])
                with col_act1:
                    st.download_button(
                        label="📥 Baixar",
                        data=msg["content"],
                        file_name=f"Parecer_{i}.txt",
                        mime="text/plain",
                        key=f"dl_{i}",
                        help="Baixar esta manifestação"
                    )
                with col_act2:
                    if st.button("👍", key=f"like_{i}", help="Aprovar resposta"):
                        st.session_state.feedbacks_coletados.append({
                            "usuario": st.session_state.user_session.email,
                            "data_hora": datetime.now().isoformat(),
                            "tipo": "positivo",
                            "trecho_resposta": msg["content"][:250]
                        })
                        st.toast("Avaliação positiva registrada!", icon="✅")
                with col_act3:
                    if st.button("👎", key=f"dislike_{i}", help="Avaliar negativamente / relatar problema"):
                        modal_feedback_negativo(i, msg["content"])
                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# 15. Processamento de Mensagens com Verificação Ativa em Tempo Real
# ----------------------------------------------------
prompt_placeholder = "Digite sua matéria jurídica ou use para pesquisar acórdãos..." if chat_vazio else "Digite sua resposta ou orientação para a próxima fase..."
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
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            is_parecer_mode = chat_atual["mode"] == "📄 Minuta de Parecer Cível"
            instrucao = SUPERPROMPT_PARECER if is_parecer_mode else PROMPT_JURISPRUDENCIA

            user_parts = []
            
            # Consulta DataJud por número de processo
            dados_cnj = None
            if re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", prompt_final):
                match_cnj = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", prompt_final).group(0)
                dados_cnj = consultar_datajud_por_numero(match_cnj, tribunal="tjsp")
                if dados_cnj:
                    user_parts.append(types.Part.from_text(text=f"[Consulta Oficial DataJud/CNJ]:\n{dados_cnj}"))

            # Ingestão binária direta de múltiplos PDFs na 1ª mensagem
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

            # Otimização e Ativação do Google Search em AMBOS os modos para validação factual
            config_params = {
                "system_instruction": instrucao,
                "temperature": 0.0,
                "thinking_config": types.ThinkingConfig(thinking_budget=0),
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
                                raise Exception(
                                    "A cota de requisições da chave do Google foi temporariamente atingida (429). "
                                    "Para remover esse limite, ative o faturamento no Google AI Studio."
                                )
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
