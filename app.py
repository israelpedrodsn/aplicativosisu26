import streamlit as st
import pandas as pd

# CONFIG
st.set_page_config(page_title="Simulador SISU", layout="wide")

# CSS LIMPO (sem quebrar nada)
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* tirar setinhas */
input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { 
    -webkit-appearance: none; 
    margin: 0; 
}
input[type=number] {
    -moz-appearance: textfield;
}

/* cards visuais */
.card {
    padding: 15px;
    border-radius: 12px;
    background-color: #111;
    border: 1px solid #333;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# CARREGAR DADOS
df = pd.read_csv("dados.csv", sep=";", decimal=",")

# TÍTULO
st.title("🎓 Simulador SISU")
st.write("Descubra onde você tem chance de passar")

# ===== LAYOUT =====
col1, col2 = st.columns([1,1])

# ===== NOTAS =====
with col1:
    st.subheader("📊 Suas notas")

    redacao = st.number_input("Redação", 0.0, 1000.0, 700.0)
    humanas = st.number_input("Ciências Humanas", 0.0, 1000.0, 600.0)
    natureza = st.number_input("Ciências da Natureza", 0.0, 1000.0, 600.0)
    linguagens = st.number_input("Linguagens e Códigos", 0.0, 1000.0, 600.0)
    matematica = st.number_input("Matemática", 0.0, 1000.0, 700.0)

# ===== FILTROS =====
with col2:
    st.subheader("🎯 Filtros")

    universidades = st.multiselect(
        "Universidade",
        options=sorted(df["universidade"].unique())
    )

    cursos = st.multiselect(
        "Curso",
        options=sorted(df["curso"].unique())
    )

    categorias = st.multiselect(
        "Tipo de chance",
        ["Alta chance", "Média chance", "Baixa chance"],
        default=["Alta chance", "Média chance"]
    )

# ===== CÁLCULO =====
df["nota_final"] = (
    redacao * df["redacao"] +
    humanas * df["ciencias humanas"] +
    natureza * df["ciencias da natureza"] +
    linguagens * df["linguagens e codigos"] +
    matematica * df["matematica"]
) / df["soma pesos"]

df["dif"] = df["nota_final"] - df["nota corte"]

# CLASSIFICAÇÃO
def classificar(dif):
    if dif >= 0:
        return "Alta chance"
    elif dif >= -10:
        return "Média chance"
    else:
        return "Baixa chance"

df["chance"] = df["dif"].apply(classificar)

# ===== FILTROS APLICADOS =====
df_filtrado = df.copy()

if universidades:
    df_filtrado = df_filtrado[df_filtrado["universidade"].isin(universidades)]

if cursos:
    df_filtrado = df_filtrado[df_filtrado["curso"].isin(cursos)]

# ===== RESULTADOS =====
st.subheader("📈 Resultados")

if categorias:
    df_filtrado = df_filtrado[df_filtrado["chance"].isin(categorias)]

# remover índice
df_filtrado = df_filtrado.reset_index(drop=True)

# renomear colunas
df_filtrado = df_filtrado.rename(columns={
    "universidade": "Universidade",
    "curso": "Curso",
    "campus": "Campus",
    "turno/grau": "Turno",
    "nota_final": "Sua Nota",
    "nota corte": "Nota de Corte",
    "chance": "Chance"
})

st.dataframe(df_filtrado, use_container_width=True)

# ===== TOP 3 (MAIS DIFÍCEIS QUE PASSA) =====
st.subheader("🏆 Cursos mais difíceis que você passaria")

top3 = df[df["dif"] >= 0].sort_values(by="nota corte", ascending=False).head(3)

top3 = top3.rename(columns={
    "universidade": "Universidade",
    "curso": "Curso",
    "campus": "Campus",
    "nota corte": "Nota de Corte",
    "nota_final": "Sua Nota"
})

st.dataframe(top3[["Universidade", "Curso", "Campus", "Nota de Corte", "Sua Nota"]], use_container_width=True)