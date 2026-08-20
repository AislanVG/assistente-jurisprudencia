import streamlit as st
import requests
import json
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página (Estilo Jus IA)
# ----------------------------------------------------
st.set_page_config(
    page_title="Assistente de Jurisprudência IA",
    page_icon="⚖️",
    layout="wide"
)

# ----------------------------------------------------
# 2. Carregamento Automático e Invisível das Chaves
# ----------------------------------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
CNJ_API_KEY = st.secrets.get("CNJ_API_KEY")

if not GEMINI_API_KEY:
    st.error("⚠️ Chave de API não configurada nos Secrets do servidor.")
    st.stop()

# ----------------------------------------------------
# 3. Barra Lateral Limpa (Apenas Filtros Jurídicos)
# ----------------------------------------------------
with st.sidebar:
    st.title("⚖️ Filtros de Jurisprudência")
    
    fonte_escolhida = st.selectbox(
        "Base Jurisprudencial:",
        [
            "STF e STJ (Tribunais Superiores)",
            "STF - Supremo Tribunal Federal",
            "STJ - Superior Tribunal de Justiça",
            "DataJud / CNJ (TJs e TRFs)"
        ]
    )

    tribunal_datajud = "tjsp"
    if fonte_escolhida == "DataJud / CNJ (TJs e TRFs)":
        tribunal_datajud = st.selectbox(
            "Tribunal Estadual / Federal:",
            ["tjsp", "tjrj", "tjmg", "tjrs", "tjpr", "tjsc", "trf1", "trf2", "trf3", "trf4", "trf5"]
        )

    st.divider()
    if st.button("🗑️ Nova Consulta / Limpar Chat"):
        st.session_state.messages = []
        st.rerun()

# ----------------------------------------------------
# 4. Ferramenta de Consulta DataJud
# ----------------------------------------------------
def consultar_processos_datajud(termo_busca: str, sigla_tribunal: str = "tjsp") -> str:
    """Consulta processos ativos e movimentações no DataJud/CNJ."""
    if not CNJ_API_KEY:
        return "Chave do DataJud não configurada no servidor."

    tribunal_limpo = sigla_tribunal.lower().strip()
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal_limpo}/_search"
    headers = {"Authorization": f"APIKey {CNJ_API_KEY}", "Content-Type": "application/json"}

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
# 5. Interface Principal de Chat
# ----------------------------------------------------
st.header("⚖️ Consulta Jurisprudencial Inteligente")
st.caption(f"Foco ativo: **{fonte_escolhida}**" + (f" ({tribunal_datajud.upper()})" if fonte_escolhida == "DataJud / CNJ (TJs e TRFs)" else ""))

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ex.: Pesquise jurisprudência sobre responsabilidade civil do Estado por erro médico..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analisando precedentes, ementas e teses vinculantes..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                # Instrução estruturada no padrão do Jus IA
                instrucoes = (
                    "Você é um consultor jurídico sênior especializado em pesquisa jurisprudencial analítica. "
                    f"Base prioritária selecionada: '{fonte_escolhida}'.\n\n"
                    "REGRAS DE FORMATAÇÃO E ESTRUTURA (ESTILO PARECER JURÍDICO):\n"
                    "Estruture rigorosamente sua resposta nas seguintes seções:\n\n"
                    "### 📌 Tese Jurídica Central\n"
                    "Apresente em 1 ou 2 frases qual é o ponto decisivo exigido pelos tribunais (nexo causal, requisitos objetivos, ônus da prova).\n\n"
                    "### ⚖️ Precedentes Favoráveis\n"
                    "Liste de 2 a 4 decisões favoráveis, no formato exato:\n"
                    "* **[Tribunal] – [Classe Processual] nº [Número do Processo]**: [Resumo fático em 2 linhas explicando por que houve procedência]. [Link Oficial/Fonte]\n\n"
                    "### 🛑 Precedentes Desfavoráveis ou Restritivos\n"
                    "Apresente 1 ou 2 decisões contrárias, demonstrando em quais circunstâncias o pedido costuma ser rejeitado.\n\n"
                    "### 📋 Critérios Objetivos Extraídos dos Julgados\n"
                    "Enumere os requisitos práticos indispensáveis para o acolhimento da tese.\n\n"
                    "### 🏛️ Precedentes Vinculantes (STF / STJ)\n"
                    "Indique se há Súmula, Tema de Repercussão Geral (STF) ou Recurso Repetitivo (STJ) aplicável.\n\n"
                    "### 📝 Sugestão de Ementa para Cópia\n"
                    "Forneça o trecho mais representativo de uma das ementas dentro de um bloco de citação pronto para uso em petições."
                )

                if fonte_escolhida == "DataJud / CNJ (TJs e TRFs)":
                    ferramentas = [consultar_processos_datajud]
                    prompt_envio = f"[Tribunal: {tribunal_datajud}] {prompt}"
                else:
                    ferramentas = [types.Tool(google_search=types.GoogleSearch())]
                    prompt_envio = f"[Base Prioritária: {fonte_escolhida}] {prompt}"

                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=instrucoes,
                        tools=ferramentas,
                        temperature=0.1
                    )
                )

                response = chat.send_message(prompt_envio)
                texto_resposta = response.text

                st.markdown(texto_resposta)
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})

            except Exception as e:
                st.error(f"Erro ao processar consulta: {str(e)}")
