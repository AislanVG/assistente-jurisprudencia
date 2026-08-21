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
    page_title="JusAssist MPMS",
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
    
    div[data-testid="stSidebar"] button[kind="primary"],
    div.stButton > button[kind="primary"] {
        border-radius: 8px !important;
        font-size: 16px !important;
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

    div[data-testid="stSidebar"] button[kind="secondary"],
    div.stButton > button[kind="secondary"] {
        border-radius: 8px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
    }
    div[data-testid="stSidebar"] button[kind="secondary"]:hover,
    div.stButton > button[kind="secondary"]:hover {
        border-color: #94a3b8 !important;
        background-color: #ffffff !important;
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
        font-size: 15px;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 18px;
        margin-bottom: 12px;
        text-align: center;
    }

    .main-chat-container {
        padding-bottom: 100px;
    }

    .action-bar {
        margin-top: 8px;
        margin-bottom: 16px;
    }

    /* CARD DE LOGIN EXCLUSIVO E UNIFICADO */
    .auth-unified-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 32px 36px 24px 36px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.06), 0 8px 10px -6px rgba(15, 23, 42, 0.03);
        text-align: center;
        max-width: 490px;
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
        gap: 10px;
        margin-bottom: 22px;
    }
    
    .pill {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        color: #334155;
        font-size: 13px;
        font-weight: 600;
        padding: 5px 12px;
        border-radius: 6px;
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
    col_l1, col_l2, col_l3 = st.columns([1, 1.35, 1])
    with col_l2:
        st.markdown(
            """
            <div class="auth-unified-card">
                <div class="auth-badge">4ª Procuradoria de Justiça Cível • MPMS</div>
                <div class="auth-title">⚖️ JusAssist MPMS</div>
                <div class="auth-subtitle">
                    Ecossistema de Inteligência Jurídica: Pesquisa Analítica de Precedentes e Elaboração de Pareceres de 2º Grau
                </div>
                <div class="feature-pills">
                    <span class="pill">🔍 Jurisprudência STF/STJ/TJMS</span>
                    <span class="pill">📄 Minutas Densas (6-10 págs)</span>
                </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("form_login"):
            email = st.text_input("E-mail cadastrado", placeholder="usuario@mpms.mp.br")
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
                    🔒 <strong>Acesso Restrito & Criptografado</strong> • Gabinete Dra. Luciana Moreira Schenk
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
            "mode": "📄 Minuta de Parecer (MPMS)",
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
def consultar_datajud_por_numero(numero_processo: str, tribunal: str = "tjms"):
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
1. ADERÊNCIA ESTRITA AOS AUTOS: Baseie sua análise EXCLUSIVAMENTE nos fatos e documentos do caso concreto anexado pelo usuário. É PROIBIDO inventar ou misturar matérias fáticas estranhas ao processo.
2. PRECEDENTES REAIS: Indique precedentes consolidados, números de REsps, Temas Vinculantes e acórdãos REAIS do STF, STJ e TJMS aplicáveis à matéria dos autos. Proibido inventar números ou ementas.
3. TRAVA DE HIERARQUIA: Precedentes das Turmas do STJ e teses vinculantes do STF prevalecem sobre atos administrativos ou pareceres técnicos.
4. RELATÓRIO SUCINTO INSTITUCIONAL: Máximo 500 palavras, fluido em parágrafos encadeados por verbos de ligação ("Alega o apelante que..."), SEM TÓPICOS/BULLETS, finalizando com a fórmula padrão de admissibilidade.
5. ESTILO: Expressões latinas em itálico (*in re ipsa*, *tempus regit actum*). Jurisprudências citadas em bloco recuado (`>`), em itálico.

### 🔄 FLUXO PROGRESSIVO OBRIGATÓRIO EM 3 ETAPAS:

- ETAPA 1 (Diagnóstico & Precedentes Aplicáveis):
  Apresente o Raio-X dos autos (Fatos reais do processo, Preliminares mapeadas, Dispositivos legais envolvidos).
  Apresente a linha de precedentes do STJ/STF/TJMS consolidada para a matéria.
  Ao final, faça a PERGUNTA OBRIGATÓRIA: "Deseja aplicar os precedentes acima sugeridos ou indicar outro julgado específico?" e PARE AQUI.

- ETAPA 2 (Ementa Técnica e Relatório Institucional):
  Quando o analista aprovar ou orientar a tese, elabore a Ementa Técnica Formal (com as palavras-chave da matéria dos autos e opinião final) e o Relatório Sucinto Fluido (máximo 500 palavras, corrido).
  Ao final, diga: "Aguardando validação da Ementa e Relatório para gerar a Minuta Integral (Etapa 3)." e PARE AQUI.

- ETAPA 3 (Minuta Integral de Alta Densidade - Peça Completa):
  Quando o analista responder "validado", "aprovado" ou "prossiga", REDIJA IMEDIATAMENTE A PEÇA COMPLETA DE SEGUNDO GRAU, sem cortes e sem placeholders:
  Cabeçalho Oficial (Autos, Classe, Órgão Julgador, Relator, Partes), Ementa Formal, "COLENDA CÂMARA CÍVEL,", Relatório, I – Das Preliminares (se houver), II – Do Mérito (Fundamentação exaustiva e densa de 2.500 a 4.000 palavras, enfrentando todas as teses dos autos com doutrina e precedentes), III – Conclusão (Opinamento formal), Datação (Campo Grande/MS) e Assinatura institucional de Luciana Moreira Schenk. NÃO REINICIE O FLUXO.
"""

# ----------------------------------------------------
# 10. Feed de Precedentes (Cache 12h)
# ----------------------------------------------------
@st.cache_data(ttl=43200)
def carregar_feed_precedentes():
    return [
        {"tribunal": "STJ", "tema": "Tema Repetitivo 1.082/STJ (Saúde Suplementar)", "desc": "Custeio de tratamento multidisciplinar (método ABA) para beneficiário com TEA e nulidade de cláusula limitativa."},
        {"tribunal": "STJ", "tema": "REsp 2.221.399/SP (3ª Turma - Direito Privado)", "desc": "Dever das operadoras de plano de saúde em fornecer cobertura de terapias especiais prescritas por médico assistente."},
        {"tribunal": "STJ", "tema": "Tema Repetitivo 290/STJ (Fraude à Execução)", "desc": "Marco temporal e requisitos da LC 118/2005 para caracterização de fraude à execução fiscal e terceiro de boa-fé."},
        {"tribunal": "STF", "tema": "Tema 793/STF (Repercussão Geral)", "desc": "Responsabilidade solidária dos entes federados no fornecimento de medicamentos e tratamentos pelo SUS."},
        {"tribunal": "STF", "tema": "Tema 1.234/STF (Medicamentos sem Registro)", "desc": "Critérios vinculantes de competência e legitimidade para fornecimento judicial de fármacos de alto custo."},
        {"tribunal": "STF", "tema": "Súmula Vinculante 510/STF (Delegação Registral)", "desc": "Cabimento de Mandado de Segurança contra atos praticados por delegatários de serviços notariais e de registro."}
    ]

# ----------------------------------------------------
# 11. Modais de Ajuda & Feedback
# ----------------------------------------------------
@st.dialog("📖 Central de Ajuda & Manual Operacional (MPMS)", width="large")
def exibir_manual_ajuda():
    st.markdown("## ⚖️ Manual Operacional: JusAssist MPMS")
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
            "O assistente é rigorosamente calibrado para atuar como Assessor Jurídico Sênior da 4ª Procuradoria de Justiça Cível do MPMS, "
            "elaborando peças densas e completas com meta real de **6 a 10 páginas (2.500 a 4.000 palavras)** no corpo da minuta."
        )
        st.markdown(
            """
1. **Passo 1: Upload dos Autos (Múltiplos PDFs)**
   * Na barra lateral, selecione **📄 Parecer** e anexe as peças necessárias (Inicial, Sentença, Apelação, Laudos).
2. **Passo 2: Início da Análise**
   * Clique em `⚡ Analisar autos e gerar parecer completo` ou use o botão na barra lateral.
3. **Passo 3: Diagnóstico Fático & Precedentes (Fase 2)**
   * A IA apresentará o raio-x e indicará os precedentes aplicáveis do STJ/STF/TJMS.
4. **Passo 4: Validação da Ementa e Relatório (Fase 3)**
   * Responda `Aprovado` para gerar a Ementa Técnica e o Relatório Fluido (até 500 palavras, sem marcadores).
5. **Passo 5: Minuta Final de Alta Densidade (Fase 4)**
   * Responda `Validado, prossiga` para a IA entregar a minuta completa pronta para exportação.
            """
        )
        st.info("💡 **Dica de Exportação:** Copie o texto da resposta final e cole no Microsoft Word mantendo a formatação de origem (Ctrl + V).")

    with tab2:
        st.markdown("### 🔍 Pesquisa Jurisprudencial Analítica")
        st.markdown("Varredura em tempo real integrada ao Google Search e à **API do DataJud (CNJ)**.")
        st.markdown("#### Exemplos Práticos de Pesquisa:")
        st.code("Qual o entendimento do STJ sobre responsabilidade do Estado por erro médico que causa sequelas em menor?", language="text")
        st.code("0845374-56.2024.8.12.0001 (Consulta direta ao DataJud/TJMS)", language="text")

    with tab3:
        st.markdown("### 🛡️ Mecanismos de Blindagem Institucional")
        st.markdown(
            """
* **Prevalência STJ/STF:** Precedentes de Turmas do STJ e STF sobrepõem-se a notas do e-NATJus ou conselhos.
* **Aderência aos Autos:** Foco restrito aos documentos do processo anexado.
* **Trava Anti-Alucinação:** Pesquisa ativa em bases oficiais, sem inventar julgados.
* **Relatório Padrão Ouro:** Narrativa fluida e encadeada de até 500 palavras, estritamente sem tópicos.
            """
        )

    with tab4:
        st.markdown("### 🛑 Comandos de Ajuste de Rota (Se não aprovar)")
        st.markdown("**1. Correção de Tese na Fase 2 (Diagnóstico):**")
        st.code("Não está aprovado. Na proposta de mérito, considere que a 3ª Turma do STJ já pacificou o dever de custeio pelo REsp 2.221.399/SP. Reformule a Fase 2 opinando pelo desprovimento do recurso.", language="text")
        st.markdown("**2. Avanço Direto:**")
        st.code("Aprovado o diagnóstico e os precedentes sugeridos. Prossiga para a emissão da Fase 3 e da Minuta Completa.", language="text")

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
# 12. Barra Lateral
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### ⚖️ **JusAssist MPMS**")
    st.caption(f"Usuário: **{st.session_state.user_session.email}**")
    
    col_u1, col_u2 = st.columns([1, 1])
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
        is_parecer = chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
        if st.button("📄 Parecer", key="btn_p", type="primary" if is_parecer else "secondary", use_container_width=True):
            chat_atual["mode"] = "📄 Minuta de Parecer (MPMS)"
            st.rerun()
    with col_m2:
        is_juris = chat_atual["mode"] == "🔍 Pesquisa de Jurisprudência"
        if st.button("🔍 Pesquisa", key="btn_j", type="primary" if is_juris else "secondary", use_container_width=True):
            chat_atual["mode"] = "🔍 Pesquisa de Jurisprudência"
            st.rerun()

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
                st.session_state["trigger_prompt"] = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes."
                st.rerun()

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
# 13. Horário Local (MS / Brasília)
# ----------------------------------------------------
try:
    fuso_ms = ZoneInfo("America/Campo_Grande")
    hora_local = datetime.now(fuso_ms).hour
except Exception:
    hora_local = (datetime.utcnow().hour - 4) % 24

if hora_local < 12:
    saudacao = "Qual é o caso da manhã?"
elif hora_local < 18:
    saudacao = "Qual é o caso da tarde?"
else:
    saudacao = "Qual é o caso da noite?"

# ----------------------------------------------------
# 14. Área Principal: Estado Inicial vs. Conversação
# ----------------------------------------------------
if chat_vazio:
    st.markdown(f"<div class='hero-title'>{saudacao}</div>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([0.5, 3.5, 0.5])
    with col_c2:
        if chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)":
            if uploaded_files:
                if st.button("⚡ Analisar autos e gerar parecer completo", key="sug_parecer", use_container_width=True, type="primary"):
                    st.session_state["trigger_prompt"] = "Analise integralmente o conjunto das peças processuais anexadas e elabore o diagnóstico da Etapa 1 com a pesquisa de precedentes."
                    st.rerun()
                if st.button("💬 Mapear apenas preliminares e teses recursais dos autos", key="sug_teses", use_container_width=True):
                    st.session_state["trigger_prompt"] = "Faça um mapeamento analítico das preliminares e das principais teses recursais cabíveis para o caso."
                    st.rerun()
            else:
                st.info("📂 Anexe os arquivos PDF na barra lateral para iniciar a análise dos autos.")
        
        else:
            st.markdown("<div class='feed-header'>🏛️ Precedentes Recentes dos Tribunais Superiores (Direito Privado / Cível)</div>", unsafe_allow_html=True)
            feed_precedentes = carregar_feed_precedentes()
            col_f1, col_f2 = st.columns(2)
            for idx, prec in enumerate(feed_precedentes):
                col_alvo = col_f1 if idx % 2 == 0 else col_f2
                with col_alvo:
                    rotulo_btn = f"📌 **[{prec['tribunal']}]** {prec['tema']}\n\n_{prec['desc']}_"
                    if st.button(rotulo_btn, key=f"prec_{idx}", use_container_width=True):
                        st.session_state["trigger_prompt"] = f"Apresente uma análise jurisprudencial analítica e aprofundada sobre o seguinte precedente do {prec['tribunal']}: {prec['tema']}. Foco na tese jurídica, critérios práticos e ementa representativa."
                        st.rerun()

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
                        file_name=f"Parecer_MPMS_{i}.txt",
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
# 15. Processamento de Mensagens com Streaming Seguro
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

            is_parecer_mode = chat_atual["mode"] == "📄 Minuta de Parecer (MPMS)"
            instrucao = SUPERPROMPT_PARECER if is_parecer_mode else PROMPT_JURISPRUDENCIA

            user_parts = []
            
            # Consulta DataJud por número de processo
            dados_cnj = None
            if not is_parecer_mode and re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", prompt_final):
                match_cnj = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", prompt_final).group(0)
                dados_cnj = consultar_datajud_por_numero(match_cnj, tribunal="tjms")
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

            # Otimização de latência ultra-baixa
            config_params = {
                "system_instruction": instrucao,
                "temperature": 0.1,
                "thinking_config": types.ThinkingConfig(thinking_budget=0)
            }

            if not is_parecer_mode:
                config_params["tools"] = [types.Tool(google_search=types.GoogleSearch())]

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
