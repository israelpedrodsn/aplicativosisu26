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

/* esconder setinhas */
input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { 
    -webkit-appearance: none; 
    margin: 0; 
}
input[type=number] {
    -moz-appearance: textfield;
}

/* centralizar títulos */
h1, h2, h3 {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ========================
# LOAD DATA
# ========================

df = pd.read_csv("dados.csv", sep=";", decimal=",")

# ========================
# HEADER
# ========================

st.title("🎓 Simulador SISU")
st.caption("Descubra as melhores opções com base na sua nota")

# ========================
# FILTROS
# ========================

with st.sidebar:
    st.header("🔎 Filtros")

    uni = st.selectbox(
        "Universidade",
        ["Todas"] + sorted(df["universidade"].unique())
    )

    df_filtrado = df if uni == "Todas" else df[df["universidade"] == uni]

    curso = st.selectbox(
        "Curso",
        ["Todos"] + sorted(df_filtrado["curso"].unique())
    )

    if curso != "Todos":
        df_filtrado = df_filtrado[df_filtrado["curso"] == curso]

# ========================
# INPUTS BONITOS
# ========================

st.subheader("📊 Suas notas no ENEM")

def nota_input(nome, valor_padrao):
    col1, col2 = st.columns([3,1])
    with col1:
        slider = st.slider(nome, 0, 1000, int(valor_padrao))
    with col2:
        numero = st.number_input("", 0.0, 1000.0, float(slider), key=nome)
    return numero

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    redacao = nota_input("Redação", 700)
with c2:
    humanas = nota_input("Humanas", 600)
with c3:
    natureza = nota_input("Natureza", 600)
with c4:
    linguagens = nota_input("Linguagens", 600)
with c5:
    matematica = nota_input("Matemática", 600)

st.divider()

# ========================
# CALCULO
# ========================

if st.button("🚀 Calcular minhas chances", use_container_width=True):

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

    # ========================
    # TOP 3
    # ========================

    st.subheader("🏆 Melhores cursos que você pode alcançar")

    aprovados = df_result[df_result["Diferença"] >= 0]

    if not aprovados.empty:
        top3 = aprovados.sort_values(by="nota corte", ascending=False).head(3)
    else:
        top3 = df_result.head(3)

    cols = st.columns(3)

    for i, (_, row) in enumerate(top3.iterrows()):
        with cols[i]:
            st.markdown(f"""
            ### 🎯 {row['curso']}
            **{row['universidade']} - {row['campus']}**  
            Nota: **{row['Minha Nota']}**  
            Diferença: **{row['Diferença']} pts**
            """)

    st.divider()

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

    st.subheader("📊 Resultados detalhados")

    if abas:
        tabs = st.tabs(nomes)

        for tab, tabela in zip(tabs, abas):
            with tab:
                st.dataframe(tabela, hide_index=True, use_container_width=True)
    else:
        st.warning("Nenhum resultado encontrado com esses filtros.")