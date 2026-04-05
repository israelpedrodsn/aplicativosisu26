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
df_acertos = pd.read_csv("microdados_acertos.csv", sep=";", decimal=",")

# ========================
# FUNÇÃO PDF
# ========================

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

def gerar_pdf(df):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20
    )

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
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
    ]))

    doc.build([tabela])
    buffer.seek(0)
    return buffer

# ========================
# ABAS
# ========================

aba0, aba1, aba2 = st.tabs([
    "📊 Simulador por Acertos",
    "🎓 Simulador SISU",
    "⚖️ Pesos dos cursos"
])

# ========================
# 📊 SIMULADOR POR ACERTOS
# ========================

with aba0:

    st.title("📊 Simulador por número de acertos")
    st.warning("⚠️ Valores estimados com base nas médias do ENEM 2023 e 2024.")

    col1, col2, col3, col4, col5 = st.columns(5)

    ac_lc = col1.number_input("Linguagens (acertos)", 0, 45, 30, key="ac_lc")
    ac_ch = col2.number_input("Humanas (acertos)", 0, 45, 30, key="ac_ch")
    ac_cn = col3.number_input("Natureza (acertos)", 0, 45, 30, key="ac_cn")
    ac_mt = col4.number_input("Matemática (acertos)", 0, 45, 30, key="ac_mt")
    red_sim = col5.number_input("Redação estimada", 0.0, 1000.0, 600.0, key="ac_red")

    def buscar_nota(acertos, coluna):
        linha = df_acertos[df_acertos["ACERTOS"] == acertos]
        if linha.empty:
            return None
        return float(linha[coluna].values[0])

    if st.button("📊 Calcular notas estimadas"):

        resultados = {
            "2024": {
                "lc": buscar_nota(ac_lc, "MED_24_LC"),
                "ch": buscar_nota(ac_ch, "MED_24_CH"),
                "cn": buscar_nota(ac_cn, "MED_24_CN"),
                "mt": buscar_nota(ac_mt, "MED_24_MT"),
            },
            "2023": {
                "lc": buscar_nota(ac_lc, "MED_23_LC"),
                "ch": buscar_nota(ac_ch, "MED_23_CH"),
                "cn": buscar_nota(ac_cn, "MED_23_CN"),
                "mt": buscar_nota(ac_mt, "MED_23_MT"),
            },
            "GERAL": {
                "lc": buscar_nota(ac_lc, "MED_GERAL_LC"),
                "ch": buscar_nota(ac_ch, "MED_GERAL_CH"),
                "cn": buscar_nota(ac_cn, "MED_GERAL_CN"),
                "mt": buscar_nota(ac_mt, "MED_GERAL_MT"),
            }
        }

        st.subheader("📈 Resultados estimados")

        for ano, valores in resultados.items():
            st.markdown(f"### 📅 {ano}")
            st.write(f"Linguagens: {valores['lc']}")
            st.write(f"Humanas: {valores['ch']}")
            st.write(f"Natureza: {valores['cn']}")
            st.write(f"Matemática: {valores['mt']}")
            st.write(f"Redação: {red_sim}")

# ========================
# 🎓 SIMULADOR SISU
# ========================

with aba1:
    st.title("🎓 Simulador SISU")

    col_filtros, col_notas = st.columns([1, 2])

    with col_filtros:
        uni = st.multiselect("Universidade", sorted(df["universidade"].unique()), key="sisu_uni")
        df_filtrado = df if not uni else df[df["universidade"].isin(uni)]

        curso = st.multiselect("Curso", sorted(df_filtrado["curso"].unique()), key="sisu_curso")
        if curso:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]

    with col_notas:
        col1, col2, col3, col4, col5 = st.columns(5)

        redacao = col1.number_input("Redação", 0.0, 1000.0, 600.0)
        humanas = col2.number_input("Humanas", 0.0, 1000.0, 600.0)
        natureza = col3.number_input("Natureza", 0.0, 1000.0, 600.0)
        linguagens = col4.number_input("Linguagens", 0.0, 1000.0, 600.0)
        matematica = col5.number_input("Matemática", 0.0, 1000.0, 600.0)

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

        df_result["Chance"] = df_result["Diferença"].apply(
            lambda d: "Alta chance" if d >= 0 else "Média" if d >= -10 else "Baixa"
        )

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

        pdf = gerar_pdf(df_view)

        st.download_button(
            "📄 Baixar PDF",
            data=pdf,
            file_name="resultado.pdf",
            mime="application/pdf"
        )

# ========================
# ⚖️ PESOS
# ========================

with aba2:
    st.title("⚖️ Pesos dos cursos")

    uni = st.multiselect("Universidade", sorted(df["universidade"].unique()), key="peso_uni")
    df_peso = df if not uni else df[df["universidade"].isin(uni)]

    curso = st.multiselect("Curso", sorted(df_peso["curso"].unique()), key="peso_curso")
    if curso:
        df_peso = df_peso[df_peso["curso"].isin(curso)]

    tabela_pesos = df_peso[[
        "universidade", "curso", "campus",
        "redacao", "ciencias humanas",
        "ciencias da natureza", "linguagens e codigos",
        "matematica", "soma pesos"
    ]]

    st.dataframe(tabela_pesos, hide_index=True)