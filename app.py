import streamlit as st
import uuid
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurações da Página
# ----------------------------------------------------
st.set_page_config(
    page_title="JusAssist IA - MPMS",
    page_icon="⚖️",
    layout="wide"
)

# ----------------------------------------------------
# 2. Carregamento da Chave
# ----------------------------------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("⚠️ Chave GEMINI_API_KEY não configurada nos Secrets do Streamlit.")
    st.stop()

# ----------------------------------------------------
# 3. Prompts Especializados (Jurisprudência & Parecer MPMS)
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
Apresente hipóteses em que a tese é rejeitada (ex: ausência de prova pericial, culpa exclusiva).

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
1. TRAVA ANTI-ALUCINAÇÃO: Utilize a ferramenta de busca do Google para localizar precedentes, números de REsps, Temas e acórdãos REAIS do STF, STJ e TJMS. Proibido inventar números ou ementas.
2. TRAVA DE HIERARQUIA: Precedentes das Turmas de Direito Privado do STJ (3ª e 4ª Turmas) e STF PREVALECEM ABSOLUTAMENTE sobre pareceres de Conselhos de Classe (CREMESP/COFFITO), notas do e-NATJus ou resoluções da ANS.
3. DIRETRIZ PROTETIVA: Em saúde, vida e vulneráveis (TEA, paralisia, oncologia, alimentos), a orientação institucional é pela tutela integral da dignidade humana quando amparada por laudo idôneo.
4. RELATÓRIO SUCINTO INSTITUCIONAL: Máximo 500 palavras, fluido em parágrafos encadeados por verbos de ligação ("Alega o apelante que..."), SEM TÓPICOS/BULLETS, finalizando com a fórmula padrão de admissibilidade.
5. ESTILO: Expressões latinas em itálico (*in re ipsa*, *rebus sic stantibus*). Jurisprudências citadas em bloco recuado (`>`), em itálico.

### 🔄 FLUXO INTERATIVO AUTOMATIZADO:
Quando o usuário pedir "Analise os autos e gere o parecer" (com arquivo PDF ou texto anexado):

- ETAPA 1 (Diagnóstico & Consulta Ativa de Precedentes):
  Apresente o Raio-X dos autos (Fatos, Preliminares mapeadas, Dispositivos legais).
  EXECUTE UMA BUSCA NA INTERNET por precedentes recentes do STJ/STF/TJMS aderentes ao caso e APRESENTE:
  "🔍 Precedentes localizados para o caso: [Liste 2 a 3 acórdãos/Temas reais encontrados com número e tese].
  👉 PERGUNTA OBRIGATÓRIA: Deseja aplicar os precedentes acima sugeridos ou a Procuradoria deseja indicar outro acórdão específico para este parecer?"
  PARE AQUI e aguarde a confirmação do analista.

- ETAPA 2 (Ementa Técnica e Relatório Institucional):
  Após o "de acordo" do analista, gere a Ementa Técnica Formal e o Relatório Sucinto Fluido (até 500 palavras, sem tópicos). PARE AQUI e aguarde validação.

- ETAPA 3 (Minuta Integral de Alta Densidade - 6 a 10 páginas):
  Redija a peça completa: Cabeçalho institucional, Ementa, "COLENDA CÂMARA CÍVEL,", Relatório, I – Da controvérsia recursal (ou Preliminares), II – Do mérito (Fundamentação exaustiva de 2.500 a 4.000 palavras, rebatendo todos os argumentos), III – Conclusão (Opinamento expresso), Datação (Campo Grande/MS) e Assinatura de Luciana Moreira Schenk.
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
# 5. Modal de Ajuda e Instruções
# ----------------------------------------------------
@st.dialog("📖 Como Funciona a IA & Exemplos de Uso", width="large")
def exibir_manual_ajuda():
    st.markdown("### ⚖️ Modos de Atuação da IA")
    st.markdown(
        """
| Modo | Objetivo Principal | Como a IA Responde | Como a Assessora Deve Entrar |
| :--- | :--- | :--- | :--- |
| **🔍 Pesquisa de Jurisprudência** | Consultas rápidas de teses, súmulas e julgados no STF, STJ e TJs. | Estrutura analítica: Tese Central, Precedentes Favoráveis, Contrapontos, Critérios e Ementa para Cópia. | Apenas digite a dúvida jurídica no chat. |
| **📄 Minuta de Parecer (MPMS)** | Elaboração da peça completa de segundo grau (6 a 10 páginas). | Lê o PDF, faz o raio-x fático, pesquisa acórdãos recentes e gera a minuta densa institucional. | Anexa o PDF do processo e digita: *'Analise os autos e gere o parecer'*. |
        """
    )
    
    st.divider()
    st.markdown("### 💡 Exemplos Práticos de Entrada")
    
    st.markdown("#### 1. Para Pesquisa de Jurisprudência:")
    st.code("Qual o entendimento do STJ sobre responsabilidade do Estado por erro médico que causa sequelas permanentes em menor?", language="text")
    st.code("Pesquise a jurisprudência do TJMS sobre rescisão de contrato imobiliário por culpa da construtora.", language="text")

    st.markdown("#### 2. Para Minuta de Parecer (MPMS):")
    st.markdown("1. Selecione o modo **📄 Minuta de Parecer (MPMS)** na barra lateral.")
    st.markdown("2. Anexe o PDF da petição inicial, sentença ou apelação no campo **📂 Anexar Autos (PDF)**.")
    st.markdown("3. Digite no chat:")
    st.code("Analise os autos e gere o parecer.", language="text")
    st.caption("A IA apresentará o raio-x e sugerirá os acórdãos reais encontrados. Basta responder 'Aprovado, prossiga' para que ela gere a ementa, o relatório e a minuta completa.")

