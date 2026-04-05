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
# FUNÇÃO PDF
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
    "🎯 Simulação por Acertos",
    "🎓 Simulador",
    "⚖️ Pesos dos cursos"
])

# ========================
# 🎯 ABA 0 (NOVA)
# ========================

with aba0:

    st.title("🎯 Simulação por número de acertos")

    st.warning("⚠️ Estimativas baseadas nas médias do ENEM 2023 e 2024. Os valores reais podem variar.")

    col1, col2, col3, col4, col5 = st.columns(5)

    ac_lc = col1.number_input("Linguagens", 0, 45, 30)
    ac_ch = col2.number_input("Humanas", 0, 45, 30)
    ac_mt = col3.number_input("Matemática", 0, 45, 30)
    ac_cn = col4.number_input("Natureza", 0, 45, 30)
    red = col5.number_input("Redação (estimada)", 0.0, 1000.0, 600.0)

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

        escolha = st.selectbox("Qual média usar?", ["2024", "2023", "Geral"])

        if st.button("🚀 Enviar para Simulador SISU"):

            if escolha == "2024":
                st.session_state["notas"] = {
                    "lc": lc[0], "ch": ch[0], "mt": mt[0], "cn": cn[0], "red": red
                }
            elif escolha == "2023":
                st.session_state["notas"] = {
                    "lc": lc[1], "ch": ch[1], "mt": mt[1], "cn": cn[1], "red": red
                }
            else:
                st.session_state["notas"] = {
                    "lc": lc[2], "ch": ch[2], "mt": mt[2], "cn": cn[2], "red": red
                }

            st.success("Notas enviadas! Vá para o Simulador SISU.")

# ========================
# 🎓 SIMULADOR (INALTERADO + integração)
# ========================

with aba1:
    st.title("🎓 Simulador SISU")
    st.write("Veja onde você tem mais chances de passar")

    col_filtros, col_notas = st.columns([1, 2])

    with col_filtros:
        st.subheader("🔎 Filtros")

        uni = st.multiselect("Universidade", sorted(df["universidade"].unique()))

        df_filtrado = df if len(uni) == 0 else df[df["universidade"].isin(uni)]

        curso = st.multiselect("Curso", sorted(df_filtrado["curso"].unique()))

        if len(curso) > 0:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]

    with col_notas:
        st.subheader("📊 Suas notas")

        notas = st.session_state.get("notas", {})

        col1, col2, col3, col4, col5 = st.columns(5)

        redacao = col1.number_input("Redação", 0.0, 1000.0, float(notas.get("red", 600)))
        humanas = col2.number_input("Humanas", 0.0, 1000.0, float(notas.get("ch", 600)))
        natureza = col3.number_input("Natureza", 0.0, 1000.0, float(notas.get("cn", 600)))
        linguagens = col4.number_input("Linguagens", 0.0, 1000.0, float(notas.get("lc", 600)))
        matematica = col5.number_input("Matemática", 0.0, 1000.0, float(notas.get("mt", 600)))

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

        df_result = df_result.sort_values(by="Diferença", ascending=False)

        st.dataframe(df_result, hide_index=True)

# ========================
# ⚖️ PESOS (INALTERADO)
# ========================

with aba2:

    st.title("⚖️ Pesos dos cursos")

    uni = st.multiselect("Universidade", sorted(df["universidade"].unique()))

    df_peso = df if len(uni) == 0 else df[df["universidade"].isin(uni)]

    curso = st.multiselect("Curso", sorted(df_peso["curso"].unique()))

    if len(curso) > 0:
        df_peso = df_peso[df_peso["curso"].isin(curso)]

    st.dataframe(df_peso, hide_index=True)