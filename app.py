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
import streamlit.components.v1 as components

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
# 4. Injeção de CSS Forense e Bloco de Bastidores
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

    /* ESTILO VISUAL DE PEÇA FORENSE DO WORD / MINISTÉRIO PÚBLICO */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 28px 36px !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05) !important;
    }

    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] {
        font-family: "Georgia", "Times New Roman", Times, serif !important;
        font-size: 16px !important;
        line-height: 1.7 !important;
        color: #111827 !important;
    }

    /* Cabeçalho do Processo em Linhas Isoladas */
    .doc-header-block {
        margin-bottom: 24px;
        line-height: 1.55;
        font-size: 15.5px;
    }
    .doc-header-line {
        margin-bottom: 4px;
    }
    .doc-header-line strong {
        color: #0f172a;
    }

    /* Ementa Recuada à Direita */
    .doc-ementa {
        margin-left: 35% !important;
        margin-right: 0 !important;
        margin-top: 20px !important;
        margin-bottom: 28px !important;
        font-size: 13.5px !important;
        line-height: 1.45 !important;
        text-align: justify !important;
        text-justify: inter-word !important;
        color: #1e293b !important;
    }

    /* Vocativo Forense Centralizado */
    .doc-vocativo {
        text-align: center !important;
        font-size: 16px !important;
        font-weight: bold !important;
        margin-top: 26px !important;
        margin-bottom: 22px !important;
        letter-spacing: 0.5px !important;
    }

    /* Parágrafos de Conteúdo com Recuo de Primeira Linha */
    .doc-p {
        text-indent: 2.2em;
        text-align: justify !important;
        text-justify: inter-word !important;
        margin-bottom: 16px !important;
    }

    .doc-section-title {
        font-size: 16px !important;
        font-weight: bold !important;
        margin-top: 24px !important;
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
</style>
"""
st.markdown(css_customizado, unsafe_allow_html=True)

# ----------------------------------------------------
# 5. Fluxo de Autenticação Seguro (JurisPrime AI - MPMS)
# ----------------------------------------------------
if "user_session" not in st.session_state:
    st.session_state.user_session = None

if not st.session_state.user_session:
    components.html("""
        <script>
        try {
            const parentDoc = window.parent.document;
            const script = parentDoc.createElement('script');
            script.innerHTML = `
                if (window.location.hash.includes('access_token=')) {
                    var hash = window.location.hash.substring(1);
                    window.location.replace(window.location.pathname + '?' + hash);
                }
            `;
            parentDoc.head.appendChild(script);
        } catch (e) {
            if (window.parent.location.hash.includes('access_token=')) {
                var hash = window.parent.location.hash.substring(1);
                window.parent.location.replace(window.parent.location.pathname + '?' + hash);
            }
        }
        </script>
    """, height=0)
    
    token = st.query_params.get("access_token")
    refresh = st.query_params.get("refresh_token")
    
    if token and refresh:
        try:
            res = supabase.auth.set_session(token, refresh)
            if res.user:
                st.session_state.user_session = res.user
                st.query_params.clear()
                st.rerun()
        except Exception:
            pass

def exibir_tela_autenticacao():
    oauth_url = f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=https://jurisprimeai.streamlit.app/"

    st.markdown("""<style>
.block-container { max-width: 1350px !important; padding-top: 0.5rem !important; padding-bottom: 0 !important; }
.stApp { background-color: #ffffff !important; overflow: hidden !important; }
.auth-right-panel { background: linear-gradient(135deg, #0B132B 0%, #0F172A 100%); border-radius: 20px; padding: 32px 28px; color: white; height: 84vh; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.25); position: relative; overflow: hidden; margin-top: 8px; }
.auth-right-panel::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(56,189,248,0.1) 0%, transparent 60%); pointer-events: none; }

.google-btn-link {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
    font-size: 14px;
    font-weight: 600;
    color: #1e293b !important;
    background: #ffffff;
    cursor: pointer;
    text-decoration: none !important;
    transition: all 0.2s;
    margin-bottom: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.google-btn-link:hover { background: #f8fafc; border-color: #cbd5e1; }

.auth-divider { display: flex; align-items: center; text-align: center; color: #94a3b8; font-size: 11px; margin: 12px 0; text-transform: lowercase; }
.auth-divider::before, .auth-divider::after { content: ''; flex: 1; border-bottom: 1px solid #e2e8f0; }
.auth-divider:not(:empty)::before { margin-right: 1em; }
.auth-divider:not(:empty)::after { margin-left: 1em; }

div[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; box-shadow: none !important; }
div[data-testid="stForm"] button[kind="primary"] { background-color: #1e3a8a !important; border-color: #1e3a8a !important; color: white !important; width: 100% !important; border-radius: 8px !important; font-weight: 600 !important; height: 44px !important; margin-top: 6px !important; }
div[data-testid="stForm"] button[kind="primary"]:hover { background-color: #2563eb !important; border-color: #2563eb !important; }
div[data-testid="stTextInput"] input { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; color: #1e293b !important; padding: 8px 12px !important; }
div[data-testid="stTextInput"] { margin-bottom: -10px !important; }
</style>""", unsafe_allow_html=True)
    
    col1, espaco, col2 = st.columns([1.1, 0.15, 1.2])
    
    with col1:
        st.markdown("<h1 style='text-align: center; color: #0f172a; font-weight: 800; font-size: 30px; line-height: 1.15; margin-top: 10px; margin-bottom: 8px;'>Sua rotina jurídica<br>mais eficiente</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #475569; font-size: 13.5px; margin-bottom: 16px;'>Faça login ou acesse com sua conta institucional</p>", unsafe_allow_html=True)
        
        st.markdown(f'''
            <a href="{oauth_url}" target="_blank" rel="noopener noreferrer" class="google-btn-link">
                <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
                Acessar com o Google
            </a>
        ''', unsafe_allow_html=True)
        
        st.markdown('<div class="auth-divider">ou</div>', unsafe_allow_html=True)
        
        with st.form("form_login"):
            email = st.text_input("E-mail *", placeholder="seu@email.com")
            senha = st.text_input("Senha *", type="password", placeholder="••••••••")
            btn_entrar = st.form_submit_button("Continuar com e-mail ➔", use_container_width=True)
            
            if btn_entrar:
                if not email or not senha:
                    st.warning("Por favor, preencha o e-mail e a senha.")
                elif not supabase:
                    st.error("Credenciais do Supabase não configuradas.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                        if res.user:
                            st.session_state.user_session = res.user
                            st.rerun()
                    except Exception:
                        st.error("E-mail ou senha incorretos.")

        st.markdown("<p style='text-align: center; font-size: 11px; color: #64748b; margin-top: 14px; margin-bottom: 0px;'>Ambiente Seguro • Acesso Restrito aos Membros e Assessores</p>", unsafe_allow_html=True)

    with col2:
        right_panel_html = (
            '<div class="auth-right-panel">'
            '<div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px; position: relative; z-index: 10;">'
            '<span style="font-size: 26px;">⚖️</span>'
            '<span style="font-size: 24px; font-weight: 800; color: white; letter-spacing: -0.5px;">JurisPrime <span style="color: #38BDF8;">AI</span></span>'
            '</div>'
            '<h2 style="text-align: center; font-size: 21px; font-weight: 800; line-height: 1.3; margin-bottom: 18px; position: relative; z-index: 10;">Inteligência Jurídica Especializada<br>em <span style="color: #38BDF8;">Segundo&nbsp;Grau</span></h2>'
            '<div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; padding: 16px 18px; position: relative; z-index: 10; backdrop-filter: blur(10px); display: flex; flex-direction: column; gap: 11px;">'
            '<div style="display: flex; align-items: flex-start; gap: 10px;">'
            '<span style="font-size: 17px;">📄</span>'
            '<div style="font-size: 14px; line-height: 1.4; color: #cbd5e1;"><strong style="color: white;">Pareceres Cíveis Densos (6 a 10 págs):</strong> Elaboração estruturada com cabeçalho oficial, ementa técnica e fundamentação exaustiva no padrão do TJMS e MPMS.</div>'
            '</div>'
            '<div style="display: flex; align-items: flex-start; gap: 10px;">'
            '<span style="font-size: 17px;">🔍</span>'
            '<div style="font-size: 14px; line-height: 1.4; color: #cbd5e1;"><strong style="color: white;">Jurisprudência Sem Alucinação:</strong> Varredura em tempo real no STF, STJ e TJMS com conferência exata de números de REsp, temas repetitivos e súmulas vinculantes.</div>'
            '</div>'
            '<div style="display: flex; align-items: flex-start; gap: 10px;">'
            '<span style="font-size: 17px;">🛡️</span>'
            '<div style="font-size: 14px; line-height: 1.4; color: #cbd5e1;"><strong style="color: white;">Auditoria Agêntica & Mentoria:</strong> Confronto probatório das minutas de assessores e estagiários com os autos, nota técnica e reestruturação integral.</div>'
            '</div>'
            '<div style="display: flex; align-items: flex-start; gap: 10px;">'
            '<span style="font-size: 17px;">🏛️</span>'
            '<div style="font-size: 14px; line-height: 1.4; color: #cbd5e1;"><strong style="color: white;">Conexão Direta DataJud (CNJ):</strong> Leitura automática de classes, órgãos julgadores e histórico de andamentos processuais.</div>'
            '</div>'
            '</div>'
            '<div style="text-align: center; margin-top: 14px; font-size: 11px; color: #94a3b8;">🔒 Infraestrutura Segura • Decoro Forense & Urbanidade Processual</div>'
            '</div>'
        )
        st.markdown(right_panel_html, unsafe_allow_html=True)

if not st.session_state.user_session:
    exibir_tela_autenticacao()
    st.stop()

# ----------------------------------------------------
# 6. Funções de Persistência Segura (PostgreSQL & Storage)
# ----------------------------------------------------
def carregar_historico_usuario(user_id: str):
    if not supabase or not user_id:
        return {}
    try:
        res_chats = supabase.table("atendimentos")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .limit(3)\
            .execute()
        
        if not res_chats.data:
            return {}
        
        chats_recuperados = {}
        for c in res_chats.data:
            cid = c["id"]
            res_msgs = supabase.table("mensagens_atendimento")\
                .select("*")\
                .eq("atendimento_id", cid)\
                .eq("user_id", user_id)\
                .order("created_at", desc=False)\
                .execute()
            
            res_files = supabase.table("arquivos_atendimento")\
                .select("file_name, file_path, file_size_kb")\
                .eq("atendimento_id", cid)\
                .eq("user_id", user_id)\
                .execute()

            mensagens = []
            gemini_history = []
            for m in res_msgs.data:
                mensagens.append({
                    "role": m["role"],
                    "content": m["content"],
                    "reasoning_steps": m.get("reasoning_steps") or []
                })
                gemini_history.append(
                    types.Content(
                        role="model" if m["role"] == "assistant" else "user",
                        parts=[types.Part.from_text(text=m["content"])]
                    )
                )

            chats_recuperados[cid] = {
                "title": c["title"],
                "mode": c["mode"],
                "messages": mensagens,
                "gemini_history": gemini_history,
                "saved_files": res_files.data or []
            }
        return chats_recuperados
    except Exception:
        return {}

def salvar_ou_atualizar_atendimento(chat_id: str, user_id: str, title: str, mode: str):
    if not supabase or not user_id:
        return
    try:
        data_payload = {
            "id": chat_id,
            "user_id": user_id,
            "title": title,
            "mode": mode,
            "updated_at": datetime.now(ZoneInfo("UTC")).isoformat()
        }
        supabase.table("atendimentos").upsert(data_payload).execute()
    except Exception:
        pass

def salvar_mensagem_banco(chat_id: str, user_id: str, role: str, content: str, reasoning_steps: list = None):
    if not supabase or not user_id:
        return
    try:
        payload = {
            "atendimento_id": chat_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "reasoning_steps": reasoning_steps or []
        }
        supabase.table("mensagens_atendimento").insert(payload).execute()
        supabase.table("atendimentos")\
            .update({"updated_at": datetime.now(ZoneInfo("UTC")).isoformat()})\
            .eq("id", chat_id)\
            .execute()
    except Exception:
        pass

def salvar_arquivos_storage(chat_id: str, user_id: str, arquivos_upload):
    if not supabase or not user_id or not arquivos_upload:
        return []
    arquivos_salvos = []
    for f in arquivos_upload:
        try:
            caminho_storage = f"{user_id}/{chat_id}/{f.name}"
            conteudo_bytes = f.getvalue()
            supabase.storage.from_("autos_processos").upload(
                path=caminho_storage,
                file=conteudo_bytes,
                file_options={"upsert": "true"}
            )
            tamanho_kb = round(len(conteudo_bytes) / 1024, 2)
            supabase.table("arquivos_atendimento").insert({
                "atendimento_id": chat_id,
                "user_id": user_id,
                "file_name": f.name,
                "file_path": caminho_storage,
                "file_size_kb": tamanho_kb
            }).execute()
            arquivos_salvos.append({"file_name": f.name, "file_path": caminho_storage, "file_size_kb": tamanho_kb})
        except Exception:
            continue
    return arquivos_salvos

# ----------------------------------------------------
# 7. Modal de Alteração de Senha
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
# 8. Gerenciamento de Sessões do Assistente com Banco
# ----------------------------------------------------
user_id_atual = st.session_state.user_session.id

if "chats" not in st.session_state:
    chats_db = carregar_historico_usuario(user_id_atual)
    if chats_db:
        st.session_state.chats = chats_db
        st.session_state.current_chat_id = list(chats_db.keys())[0]
    else:
        primeiro_id = str(uuid.uuid4())
        st.session_state.chats = {
            primeiro_id: {
                "title": "",
                "mode": "📄 Minuta de Parecer Cível",
                "messages": [],
                "gemini_history": [],
                "saved_files": []
            }
        }
        st.session_state.current_chat_id = primeiro_id

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chats:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

chat_atual = st.session_state.chats[st.session_state.current_chat_id]
chat_vazio = len(chat_atual["messages"]) == 0

# ----------------------------------------------------
# 9. Módulo de Integração com API DataJud (CNJ)
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
# 10. Prompts Especializados com Formatação Forense Rigorosa
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
Atue como Assessor Jurídico Sênior com atuação em Segundo Grau de Jurisdição (Cível). Seu objetivo é elaborar minutas de PARECER CÍVEL EM SEGUNDO GRAU completas, densas, fluidas e exaustivamente fundamentadas (meta real de 6 a 10 páginas / 2.500 a 4.000 palavras), com tom formal, erudito, sóbrio e cerebral, seguindo o padrão vernáculo e estilístico das manifestações de segundo grau.

### 🏛️ PADRÃO VERNÁCULO FORENSE, URBANIDADE E DECORO PROCESSUAL:
1. É TERMINANTEMENTE PROIBIDO O USO DE LINGUAGEM COLOQUIAL, RASTEIRA OU PERSONALISTA CONTRA O MAGISTRADO DE PRIMEIRO GRAU.
   - NUNCA escreva frases como: "o juiz cometeu um erro", "o magistrado se equivocou", "a decisão está errada", "o juiz não analisou os documentos".
   - A crítica deve ser IMPESSOAL, direcionada à DECISÃO/SENTENÇA:
     * Utilize fórmulas consagradas: "A r. sentença recorrida comporta reforma...", "Com a devida vênia ao entendimento esposado pelo d. Juízo singular...", "O decisum de piso merece reparo...", "O Apelante/Município parte da premissa correta, mas extrai consequência jurídica incorreta ao sustentar que...".
2. TRATAMENTO FORENSE: Trate o órgão de origem como "d. Juízo a quo", "d. Juízo singular", "r. sentença combatida/recorrida", e a instância recursal como "Colenda Câmara Cível", "E. Tribunal de Justiça", "ínclito Relator".

### 🎯 REGRA DE OURO: SOBERANIA DAS DIRETRIZES DO ASSESSOR (OBEDIÊNCIA ESTRITA)
1. DISTINÇÃO ENTRE 1º GRAU E 2º GRAU:
   - **Decisão do Juiz (1º Grau):** É a decisão ou sentença originária recorrida (objeto do recurso).
   - **Decisão do Desembargador Relator (2º Grau):** É a decisão monocrática liminar, tutela antecipada recursal ou efeito suspensivo deferido/indeferido no Tribunal de Justiça.
   - **COMANDO DO USUÁRIO:** Se o usuário responder "pelo desprovimento", "pelo provimento", "acompanhe o relator", ADOTE IMEDIATAMENTE essa orientação de mérito e avance sem pedir novas confirmações.
2. SOBERANIA TOTAL: A tese e orientação definidas pelo usuário no chat são ABSOLUTAS e VINCULANTES.

### 📜 ESTRUTURA VISUAL E FORMATAÇÃO HTML OBRIGATÓRIA (ESTILO WORD INSTITUCIONAL):
Ao gerar a Etapa 2 e a Etapa 3, UTILIZE ESTRITAMENTE as seguintes classes HTML para formatar o texto:

1. CABEÇALHO DO PROCESSO (Linhas isoladas e destacadas):
<div class="doc-header-block">
  <div class="doc-header-line"><strong>N.º MP:</strong> [Número do MP ou 'A ser preenchido']</div>
  <div class="doc-header-line"><strong>Autos n.º:</strong> [Número do Processo SAJ]</div>
  <div class="doc-header-line"><strong>Classe:</strong> [Apelação Cível / Agravo de Instrumento]</div>
  <div class="doc-header-line"><strong>Órgão Julgador:</strong> [Câmara Cível competente]</div>
  <div class="doc-header-line"><strong>Relator(a):</strong> [Nome do Relator]</div>
  <div class="doc-header-line"><strong>Apelante(s):</strong> [Nome da Parte Ativa]</div>
  <div class="doc-header-line"><strong>Apelado(s):</strong> [Nome da Parte Passiva]</div>
</div>

2. EMENTA TÉCNICA FORMAL (RECUADA À DIREITA, SEM TÍTULOS ARTIFICIAIS):
NÃO escreva "EMENTA TÉCNICA FORMAL". Insira a ementa diretamente na div com classe doc-ementa:
<div class="doc-ementa">
APELAÇÃO CÍVEL. AÇÃO DE OBRIGAÇÃO DE FAZER... [Palavras-chave em CAIXA ALTA separadas por pontos]. PRECEDENTES DO STF/STJ. <strong>PARECER PELO CONHECIMENTO E PROVIMENTO / DESPROVIMENTO / PARCIAL PROVIMENTO DO RECURSO.</strong>
</div>

3. VOCATIVO FORENSE:
<div class="doc-vocativo">COLENDA CÂMARA CÍVEL,</div>

4. RELATÓRIO DO RECURSO E CAPÍTULOS (SEM SUBTÍTULOS COMO 'RELATÓRIO DO RECURSO'):
Comece diretamente a narrativa do relatório em parágrafos justificados com recuo, contendo OBRIGATORIAMENTE os pedidos finais expressos da parte recorrente antes do fecho de admissibilidade:
<p class="doc-p">Trata-se de Apelação Cível / Agravo de Instrumento interposto por... em face da r. sentença / decisão interlocutória que...</p>
<p class="doc-p">[Resumo encadeado dos fatos e das razões recursais com verbos técnicos: "Sustenta o apelante que...", "Alega que...", "Afirma que..."]</p>
<p class="doc-p">Ao final, requer o recorrente o conhecimento e provimento do recurso [e/ou a concessão de tutela recursal / efeito suspensivo], a fim de que seja reformada a r. decisão combatida para [descrever os pedidos práticos pleiteados no recurso].</p>
<p class="doc-p">É o relatório.<br>O presente recurso é tempestivo e preenche os demais requisitos de admissibilidade, razão pela qual merece ser conhecido.</p>

<div class="doc-section-title">I – Da controvérsia recursal</div>
<p class="doc-p">A controvérsia recursal cinge-se a verificar/definir se...</p>

<div class="doc-section-title">II – Do mérito</div>
<p class="doc-p">[Desenvolvimento denso, contínuo e fundamentado (2.500 a 4.000 palavras)...]</p>

<div class="doc-section-title">III – Conclusão</div>
<p class="doc-p">Ante o exposto, esta Procuradoria de Justiça manifesta-se pelo conhecimento e provimento / desprovimento / parcial provimento do recurso.</p>

### 🔄 FLUXO PROGRESSIVO EM 3 ETAPAS:
- **ETAPA 1:** Apresente o Raio-X dos autos e a Pergunta de Validação da tese. PARE e aguarde a resposta do assessor.
- **ETAPA 2:** Quando o usuário responder com o sentido do parecer (ex: "pelo desprovimento", "sim", "confirmado", "prosseguir"), GERE IMEDIATAMENTE o Cabeçalho, a Ementa Recuada e o Relatório do Recurso no padrão HTML forense acima. PARE e aguarde o comando para gerar a Minuta Integral (Etapa 3).
- **ETAPA 3:** Quando o usuário autorizar ("prosseguir", "validado", "minuta final"), GERE A PEÇA COMPLETA DE SEGUNDO GRAU integralmente (2.500 a 4.000 palavras) sem qualquer placeholder.
"""

SUPERPROMPT_AUDITORIA = """
Atue como o Assessor Jurídico Sênior Auditor e Mentor Especializado em Segundo Grau de Jurisdição Cível. Seu objetivo é AUDITAR, AVALIAR e REVISAR exaustivamente as minutas de pareceres elaboradas por estagiários e assessores em formação, fornecendo um parecer técnico de revisão pedagógico, rigoroso, construtivo e totalmente livre de alucinações.

### 🏛️ PADRÃO VERNÁCULO FORENSE E DECORO PROCESSUAL
- Aponte como vício grave de redação qualquer linguagem coloquial, agressiva ou personalista que ataque a figura do magistrado (ex: "o juiz errou", "o juiz cometeu um erro").
- Recomende sempre construções jurídicas impessoais e eruditas (ex: "com a devida vênia ao entendimento firmado na origem, a r. decisão comporta reforma").

### 🛡️ TRAVA DE HIGIENE DE CONTEXTO E PREVENÇÃO DE CONTAMINAÇÃO PROCESSUAL
- Esta sessão destina-se EXCLUSIVAMENTE à análise, auditoria e redação do PROCESSO ATUAL.
- Se em qualquer momento o usuário tentar iniciar a análise de um NOVO PROCESSO dentro desta mesma conversa, PARE IMEDIATAMENTE e emita o aviso de abertura de Novo Atendimento.

### 🔄 FLUXO DE TRABALHO AGÊNTICO EM 3 FASES:
#### FASE 1: Identificação dos Autos e da Minuta Anexada nos arquivos.
#### FASE 2: Relatório de Auditoria, Nota (0 a 10), Tabela Gramatical de Português e Detecção de Alucinações de IA.
#### FASE 3: Minuta Integral Reestruturada (6 a 10 páginas / 2.500 a 4.000 palavras).
"""

# ----------------------------------------------------
# 11. Modais de Ajuda & Manual Operacional Completo
# ----------------------------------------------------
@st.dialog("📖 Central de Ajuda & Manual Operacional", width="large")
def exibir_manual_ajuda():
    st.markdown("## ⚖️ Manual Operacional: JurisPrime AI")
    st.caption("Guia Oficial para Pesquisa Jurisprudencial, Elaboração de Pareceres e Auditoria de Peças de 2º Grau")
    
    tab1, tab2, tab3 = st.tabs(["📄 Minuta de Parecer", "🛡️ Auditoria & Mentoria", "🔍 Pesquisa Jurisprudencial"])
    
    with tab1:
        st.markdown("### 🏛️ Elaboração de Pareceres de 2º Grau")
        st.markdown("""
        O módulo de **Pareceres Cíveis** opera com inteligência jurídica progressiva em 3 etapas para garantir controle total sobre a tese ministerial:

        * **Etapa 1 – Raio-X Probatório & Validação:**
          * Faça o upload dos PDFs dos autos (Petição Inicial, Sentença, Apelação, Contrarrazões, Laudos).
          * A IA realiza a leitura do acervo fático, mapeia os pedidos, sintetiza a controvérsia e faz uma pergunta objetiva de validação de tese.
        * **Etapa 2 – Ementa Técnica & Relatório do Recurso:**
          * Responda com a orientação de mérito desejada (*ex: 'pelo desprovimento', 'acompanhar o relator', 'pelo provimento parcial'*).
          * A IA gera o cabeçalho oficial do processo, a ementa técnica com recuo padrão e o relatório estruturado do recurso.
        * **Etapa 3 – Minuta Integral de Segundo Grau:**
          * Ao confirmar com *'prosseguir'* ou *'minuta final'*, a IA redige a peça completa e exaustiva (meta de 6 a 10 páginas / 2.500 a 4.000 palavras), com rigor vernáculo e precedentes vinculantes.
        
        **Regras de Redação:** Decoro forense absoluto, tratamento impessoal ao juízo de origem (*d. Juízo a quo, r. sentença recorrida*) e soberania estrita das instruções do usuário.
        """)

    with tab2:
        st.markdown("### 🛡️ Auditoria Agêntica & Mentoria Pedagógica")
        st.markdown("""
        Módulo desenvolvido para revisar e qualificar minutas elaboradas por estagiários, residentes e assessores em formação:

        * **Como Utilizar:**
          * Anexe na barra lateral os **PDFs dos Autos** conjuntamente com o **PDF da Minuta elaborada pelo assessor/estagiário**.
          * Clique em *'Iniciar Auditoria dos Autos e Minuta'*.
        * **Entregáveis da Auditoria (Fase 2):**
          * **Confronto Probatório:** Verificação se os fatos e valores citados na minuta realmente existem nos autos.
          * **Detecção de Alucinações:** Identificação de leis revogadas ou números de processos inexistentes.
          * **Tabela Gramatical e Vernáculo:** Correção de erros ortográficos, concordância e linguagem inadequada/coloquial.
          * **Nota Técnica (0 a 10):** Avaliação de maturidade jurídica da peça.
        * **Reestruturação Integral (Fase 3):**
          * A IA entrega a versão reescrita e aprimorada da peça (6 a 10 páginas), pronta para assinatura.
        """)

    with tab3:
        st.markdown("### 🔍 Pesquisa Jurisprudencial Analítica")
        st.markdown("""
        Módulo especializado em pesquisa em tempo real com **tolerância zero a precedentes fictícios**:

        * **Varredura Integrada:** Realiza buscas ao vivo no STF, STJ e Tribunais Estaduais/Regionais via Google Search.
        * **Integração com DataJud (CNJ):** Se você digitar o número de um processo no padrão CNJ (`0000000-00.0000.0.00.0000`), o sistema consulta a API oficial do DataJud e extrai automaticamente classe, vara e últimas movimentações.
        * **Estrutura do Relatório Jurisprudencial:**
          * Tese jurídica central e distribuição do ônus probatório.
          * Precedentes favoráveis e desfavoráveis (*distinguishing*).
          * Critérios objetivos exigidos pelos tribunais.
          * Súmulas e Temas Repetitivos vinculantes.
          * Sugestão de ementa oficial pronta para citação.
        """)

# ----------------------------------------------------
# 12. Barra Lateral (Menu Vertical Limpo e Otimizado)
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
            "gemini_history": [],
            "saved_files": []
        }
        st.session_state.current_chat_id = novo_id
        salvar_ou_atualizar_atendimento(novo_id, user_id_atual, "Novo Atendimento", chat_atual["mode"])
        st.rerun()

    st.markdown('<div class="sidebar-label">Modo de Operação</div>', unsafe_allow_html=True)
    
    is_parecer = chat_atual["mode"] == "📄 Minuta de Parecer Cível"
    if st.button("📄 Parecer Cível (2º Grau)", key="btn_mode_parecer", type="primary" if is_parecer else "secondary", use_container_width=True):
        chat_atual["mode"] = "📄 Minuta de Parecer Cível"
        salvar_ou_atualizar_atendimento(st.session_state.current_chat_id, user_id_atual, chat_atual["title"] or "Atendimento", chat_atual["mode"])
        st.rerun()

    is_audit = chat_atual["mode"] == "🛡️ Auditoria & Mentoria"
    if st.button("🛡️ Auditoria & Mentoria", key="btn_mode_audit", type="primary" if is_audit else "secondary", use_container_width=True):
        chat_atual["mode"] = "🛡️ Auditoria & Mentoria"
        salvar_ou_atualizar_atendimento(st.session_state.current_chat_id, user_id_atual, chat_atual["title"] or "Atendimento", chat_atual["mode"])
        st.rerun()

    is_juris = chat_atual["mode"] == "🔍 Pesquisa de Jurisprudência"
    if st.button("🔍 Pesquisa Jurisprudencial", key="btn_mode_pesquisa", type="primary" if is_juris else "secondary", use_container_width=True):
        chat_atual["mode"] = "🔍 Pesquisa de Jurisprudência"
        salvar_ou_atualizar_atendimento(st.session_state.current_chat_id, user_id_atual, chat_atual["title"] or "Atendimento", chat_atual["mode"])
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
        cid: cdata for cid, cdata in st.session_state.chats.items() if len(cdata["messages"]) > 0 or cdata.get("title")
    }

    if conversas_com_historico:
        st.markdown('<div class="sidebar-label">Últimos Atendimentos (Máx. 3)</div>', unsafe_allow_html=True)
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
                    if supabase:
                        try:
                            supabase.table("atendimentos").delete().eq("id", chat_id).eq("user_id", user_id_atual).execute()
                        except Exception:
                            pass
                    del st.session_state.chats[chat_id]
                    if st.session_state.current_chat_id == chat_id:
                        restantes = list(st.session_state.chats.keys())
                        st.session_state.current_chat_id = restantes[0] if restantes else str(uuid.uuid4())
                        if not restantes:
                            st.session_state.chats[st.session_state.current_chat_id] = {
                                "title": "", "mode": chat_atual["mode"], "messages": [], "gemini_history": [], "saved_files": []
                            }
                    st.rerun()

    st.markdown('<div class="help-section"></div>', unsafe_allow_html=True)
    if st.button("❓ Guia Operacional & Ajuda", use_container_width=True):
        exibir_manual_ajuda()

# ----------------------------------------------------
# 13. Área Principal: Telas Iniciais vs. Chat
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
            if msg["role"] == "assistant" and msg.get("reasoning_steps"):
                with st.expander("🧠 Bastidores da Análise & Raciocínio Agêntico", expanded=False):
                    for step in msg["reasoning_steps"]:
                        st.markdown(step)
            
            st.markdown(msg["content"], unsafe_allow_html=True)
            
            if msg["role"] == "assistant":
                st.markdown("<div class='action-bar'>", unsafe_allow_html=True)
                col_act1, col_act2 = st.columns([0.15, 0.85])
                with col_act1:
                    st.download_button(
                        label="📥 Baixar",
                        data=msg["content"],
                        file_name=f"JurisPrime_{i}.txt",
                        mime="text/plain",
                        key=f"dl_{i}",
                        help="Baixar este documento"
                    )
                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# 14. Processamento Seguro com Persistência Automática
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

    salvar_ou_atualizar_atendimento(st.session_state.current_chat_id, user_id_atual, chat_atual["title"], chat_atual["mode"])

    # Upload dos arquivos no storage se for a primeira mensagem
    if len(chat_atual["messages"]) == 0 and uploaded_files:
        arquivos_salvos = salvar_arquivos_storage(st.session_state.current_chat_id, user_id_atual, uploaded_files)
        chat_atual["saved_files"] = arquivos_salvos

    chat_atual["messages"].append({"role": "user", "content": prompt_final})
    salvar_mensagem_banco(st.session_state.current_chat_id, user_id_atual, "user", prompt_final)

    with st.chat_message("user"):
        st.markdown(prompt_final)

    with st.chat_message("assistant"):
        passos_executados = []
        
        qtd_msg = len(chat_atual["messages"])
        if qtd_msg <= 1:
            etiqueta_status = "⏳ Produzindo Raio-X dos Autos e Pesquisa de Precedentes (Etapa 1)..."
        elif qtd_msg <= 3:
            etiqueta_status = "⏳ Produzindo Cabeçalho, Ementa Técnica e Relatório do Recurso (Etapa 2)..."
        else:
            etiqueta_status = "⏳ Redigindo Minuta Integral de Segundo Grau de Alta Densidade (Etapa 3)..."

        with st.status(etiqueta_status, expanded=True) as status_box:
            p1 = "📂 **Leitura e extração minuciosa do acervo probatório dos autos**"
            st.write(p1)
            passos_executados.append(p1)

            p2 = "🔍 **Consulta ativa de jurisprudência e teses vinculantes no STF e STJ**"
            st.write(p2)
            passos_executados.append(p2)

            p3 = "✍️ **Estruturação da fundamentação jurídica e diagramação forense**"
            st.write(p3)
            passos_executados.append(p3)

            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                if chat_atual["mode"] == "🛡️ Auditoria & Mentoria":
                    instrucao = SUPERPROMPT_AUDITORIA
                elif chat_atual["mode"] == "📄 Minuta de Parecer Cível":
                    instrucao = SUPERPROMPT_PARECER
                else:
                    instrucao = PROMPT_JURISPRUDENCIA

                user_parts = []
                
                if re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", prompt_final):
                    match_cnj = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", prompt_final).group(0)
                    dados_cnj = consultar_datajud_por_numero(match_cnj, tribunal="tjsp")
                    if dados_cnj:
                        user_parts.append(types.Part.from_text(text=f"[Consulta Oficial DataJud/CNJ]:\n{dados_cnj}"))

                # Anexa binários em bytes na primeira mensagem da conversa
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
                    primeiro_chunk = True
                    for tentativa in range(3):
                        try:
                            response_stream = client.models.generate_content_stream(
                                model="gemini-2.5-flash",
                                contents=chat_atual["gemini_history"],
                                config=types.GenerateContentConfig(**config_params)
                            )
                            for chunk in response_stream:
                                if chunk.text:
                                    if primeiro_chunk:
                                        status_box.update(label="✅ Análise concluída com sucesso", state="complete", expanded=False)
                                        primeiro_chunk = False
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
                chat_atual["messages"].append({
                    "role": "assistant",
                    "content": texto_resposta,
                    "reasoning_steps": passos_executados
                })
                salvar_mensagem_banco(st.session_state.current_chat_id, user_id_atual, "assistant", texto_resposta, passos_executados)
                st.rerun()

            except Exception as e:
                status_box.update(label="❌ Erro no processamento", state="error", expanded=True)
                st.error(f"Erro no processamento da análise: {str(e)}")
