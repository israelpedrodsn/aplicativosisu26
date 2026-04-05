import streamlit as st
import pandas as pd

# PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
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
df_acertos = pd.read_csv("acertos.csv", sep=";", decimal=",")

# ========================
# SESSION STATE (INTEGRAÇÃO)
# ========================
if "notas_estimadas" not in st.session_state:
    st.session_state["notas_estimadas"] = None

# ========================
# FUNÇÃO PDF
# ========================
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


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
        data.append([Paragraph(str(c), styleN) for c in row])

    tabela = Table(data)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
    ]))

    doc.build([tabela])
    buffer.seek(0)

    return buffer

# ========================
# ABAS
# ========================
aba0, aba1, aba2 = st.tabs([
    "📊 Simular por acertos",
    "🎓 Simulador",
    "⚖️ Pesos dos cursos"
])

# ========================
# 📊 SIMULAÇÃO POR ACERTOS
# ========================
with aba0:
    st.title("📊 Simulação por número de acertos")

    st.warning(
        "⚠️ Baseado em médias do ENEM 2023 e 2024. Pode haver variação."
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    ac_lc = col1.number_input("Linguagens", 0, 45, 30)
    ac_ch = col2.number_input("Humanas", 0, 45, 30)
    ac_mt = col3.number_input("Matemática", 0, 45, 30)
    ac_cn = col4.number_input("Natureza", 0, 45, 30)
    red = col5.number_input("Redação", 0.0, 1000.0, 700.0)

    def buscar(ac, col):
        linha = df_acertos[df_acertos["ACERTOS"] == ac]
        return float(linha.iloc[0][col]) if not linha.empty else 0

    lc = buscar(ac_lc, "MED_GERAL_LC")
    ch = buscar(ac_ch, "MED_GERAL_CH")
    mt = buscar(ac_mt, "MED_GERAL_MT")
    cn = buscar(ac_cn, "MED_GERAL_CN")

    st.subheader("📌 Notas estimadas (geral)")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Linguagens", f"{lc:.0f}")
    c2.metric("Humanas", f"{ch:.0f}")
    c3.metric("Matemática", f"{mt:.0f}")
    c4.metric("Natureza", f"{cn:.0f}")

    st.metric("Redação", f"{red:.0f}")

    if st.button("🚀 Usar essas notas no simulador"):
        st.session_state["notas_estimadas"] = {
            "redacao": red,
            "humanas": ch,
            "natureza": cn,
            "linguagens": lc,
            "matematica": mt
        }
        st.success("Notas enviadas para o simulador!")

# ========================
# 🎓 SIMULADOR
# ========================
with aba1:
    st.title("🎓 Simulador SISU")

    usar_auto = st.toggle("Usar notas estimadas automaticamente")

    notas_auto = st.session_state["notas_estimadas"]

    col_filtros, col_notas = st.columns([1, 2])

    with col_filtros:
        uni = st.multiselect("Universidade", sorted(df["universidade"].unique()))
        df_filtrado = df[df["universidade"].isin(uni)] if uni else df

        curso = st.multiselect("Curso", sorted(df_filtrado["curso"].unique()))
        if curso:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]

    with col_notas:
        col1, col2, col3, col4, col5 = st.columns(5)

        if usar_auto and notas_auto:
            redacao = col1.number_input("Redação", value=notas_auto["redacao"])
            humanas = col2.number_input("Humanas", value=notas_auto["humanas"])
            natureza = col3.number_input("Natureza", value=notas_auto["natureza"])
            linguagens = col4.number_input("Linguagens", value=notas_auto["linguagens"])
            matematica = col5.number_input("Matemática", value=notas_auto["matematica"])
        else:
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

        df_result["Chance"] = df_result["Diferença"].apply(
            lambda d: "Alta chance" if d >= 0 else "Média" if d >= -10 else "Baixa"
        )

        st.dataframe(df_result)

# ========================
# ⚖️ PESOS
# ========================
with aba2:
    st.title("⚖️ Pesos dos cursos")

    st.dataframe(df)