import streamlit as st
import pandas as pd

# ========================
# CONFIG
# ========================

st.set_page_config(page_title="Simulador SISU", layout="wide")

# ========================
# CARREGAR DADOS
# ========================

df = pd.read_csv("dados.csv", sep=";", decimal=",")

st.title("🎓 Simulador SISU")
st.write("Descubra onde você tem mais chances de passar")

# ========================
# FILTROS
# ========================

st.sidebar.header("🔎 Filtros")

universidades = sorted(df["universidade"].unique())
uni_escolhida = st.sidebar.selectbox("Universidade", ["Todas"] + universidades)

if uni_escolhida != "Todas":
    df_filtrado = df[df["universidade"] == uni_escolhida]
else:
    df_filtrado = df.copy()

cursos = sorted(df_filtrado["curso"].unique())
curso_escolhido = st.sidebar.selectbox("Curso", ["Todos"] + cursos)

if curso_escolhido != "Todos":
    df_filtrado = df_filtrado[df_filtrado["curso"] == curso_escolhido]

# ========================
# INPUTS
# ========================

st.subheader("📊 Suas notas do ENEM")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    redacao = st.number_input("Redação", 0.0, 1000.0, 700.0)

with col2:
    humanas = st.number_input("Humanas", 0.0, 1000.0, 600.0)

with col3:
    natureza = st.number_input("Natureza", 0.0, 1000.0, 600.0)

with col4:
    linguagens = st.number_input("Linguagens", 0.0, 1000.0, 600.0)

with col5:
    matematica = st.number_input("Matemática", 0.0, 1000.0, 600.0)

# ========================
# CÁLCULO
# ========================

if st.button("🚀 Calcular minhas chances"):

    df_resultado = df_filtrado.copy()

    # cálculo
    df_resultado["Minha Nota"] = (
        redacao * df_resultado["redacao"] +
        humanas * df_resultado["ciencias humanas"] +
        natureza * df_resultado["ciencias da natureza"] +
        linguagens * df_resultado["linguagens e codigos"] +
        matematica * df_resultado["matematica"]
    ) / df_resultado["soma pesos"]

    df_resultado["Diferença"] = df_resultado["Minha Nota"] - df_resultado["nota corte"]

    # classificação nova
    def classificar(diff):
        if diff >= 0:
            return "Alta chance"
        elif diff >= -10:
            return "Média"
        else:
            return "Baixa"

    df_resultado["Chance"] = df_resultado["Diferença"].apply(classificar)

    # arredondar
    df_resultado["Minha Nota"] = df_resultado["Minha Nota"].round(1)
    df_resultado["nota corte"] = df_resultado["nota corte"].round(1)
    df_resultado["Diferença"] = df_resultado["Diferença"].round(1)

    # remover cursos muito fora
    df_resultado = df_resultado[df_resultado["Diferença"] > -100]

    # ordenar
    df_resultado = df_resultado.sort_values(by="Diferença", ascending=False)

    # ========================
    # TOP 3
    # ========================

    st.subheader("🏆 Suas melhores opções")

    top3 = df_resultado.head(3)

    colA, colB, colC = st.columns(3)

    for i, (idx, row) in enumerate(top3.iterrows()):
        with [colA, colB, colC][i]:
            st.metric(
                label=f"{row['curso']}",
                value=f"{row['Minha Nota']}",
                delta=f"{row['Diferença']} vs corte"
            )
            st.caption(f"{row['universidade']} - {row['campus']}")

    # ========================
    # TABELA BONITA
    # ========================

    df_exibir = df_resultado[[
        "universidade",
        "curso",
        "campus",
        "Minha Nota",
        "nota corte",
        "Diferença",
        "Chance"
    ]].rename(columns={
        "universidade": "Universidade",
        "curso": "Curso",
        "campus": "Campus",
        "nota corte": "Nota de Corte"
    })

    # ========================
    # RESULTADOS
    # ========================

    st.subheader("📊 Análise completa")

    tab1, tab2, tab3 = st.tabs(["🟢 Alta chance", "🟡 Média", "🔴 Baixa"])

    with tab1:
        st.dataframe(df_exibir[df_exibir["Chance"] == "Alta chance"])

    with tab2:
        st.dataframe(df_exibir[df_exibir["Chance"] == "Média"])

    with tab3:
        st.dataframe(df_exibir[df_exibir["Chance"] == "Baixa"])