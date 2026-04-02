import streamlit as st
import pandas as pd

# ========================
# CONFIG
# ========================

st.set_page_config(page_title="Simulador SISU", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ========================
# 🔐 SISTEMA DE SENHA
# ========================

SENHA_CORRETA = st.secrets["senha"]

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔒 Acesso restrito")

    senha = st.text_input("Digite a senha para acessar", type="password")

    if st.button("Entrar"):
        if senha == SENHA_CORRETA:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()

# ========================
# LOAD DATA
# ========================

df = pd.read_csv("dados.csv", sep=";", decimal=",")

# ========================
# ABAS PRINCIPAIS
# ========================

aba1, aba2 = st.tabs(["🎓 Simulador", "⚖️ Pesos dos cursos"])

# ========================
# ========================
# 🎓 ABA 1 - SIMULADOR
# ========================
# ========================

with aba1:

    st.title("🎓 Simulador SISU")
    st.write("Veja onde você tem mais chances de passar")

    col_filtros, col_notas = st.columns([1, 2])

    # FILTROS
    with col_filtros:
        st.subheader("🔎 Filtros")

        uni = st.selectbox(
            "Universidade",
            ["Todas"] + sorted(df["universidade"].unique()),
            key="sim_uni"
        )

        df_filtrado = df if uni == "Todas" else df[df["universidade"] == uni]

        curso = st.selectbox(
            "Curso",
            ["Todos"] + sorted(df_filtrado["curso"].unique()),
            key="sim_curso"
        )

        if curso != "Todos":
            df_filtrado = df_filtrado[df_filtrado["curso"] == curso]

    # NOTAS
    with col_notas:
        st.subheader("📊 Suas notas")

        col1, col2, col3, col4, col5 = st.columns(5)

        redacao = col1.number_input("Redação", 0.0, 1000.0, 600.0, step=None)
        humanas = col2.number_input("Humanas", 0.0, 1000.0, 600.0, step=None)
        natureza = col3.number_input("Natureza", 0.0, 1000.0, 600.0, step=None)
        linguagens = col4.number_input("Linguagens", 0.0, 1000.0, 600.0, step=None)
        matematica = col5.number_input("Matemática", 0.0, 1000.0, 600.0, step=None)

    # BOTÃO
    if st.button("🚀 Calcular minhas chances"):

        df_result = df_filtrado.copy()

        df_result["Minha Nota"] = (
            redacao * df_result["redacao"] +
            humanas * df_result["ciencias humanas"] +
            natureza * df_result["ciencias da natureza"] +
            linguagens * df_result["linguagens e codigos"] +
            matematica * df_result["matematica"]
        ) / df_result["soma pesos"]

        df_result["Diferença"] = df_result["Minha Nota"] - df_result["nota corte"]

        def classificar(d):
            if d >= 0:
                return "Alta chance"
            elif d >= -10:
                return "Média"
            else:
                return "Baixa"

        df_result["Chance"] = df_result["Diferença"].apply(classificar)

        df_result["Minha Nota"] = df_result["Minha Nota"].round(1)
        df_result["Diferença"] = df_result["Diferença"].round(1)

        df_result = df_result.sort_values(by="Diferença", ascending=False)

        # TOP 3
        st.subheader("🏆 Melhores Opções")

        aprovados = df_result[df_result["Diferença"] >= 0]

        if not aprovados.empty:
            top3 = aprovados.sort_values(by="nota corte", ascending=False).head(3)
        else:
            top3 = df_result.head(3)

        cols = st.columns(3)

        for i, (_, row) in enumerate(top3.iterrows()):
            with cols[i]:
                st.metric(
                    row["curso"],
                    f"{row['Minha Nota']}",
                    f"{row['Diferença']} pts"
                )
                st.caption(f"{row['universidade']} - {row['campus']}")

        # TABELA
        df_view = df_result[[
            "universidade", "curso", "campus",
            "Minha Nota", "nota corte", "Diferença", "Chance"
        ]].rename(columns={
            "universidade": "Universidade",
            "curso": "Curso",
            "campus": "Campus",
            "nota corte": "Nota de Corte"
        })

        df_alta = df_view[df_view["Chance"] == "Alta chance"]
        df_media = df_view[df_view["Chance"] == "Média"]
        df_baixa = df_view[df_view["Chance"] == "Baixa"]

        abas = []
        nomes = []

        if not df_alta.empty:
            abas.append(df_alta)
            nomes.append("🟢 Alta chance")

        if not df_media.empty:
            abas.append(df_media)
            nomes.append("🟡 Média")

        if not df_baixa.empty:
            abas.append(df_baixa)
            nomes.append("🔴 Baixa")

        st.subheader("📊 Resultados")

        if abas:
            tabs = st.tabs(nomes)

            for tab, tabela in zip(tabs, abas):
                with tab:
                    st.dataframe(tabela, hide_index=True)
        else:
            st.warning("Nenhum resultado encontrado com esses filtros.")

        # DOWNLOAD
        st.markdown("---")
        st.subheader("📥 Exportar resultados")

        csv = df_view.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Baixar tabela completa (CSV)",
            data=csv,
            file_name="simulador_sisu_resultados.csv",
            mime="text/csv"
        )

# ========================
# ========================
# ⚖️ ABA 2 - PESOS
# ========================
# ========================

with aba2:

    st.title("⚖️ Pesos dos cursos")
    st.write("Veja como cada curso calcula sua nota")

    col1, col2 = st.columns(2)

    with col1:
        uni_peso = st.selectbox(
            "Universidade",
            ["Todas"] + sorted(df["universidade"].unique()),
            key="peso_uni"
        )

    df_peso = df if uni_peso == "Todas" else df[df["universidade"] == uni_peso]

    with col2:
        curso_peso = st.selectbox(
            "Curso",
            ["Todos"] + sorted(df_peso["curso"].unique()),
            key="peso_curso"
        )

    if curso_peso != "Todos":
        df_peso = df_peso[df_peso["curso"] == curso_peso]

    tabela_pesos = df_peso[[
        "universidade", "curso", "campus",
        "redacao", "ciencias humanas",
        "ciencias da natureza", "linguagens e codigos",
        "matematica", "soma pesos"
    ]].rename(columns={
        "universidade": "Universidade",
        "curso": "Curso",
        "campus": "Campus",
        "redacao": "Redação",
        "ciencias humanas": "Humanas",
        "ciencias da natureza": "Natureza",
        "linguagens e codigos": "Linguagens",
        "matematica": "Matemática",
        "soma pesos": "Soma"
    })

    st.subheader("📊 Pesos por curso")
    st.dataframe(tabela_pesos, hide_index=True)