# ----------------------------------------------------
# 6. Barra Lateral
# ----------------------------------------------------
with st.sidebar:
    st.title("⚖️ JusAssist MPMS")
    
    modo_selecionado = st.radio(
        "Modo de Atuação:",
        ["📄 Minuta de Parecer (MPMS)", "🔍 Pesquisa de Jurisprudência"],
        index=0 if chat_atual.get("mode") == "📄 Minuta de Parecer (MPMS)" else 1,
        help="Alterne entre a elaboração do parecer completo do processo ou pesquisa livre de teses."
    )
    chat_atual["mode"] = modo_selecionado

    st.divider()

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📝 Nova Conversa", use_container_width=True, type="primary"):
            if len(chat_atual["messages"]) > 0:
                novo_id = str(uuid.uuid4())
                st.session_state.chats[novo_id] = {
                    "title": "",
                    "mode": modo_selecionado,
                    "messages": []
                }
                st.session_state.current_chat_id = novo_id
                st.rerun()
    with col_btn2:
        if st.button("ℹ️ Ajuda & Exemplos", use_container_width=True):
            exibir_manual_ajuda()

    uploaded_file = None
    if modo_selecionado == "📄 Minuta de Parecer (MPMS)":
        st.markdown("### 📂 Anexar Autos (PDF)")
        uploaded_file = st.file_uploader(
            "Envie a Inicial, Sentença ou Apelação",
            type=["pdf"],
            help="O arquivo será lido integralmente pela IA para extração dos fatos e emissão do parecer."
        )

    st.divider()

    # Histórico de Conversas
    conversas_com_historico = {
        cid: cdata for cid, cdata in st.session_state.chats.items() if len(cdata["messages"]) > 0
    }

    if conversas_com_historico:
        st.caption("ÚLTIMAS CONSULTAS / PARECERES")
        for chat_id, chat_data in list(conversas_com_historico.items()):
            icone = "📄" if chat_data.get("mode") == "📄 Minuta de Parecer (MPMS)" else "🔍"
            titulo_exibicao = chat_data["title"] if chat_data["title"] else "Consulta"
            if len(titulo_exibicao) > 24:
                titulo_exibicao = titulo_exibicao[:21] + "..."
            
            is_active = (chat_id == st.session_state.current_chat_id)
            btn_style = f"{icone} {titulo_exibicao}" if not is_active else f"🔹 **{titulo_exibicao}**"
            
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(btn_style, key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                if st.button("✕", key=f"del_{chat_id}", help="Excluir"):
                    del st.session_state.chats[chat_id]
                    if st.session_state.current_chat_id == chat_id:
                        restantes = list(st.session_state.chats.keys())
                        if restantes:
                            st.session_state.current_chat_id = restantes[0]
                        else:
                            novo_id = str(uuid.uuid4())
                            st.session_state.chats[novo_id] = {"title": "", "mode": modo_selecionado, "messages": []}
                            st.session_state.current_chat_id = novo_id
                    st.rerun()

# ----------------------------------------------------
# 7. Interface Principal de Chat
# ----------------------------------------------------
st.header(f"⚖️ {chat_atual['mode']}")
if chat_atual["title"]:
    st.caption(f"Assunto: **{chat_atual['title']}**")
else:
    if modo_selecionado == "📄 Minuta de Parecer (MPMS)":
        st.caption("Anexe os autos em PDF na barra lateral e digite: 'Analise os autos e gere o parecer'.")
    else:
        st.caption("Pesquisa analítica de jurisprudência em Tribunais Superiores e Estaduais.")

# Exibição do histórico de mensagens
for msg in chat_atual["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

placeholder_texto = (
    "Ex.: Analise os autos e gere o parecer..."
    if modo_selecionado == "📄 Minuta de Parecer (MPMS)"
    else "Ex.: Qual o entendimento do STJ sobre apropriação indébita tributária?"
)

if prompt := st.chat_input(placeholder_texto):
    if not chat_atual["title"]:
        chat_atual["title"] = prompt[:35] + ("..." if len(prompt) > 35 else "")

    chat_atual["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processando fundamentação e pesquisando precedentes oficiais..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)

                instrucao_ativa = (
                    SUPERPROMPT_PARECER
                    if modo_selecionado == "📄 Minuta de Parecer (MPMS)"
                    else PROMPT_JURISPRUDENCIA
                )

                conteudos = []
                if uploaded_file is not None and len(chat_atual["messages"]) <= 1:
                    bytes_data = uploaded_file.getvalue()
                    conteudos.append(types.Part.from_bytes(data=bytes_data, mime_type="application/pdf"))
                    conteudos.append(f"[Documento Processual Anexado: {uploaded_file.name}]")

                conteudos.append(prompt)

                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=instrucao_ativa,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1
                    )
                )

                response = chat.send_message(conteudos)
                texto_resposta = response.text

                st.markdown(texto_resposta)
                chat_atual["messages"].append({"role": "assistant", "content": texto_resposta})
                st.rerun()

            except Exception as e:
                st.error(f"Erro no processamento: {str(e)}")
