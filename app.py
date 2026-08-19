import streamlit as st
import requests
import json
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página
# ----------------------------------------------------
st.set_page_config(
    page_title="Assistente de Jurisprudência IA",
    page_icon="⚖️",
    layout="wide"
)

# ----------------------------------------------------
# 2. Barra Lateral (Credenciais e Fontes)
# ----------------------------------------------------
with st.sidebar:
    st.title("⚖️ Painel de Configuração")
    st.markdown("Defina a base prioritária de pesquisa:")

    gemini_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else st.text_input(
        "Gemini API Key", type="password", help="Chave obtida no Google AI Studio"
    )
    cnj_key = st.secrets.get("CNJ_API_KEY") if "CNJ_API_KEY" in st.secrets else st.text_input(
        "DataJud / CNJ API Key (Opcional)", type="password", help="Chave pública do DataJud"
    )

    st.divider()

    fonte_escolhida = st.selectbox(
        "Base Jurisprudencial Prioritária:",
        [
            "STF - Supremo Tribunal Federal",
            "STJ - Superior Tribunal de Justiça",
            "STF e STJ (Tribunais Superiores)",
            "DataJud / CNJ (TJs e TRFs)"
        ]
    )

    tribunal_datajud = "tjsp"
    if fonte_escolhida == "DataJud / CNJ (TJs e TRFs)":
        tribunal_datajud = st.selectbox(
            "Selecione o Tribunal (DataJud):",
            ["tjsp", "tjrj", "tjmg", "tjrs", "tjpr", "tjsc", "trf1", "trf2", "trf3", "trf4", "trf5"]
        )

    st.divider()
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# ----------------------------------------------------
# 3. Ferramenta para Consulta ao DataJud
# ----------------------------------------------------
def consultar_processos_datajud(termo_busca: str, sigla_tribunal: str = "tjsp") -> str:
    """
    Consulta processos e movimentações no DataJud/CNJ (TJs e TRFs).
    """
    if not cnj_key:
        return "Chave do DataJud/CNJ não informada."

    tribunal_limpo = sigla_tribunal.lower().strip()
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal_limpo}/_search"
    headers = {"Authorization": f"APIKey {cnj_key}", "Content-Type": "application/json"}

    payload = {
        "size": 5,
        "query": {"match": {"assuntos.nome": termo_busca}}
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            hits = response.json().get("hits", {}).get("hits", [])
            if not hits:
                return f"Nenhum processo localizado no {sigla_tribunal.upper()} para '{termo_busca}'."

            resultados = []
            for item in hits:
                fonte = item.get("_source", {})
                assuntos = [a.get("nome") for a in fonte.get("assuntos", []) if a.get("nome")]
                resultados.append({
                    "numeroProcesso": fonte.get("numeroProcesso"),
                    "classe": fonte.get("classe", {}).get("nome"),
                    "tribunal": fonte.get("tribunal"),
                    "orgaoJulgador": fonte.get("orgaoJulgador", {}).get("nome"),
                    "dataAjuizamento": fonte.get("dataAjuizamento"),
                    "assuntos": assuntos[:3]
                })
            return json.dumps(resultados, ensure_ascii=False)
        return f"Erro DataJud ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro de conexão com DataJud: {str(e)}"

# ----------------------------------------------------
# 4. Interface Principal de Chat
# ----------------------------------------------------
st.header("⚖️ Consulta Jurisprudencial com IA")
st.info(f"📍 Foco Selecionado: **{fonte_escolhida}**")

if not gemini_key:
    st.warning("👈 Insira sua **Gemini API Key** na barra lateral para começar.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ex.: Qual o entendimento do STJ sobre apropriação indébita tributária?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Buscando jurisprudência atualizada e acórdãos..."):
            try:
                client = genai.Client(api_key=gemini_key)

                instrucoes = (
                    "Você é um especialista em pesquisa jurisprudencial brasileira. "
                    f"O usuário definiu foco na base: '{fonte_escolhida}'. "
                    "Utilize a ferramenta de busca do Google para encontrar teses consolidadas, súmulas, "
                    "temas de repercussão geral (STF), recursos repetitivos (STJ) e acórdãos oficiais. "
                    "Sempre cite os números dos temas, súmulas ou julgados e apresente a fundamentação com clareza."
                )

                # Ativa o Google Search nativo da API do Gemini + DataJud
                ferramentas = [
                    types.Tool(google_search=types.GoogleSearch()),
                    consultar_processos_datajud
                ]

                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=instrucoes,
                        tools=ferramentas,
                        temperature=0.1
                    )
                )

                prompt_completo = f"[Base Prioritária: {fonte_escolhida}] {prompt}"
                response = chat.send_message(prompt_completo)
                texto_resposta = response.text

                st.markdown(texto_resposta)
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})

            except Exception as e:
                st.error(f"Erro na pesquisa: {str(e)}")
