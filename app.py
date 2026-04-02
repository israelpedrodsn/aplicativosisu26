import streamlit as st
import pandas as pd

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

    senha = st.text_input("Digite a senha", type="password")

    if st.button("Entrar"):
        if senha == SENHA_CORRETA:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()

# ========================
# LOAD
# ========================

df = pd.read_csv("dados.csv", sep=";", decimal=",")

# ========================
# PDF FUNÇÃO
# ========================

def gerar_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    styleN = styles["Normal"]

    data = [df.columns.tolist()]
    for row in df.values:
        data.append([Paragraph(str(cell), styleN) for cell in row])

    tabela = Table(data, colWidths=[80]*len(df.columns))

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

aba1, aba2 = st.tabs(["🎓 Simulador", "⚖️ Pesos"])

# ========================
# 🎓 SIMULADOR
# ========================

with aba1:

    st.title("🎓 Simulador SISU")

    col_filtros, col_notas = st.columns([1, 2])

    with col_filtros:
        st.subheader("🔎 Filtros")

        uni = st.multiselect(
            "Universidades",
            sorted(df["universidade"].unique())
        )

        df_filtrado = df if not uni else df[df["universidade"].isin(uni)]

        curso = st.multiselect(
            "Cursos",
            sorted(df_filtrado["curso"].unique())
        )

        if curso:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]

    with col_notas:
        st.subheader("📊 Suas notas")

        col1, col2, col3, col4, col5 = st.columns(5)

        redacao = col1.number_input("Redação", 0.0, 1000.0, 600.0)
        humanas = col2.number_input("Humanas", 0.0, 1000.0, 600.0)
        natureza = col3.number_input("Natureza", 0.0, 1000.0, 600.0)
        linguagens = col4.number_input("Linguagens", 0.0, 1000.0, 600.0)
        matematica = col5.number_input("Matemática", 0.0, 1000.0, 600.0)

    if st.button("🚀 Calcular"):

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

        df_result = df_result.sort_values(by="Diferença", ascending=False)

        df_view = df_result[[
            "universidade", "curso", "campus",
            "Minha Nota", "nota corte", "Diferença", "Chance"
        ]].rename(columns={
            "universidade": "Universidade",
            "curso": "Curso",
            "campus": "Campus",
            "nota corte": "Nota de Corte"
        })

        st.dataframe(df_view, hide_index=True)

        # PDF
        pdf = gerar_pdf(df_view.head(30))

        st.download_button(
            "📄 Baixar PDF",
            pdf,
            "resultado.pdf",
            "application/pdf"
        )

# ========================
# ⚖️ PESOS
# ========================

with aba2:

    st.title("⚖️ Pesos dos cursos")

    uni = st.multiselect(
        "Universidades",
        sorted(df["universidade"].unique())
    )

    df_peso = df if not uni else df[df["universidade"].isin(uni)]

    curso = st.multiselect(
        "Cursos",
        sorted(df_peso["curso"].unique())
    )

    if curso:
        df_peso = df_peso[df_peso["curso"].isin(curso)]

    tabela = df_peso[[
        "universidade", "curso", "campus",
        "redacao", "ciencias humanas",
        "ciencias da natureza", "linguagens e codigos",
        "matematica"
    ]]

    st.dataframe(tabela, hide_index=True)

    # PDF PESOS
    pdf = gerar_pdf(tabela.head(30))

    st.download_button(
        "📄 Baixar PDF dos pesos",
        pdf,
        "pesos.pdf",
        "application/pdf"
    )