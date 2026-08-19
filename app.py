import streamlit as st
import requests
import json
from duckduckgo_search import DDGS
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página
# ----------------------------------------------------
st.set_page_config(page_title="Assistente Jurídico IA", page_icon="⚖️", layout="wide")

# ----------------------------------------------------
# 2. Barra Lateral (Credenciais e Configurações)
# ----------------------------------------------------
with st.sidebar:
    st.title("⚖️ Painel de Configuração")
    st.markdown("Insira suas chaves de API para iniciar.")
    
    gemini_key = st.text_input("Gemini API Key", type="password", help="Chave obtida no Google AI Studio")
    cnj_key = st.text_input("DataJud / CNJ API Key", type="password", help="Chave pública do DataJud")
    
    st.divider()
    tribunal_padrao = st.selectbox(
        "Tribunal padrão para o DataJud:",
        ["tjsp", "tjrj", "tjmg", "tjrs", "trf1", "trf2", "trf3", "trf4", "trf5"]
    )
    
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# ----------------------------------------------------
# 3. Ferramentas (Tools) para o Gemini
# ----------------------------------------------------
def buscar_jurisprudencia_stf_stj(termo_busca: str, tribunal: str = "ambos") -> str:
    """
    Busca ementas, súmulas e teses jurisprudenciais oficiais no STF e/ou STJ.
    
    Args:
        termo_busca: A tese, tema ou termo jurídico a ser pesquisado.
        tribunal: 'stf', 'stj' ou 'ambos'.
    """
    sites = []
    if tribunal.lower() == "stf":
        sites = ["site:jurisprudencia.stf.jus.br", "site:portal.stf.jus.br"]
    elif tribunal.lower() == "stj":
        sites = ["site:scon.stj.jus.br", "site:stj.jus.br/jurisprudencia"]
    else:
        sites = ["site:jurisprudencia.stf.jus.br", "site:scon.stj.jus.br", "site:portal.stf.jus.br"]

    query = f"({' OR '.join(sites)}) {termo_busca}"
    
    try:
        ddgs = DDGS()
        resultados = list(ddgs.text(query, max_results=5))
        if not resultados:
            return f"Nenhuma jurisprudência relevante encontrada nos tribunais superiores para: {termo_busca}"
        
        documentos = []
        for item in resultados:
            documentos.append({
                "titulo": item.get("title"),
                "trecho_ementa": item.get("body"),
                "link_oficial": item.get("href")
            })
        return json.dumps(documentos, ensure_ascii=False)
    except Exception as e:
        return f"Erro ao consultar jurisprudência do STF/STJ: {str(e)}"


def consultar_processos_datajud(termo_busca: str, sigla_tribunal: str = "tjsp") -> str:
    """
    Consulta processos ativos e movimentações no DataJud/CNJ (TJs e TRFs).
    
    Args:
        termo_busca: Assunto ou tese a ser pesquisada.
        sigla_tribunal: Sigla do tribunal (ex: tjsp, trf3, tjrj, tjmg).
    """
    if not cnj_key:
        return "Chave da API do CNJ não informada na barra lateral."
        
    tribunal_limpo = sigla_tribunal.lower().strip()
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal_limpo}/_search"
    headers = {"Authorization": f"APIKey {cnj_key}", "Content-Type": "application/json"}
    
    payload = {
        "size": 4,
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
        return f"Erro no DataJud ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro de conexão com DataJud: {str(e)}"

# ----------------------------------------------------
# 4. Interface Principal de Chat
# ----------------------------------------------------
st.header("⚖️ Consulta Inteligente de Jurisprudência e Processos")
st.caption("Pesquise teses no STF/STJ ou consulte processos nos Tribunais de Justiça via DataJud.")

if not gemini_key:
    st.warning("👈 Insira sua **Gemini API Key** na barra lateral para começar.")
    st.stop()

# Histórico de mensagens na sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens anteriores
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada de nova pergunta do usuário
if prompt := st.chat_input("Ex.: Qual a jurisprudência do STJ sobre desapropriação indireta?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Chamada ao Gemini com ferramentas integradas
    with st.chat_message("assistant"):
        with st.spinner("Consultando bases jurisprudenciais e analisando julgados..."):
            try:
                client = genai.Client(api_key=gemini_key)
                
                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction="Você é um assistente jurídico sênior especializado em pesquisa jurisprudencial. Resuma os precedentes encontrados com clareza, citando tribunais, números de processos, teses e links quando disponíveis.",
                        tools=[buscar_jurisprudencia_stf_stj, consultar_processos_datajud],
                        temperature=0.2
                    )
                )
                
                # Executa a chamada
                response = chat.send_message(prompt)
                texto_resposta = response.text
                st.markdown(texto_resposta)
                
                # Salva no histórico
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar a consulta: {str(e)}")