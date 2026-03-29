import streamlit as st
import pandas as pd

# CONFIG
st.set_page_config(page_title="Simulador SISU", layout="wide")

# CSS
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { 
    -webkit-appearance: none; 
    margin: 0; 
}
input[type=number] {
    -moz-appearance: textfield;
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

# ===== BOTÃO =====
simular = st.button("🚀 Simular minhas chances")

# ===== EXECUÇÃO =====
if simular:

    df_calc = df.copy()

    # cálculo da nota
    df_calc["nota_final"] = (
        redacao * df_calc["redacao"] +
        humanas * df_calc["ciencias humanas"] +
        natureza * df_calc["ciencias da natureza"] +
        linguagens * df_calc["linguagens e codigos"] +
        matematica * df_calc["matematica"]
    ) / df_calc["soma pesos"]

    df_calc["dif"] = df_calc["nota_final"] - df_calc["nota corte"]

    # classificação
    def classificar(dif):
        if dif >= 0:
            return "Alta chance"
        elif dif >= -10:
            return "Média chance"
        else:
            return "Baixa chance"

    df_calc["chance"] = df_calc["dif"].apply(classificar)

    # aplicar filtros
    if universidades:
        df_calc = df_calc[df_calc["universidade"].isin(universidades)]

    if cursos:
        df_calc = df_calc[df_calc["curso"].isin(cursos)]

    # ===== RESULTADOS =====
    st.subheader("📈 Resultados")

    df_calc = df_calc.reset_index(drop=True)

    df_calc = df_calc.rename(columns={
        "universidade": "Universidade",
        "curso": "Curso",
        "campus": "Campus",
        "turno/grau": "Turno",
        "nota_final": "Sua Nota",
        "nota corte": "Nota de Corte",
        "chance": "Chance"
    })

    st.dataframe(df_calc, use_container_width=True)

    # ===== TOP 3 =====
    st.subheader("🏆 Cursos mais difíceis que você passaria")

    top3 = df_calc[df_calc["Chance"] == "Alta chance"] \
        .sort_values(by="Nota de Corte", ascending=False) \
        .head(3)

    st.dataframe(
        top3[["Universidade", "Curso", "Campus", "Nota de Corte", "Sua Nota"]],
        use_container_width=True
    )