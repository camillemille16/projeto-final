import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from groq import Groq

# ---------------- CONFIGURAÇÕES INICIAIS ---------------- #
st.set_page_config(page_title="Sistema de Vendas", layout="wide")

# ---------------- ESTADOS ---------------- #
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"admin": "123"}  # login inicial
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "login"  # tela inicial
if "produtos" not in st.session_state:
    st.session_state.produtos = []
if "vendas" not in st.session_state:
    st.session_state.vendas = []

# ---------------- FUNÇÕES ---------------- #
def pagina_login():
    st.title("🔑 Login do Sistema")
    user = st.text_input("Usuário", key="login_user")
    senha = st.text_input("Senha", type="password", key="login_senha")

    if st.button("Entrar"):
        if user in st.session_state.usuarios and st.session_state.usuarios[user] == senha:
            st.session_state.logado = True
            st.session_state.usuario_atual = user
            st.session_state.pagina = "menu"
            st.success(f"Bem-vindo, {user}!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

    if st.button("Cadastrar novo usuário"):
        st.session_state.pagina = "cadastro"
        st.rerun()

def pagina_cadastro():
    st.title("📝 Cadastro de Usuário")
    user = st.text_input("Novo usuário", key="cad_user")
    senha = st.text_input("Senha", type="password", key="cad_senha")
    confirmar = st.text_input("Confirme a senha", type="password", key="cad_conf")

    if st.button("Cadastrar"):
        if not user or not senha:
            st.error("Preencha todos os campos.")
        elif user in st.session_state.usuarios:
            st.error("Usuário já existe.")
        elif senha != confirmar:
            st.error("As senhas não coincidem.")
        else:
            st.session_state.usuarios[user] = senha
            st.success(f"Usuário '{user}' cadastrado com sucesso!")
            st.session_state.pagina = "login"
            st.rerun()

    if st.button("Voltar para Login"):
        st.session_state.pagina = "login"
        st.rerun()

def cadastro_produto():
    st.subheader("📦 Cadastro de Produtos")
    nome = st.text_input("Nome do produto")
    preco = st.number_input("Preço (R$)", min_value=0.0, step=0.01)
    if st.button("Cadastrar Produto"):
        st.session_state.produtos.append({"nome": nome, "preco": preco})
        st.success(f"Produto '{nome}' cadastrado!")

    if st.session_state.produtos:
        df = pd.DataFrame(st.session_state.produtos)
        st.dataframe(df)

def registrar_venda():
    st.subheader("🛒 Registrar Venda")
    if not st.session_state.produtos:
        st.warning("Cadastre produtos primeiro.")
        return

    produto = st.selectbox("Produto", [p["nome"] for p in st.session_state.produtos])
    quantidade = st.number_input("Quantidade", min_value=1, step=1)
    if st.button("Registrar Venda"):
        preco = next(p["preco"] for p in st.session_state.produtos if p["nome"] == produto)
        total = preco * quantidade
        st.session_state.vendas.append({
            "produto": produto,
            "quantidade": quantidade,
            "total": total,
            "data": datetime.date.today(),
            "usuario": st.session_state.usuario_atual
        })
        st.success(f"Venda registrada: {quantidade}x {produto} (R$ {total:.2f})")

    if st.session_state.vendas:
        df = pd.DataFrame(st.session_state.vendas)
        st.dataframe(df)

def relatorios():
    st.subheader("📊 Relatórios de Vendas")
    if not st.session_state.vendas:
        st.info("Nenhuma venda registrada.")
        return

    df = pd.DataFrame(st.session_state.vendas)

    # Gráfico de vendas por produto
    fig1 = px.bar(df.groupby("produto")["total"].sum().reset_index(),
                  x="produto", y="total", title="Faturamento por Produto")
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico de vendas por dia
    fig2 = px.line(df.groupby("data")["total"].sum().reset_index(),
                   x="data", y="total", title="Faturamento por Dia")
    st.plotly_chart(fig2, use_container_width=True)

    # ---------------- USO DO GROQ (IA) ---------------- #
    st.subheader("🤖 Análise com Groq AI")

    api_key = st.text_input("Groq API Key", type="password")
    if api_key:
        client = Groq(api_key=api_key)

        resumo_prompt = f"""
        Você é um analista de vendas. Aqui estão os dados:
        {df.to_dict(orient="records")}
        
        Gere um resumo curto sobre quais produtos mais vendem e se as vendas estão aumentando.
        """

        if st.button("Gerar Insight com IA"):
            try:
                resposta = client.chat.completions.create(
                    model="llama-3.1-8b-instant",  # modelo atualizado
                    messages=[{"role": "user", "content": resumo_prompt}],
                )
                st.success(resposta.choices[0].message["content"])
            except Exception as e:
                st.error(f"Erro ao chamar a API Groq: {e}")

def pagina_menu():
    st.sidebar.title(f"📌 Menu - Usuário: {st.session_state.usuario_atual}")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.pagina = "login"
        st.rerun()

    escolha = st.sidebar.radio("Navegar para:", ["Cadastro de Produtos", "Menu de Vendas", "Relatórios"])

    if escolha == "Cadastro de Produtos":
        cadastro_produto()
    elif escolha == "Menu de Vendas":
        registrar_venda()
    elif escolha == "Relatórios":
        relatorios()

# ---------------- FLUXO PRINCIPAL ---------------- #
if st.session_state.pagina == "login":
    pagina_login()
elif st.session_state.pagina == "cadastro":
    pagina_cadastro()
elif st.session_state.pagina == "menu" and st.session_state.logado:
    pagina_menu()
else:
    st.session_state.pagina = "login"
    st.rerun()
