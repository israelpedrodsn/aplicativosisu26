import streamlit as st
import pandas as pd

# PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

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
# 🔐 SENHA
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
micro = pd.read_csv("microdados.csv", sep=";", decimal=",")

# ========================
# PDF
# ========================

def gerar_pdf(df):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    styleN = styles["Normal"]

    df_pdf = df[[
        "Universidade", "Curso", "Campus",
        "Minha Nota", "Nota de Corte", "Chance"
    ]]

    data = [df_pdf.columns.tolist()]
    for row in df_pdf.values:
        data.append([Paragraph(str(cell), styleN) for cell in row])

    tabela = Table(data, colWidths=[70, 140, 120, 70, 80, 80])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))

    doc.build([tabela])
    buffer.seek(0)
    return buffer

# ========================
# ABAS
# ========================

aba0, aba1, aba2 = st.tabs([
    "🎯 Acertos",
    "🎓 Simulador",
    "⚖️ Pesos dos cursos"
])

# ========================
# 🎯 ABA ACERTOS
# ========================

with aba0:

    st.title("🎯 Simulação por acertos")

    st.warning("⚠️ Estimativa baseada nas médias do ENEM 2023 e 2024. Pode variar.")

    col1, col2, col3, col4, col5 = st.columns(5)

    ac_lc = col1.number_input("Linguagens", 0, 45, 30)
    ac_ch = col2.number_input("Humanas", 0, 45, 30)
    ac_mt = col3.number_input("Matemática", 0, 45, 30)
    ac_cn = col4.number_input("Natureza", 0, 45, 30)
    redacao_est = col5.number_input("Redação", 0.0, 1000.0, 700.0)

    if st.button("📊 Calcular notas estimadas"):

        def buscar(area, acertos):
            linha = micro[micro["ACERTOS"] == acertos]
            if linha.empty:
                return 0, 0, 0

            return (
                linha[f"MED_24_{area}"].values[0],
                linha[f"MED_23_{area}"].values[0],
                linha[f"MED_GERAL_{area}"].values[0],
            )

        lc = buscar("LC", ac_lc)
        ch = buscar("CH", ac_ch)
        mt = buscar("MT", ac_mt)
        cn = buscar("CN", ac_cn)

        df_notas = pd.DataFrame({
            "Área": ["Linguagens", "Humanas", "Matemática", "Natureza"],
            "2024": [lc[0], ch[0], mt[0], cn[0]],
            "2023": [lc[1], ch[1], mt[1], cn[1]],
            "Geral": [lc[2], ch[2], mt[2], cn[2]],
        })

        st.dataframe(df_notas, hide_index=True)

        escolha = st.selectbox(
            "Escolha qual média usar:",
            ["2024", "2023", "Geral"]
        )

        if st.button("🚀 Enviar para Simulador SISU"):

            if escolha == "2024":
                notas = [lc[0], ch[0], mt[0], cn[0]]
            elif escolha == "2023":
                notas = [lc[1], ch[1], mt[1], cn[1]]
            else:
                notas = [lc[2], ch[2], mt[2], cn[2]]

            st.session_state["notas"] = {
                "linguagens": notas[0],
                "humanas": notas[1],
                "matematica": notas[2],
                "natureza": notas[3],
                "redacao": redacao_est
            }

            st.success("Notas enviadas! Vá para o Simulador SISU.")

# ========================
# 🎓 SIMULADOR (INALTERADO + INTEGRAÇÃO)
# ========================

with aba1:
    st.title("🎓 Simulador SISU")
    st.write("Veja onde você tem mais chances de passar")

    col_filtros, col_notas = st.columns([1, 2])

    with col_filtros:
        st.subheader("🔎 Filtros")

        uni = st.multiselect("Universidade", sorted(df["universidade"].unique()))

        df_filtrado = df[df["universidade"].isin(uni)] if uni else df

        curso = st.multiselect("Curso", sorted(df_filtrado["curso"].unique()))

        if curso:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]

    with col_notas:
        st.subheader("📊 Suas notas")

        notas = st.session_state.get("notas", {})

        col1, col2, col3, col4, col5 = st.columns(5)

        redacao = col1.number_input("Redação", 0.0, 1000.0, float(notas.get("redacao", 600)))
        humanas = col2.number_input("Humanas", 0.0, 1000.0, float(notas.get("humanas", 600)))
        natureza = col3.number_input("Natureza", 0.0, 1000.0, float(notas.get("natureza", 600)))
        linguagens = col4.number_input("Linguagens", 0.0, 1000.0, float(notas.get("linguagens", 600)))
        matematica = col5.number_input("Matemática", 0.0, 1000.0, float(notas.get("matematica", 600)))

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

        st.dataframe(df_result, hide_index=True)

# ========================
# ⚖️ PESOS (INALTERADO)
# ========================

with aba2:

    st.title("⚖️ Pesos dos cursos")

    uni_peso = st.multiselect("Universidade", sorted(df["universidade"].unique()))

    df_peso = df[df["universidade"].isin(uni_peso)] if uni_peso else df

    curso_peso = st.multiselect("Curso", sorted(df_peso["curso"].unique()))

    if curso_peso:
        df_peso = df_peso[df_peso["curso"].isin(curso_peso)]

    st.dataframe(df_peso, hide_index=True)