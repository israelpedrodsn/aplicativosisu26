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
    </style>
""", unsafe_allow_html=True)

# ========================
# LOAD DATA
# ========================

df = pd.read_csv("dados.csv", sep=";", decimal=",")

st.title("🎓 Simulador SISU Inteligente")
st.write("Veja onde você realmente tem chance de passar")

# ========================
# FILTROS
# ========================

st.sidebar.header("🔎 Filtros")

uni = st.sidebar.selectbox(
    "Universidade",
    ["Todas"] + sorted(df["universidade"].unique())
)

df_filtrado = df if uni == "Todas" else df[df["universidade"] == uni]

curso = st.sidebar.selectbox(
    "Curso",
    ["Todos"] + sorted(df_filtrado["curso"].unique())
)

if curso != "Todos":
    df_filtrado = df_filtrado[df_filtrado["curso"] == curso]

# ========================
# INPUT NOTAS
# ========================

st.subheader("📊 Suas notas")

col1, col2, col3, col4, col5 = st.columns(5)

redacao = col1.number_input("Redação", 0.0, 1000.0, 700.0)
humanas = col2.number_input("Humanas", 0.0, 1000.0, 600.0)
natureza = col3.number_input("Natureza", 0.0, 1000.0, 600.0)
linguagens = col4.number_input("Linguagens", 0.0, 1000.0, 600.0)
matematica = col5.number_input("Matemática", 0.0, 1000.0, 600.0)

# ========================
# CALCULO
# ========================

if st.button("🚀 Analisar minhas chances"):

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
            return "Alta"
        elif d >= -10:
            return "Média"
        else:
            return "Baixa"

    df_result["Chance"] = df_result["Diferença"].apply(classificar)

    df_result["Minha Nota"] = df_result["Minha Nota"].round(1)
    df_result["Diferença"] = df_result["Diferença"].round(1)

    df_result = df_result.sort_values(by="Diferença", ascending=False)

    # ========================
    # INSIGHTS INTELIGENTES
    # ========================

    st.subheader("🧠 Diagnóstico")

    aprovados = df_result[df_result["Diferença"] >= 0]
    quase = df_result[(df_result["Diferença"] < 0) & (df_result["Diferença"] >= -20)]

    if not aprovados.empty:
        st.success(f"🎉 Você já passaria em {len(aprovados)} cursos!")

    if not quase.empty:
        media_falta = abs(quase["Diferença"].mean())
        st.warning(f"📈 Você está perto! Em média faltam {round(media_falta,1)} pontos.")

    if aprovados.empty and quase.empty:
        st.error("⚠️ Nenhum curso próximo — talvez mirar estratégias diferentes.")

    # ========================
    # TOP 3
    # ========================

    st.subheader("🏆 Melhores opções")

    top3 = df_result.head(3)
    cols = st.columns(3)

    for i, (_, row) in enumerate(top3.iterrows()):
        with cols[i]:
            st.metric(
                row["curso"],
                f"{row['Minha Nota']}",
                f"{row['Diferença']} pts"
            )
            st.caption(f"{row['universidade']}")

    # ========================
    # TABELA
    # ========================

    df_view = df_result[[
        "universidade", "curso", "campus",
        "Minha Nota", "nota corte", "Diferença", "Chance"
    ]].rename(columns={
        "universidade": "Universidade",
        "curso": "Curso",
        "campus": "Campus",
        "nota corte": "Nota de Corte"
    })

    st.subheader("📊 Lista completa")

    st.dataframe(df_view, hide_index=True)