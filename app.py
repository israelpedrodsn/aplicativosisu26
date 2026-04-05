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

    df_pdf = df[
        ["Universidade", "Curso", "Campus", "Minha Nota", "Nota de Corte", "Chance"]
    ]

    data = [df_pdf.columns.tolist()]

    for row in df_pdf.values:
        new_row = []
        for cell in row:
            new_row.append(Paragraph(str(cell), styleN))
        data.append(new_row)

    col_widths = [70, 140, 120, 70, 80, 80]

    tabela = Table(data, colWidths=col_widths)

    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (3, 1), (4, -1), "CENTER"),
                ("ALIGN", (5, 1), (5, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ]
        )
    )

    doc.build([tabela])
    buffer.seek(0)
    return buffer


# ========================
# ABAS 
# ========================
aba0, aba1, aba2 = st.tabs(
    ["🧠 Simular por acertos", "🎓 Simulador SISU", "⚖️ Pesos dos cursos"]
)

# ========================
# acertos
# ========================
with aba0:
    st.title("🧠 Simulação por número de acertos")

    st.warning(
        "⚠️ Esta simulação é uma estimativa baseada nas médias do ENEM 2023 e 2024. "
        "Os valores reais podem variar."
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    ac_lc = col1.number_input("Linguagens (acertos)", 0, 45, 20, key="ac_lc")
    ac_ch = col2.number_input("Humanas (acertos)", 0, 45, 20, key="ac_ch")
    ac_cn = col3.number_input("Natureza (acertos)", 0, 45, 20, key="ac_cn")
    ac_mt = col4.number_input("Matemática (acertos)", 0, 45, 20, key="ac_mt")
    red = col5.number_input("Redação", 0.0, 1000.0, 600.0, key="ac_red")

    def buscar_nota(acertos, coluna):
        linha = df_acertos[df_acertos["ACERTOS"] == acertos]
        if not linha.empty:
            return float(linha.iloc[0][coluna])
        return 0

    if st.button("📊 Calcular notas estimadas"):
        resultados = {
            "2024": {
                "LC": buscar_nota(ac_lc, "MED_24_LC"),
                "CH": buscar_nota(ac_ch, "MED_24_CH"),
                "CN": buscar_nota(ac_cn, "MED_24_CN"),
                "MT": buscar_nota(ac_mt, "MED_24_MT"),
            },
            "2023": {
                "LC": buscar_nota(ac_lc, "MED_23_LC"),
                "CH": buscar_nota(ac_ch, "MED_23_CH"),
                "CN": buscar_nota(ac_cn, "MED_23_CN"),
                "MT": buscar_nota(ac_mt, "MED_23_MT"),
            },
            "GERAL": {
                "LC": buscar_nota(ac_lc, "MED_GERAL_LC"),
                "CH": buscar_nota(ac_ch, "MED_GERAL_CH"),
                "CN": buscar_nota(ac_cn, "MED_GERAL_CN"),
                "MT": buscar_nota(ac_mt, "MED_GERAL_MT"),
            },
        }

        st.subheader("📈 Resultados estimados")

        for nome, valores in resultados.items():
            st.markdown(f"### {nome}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Linguagens", round(valores["LC"], 1))
            c2.metric("Humanas", round(valores["CH"], 1))
            c3.metric("Natureza", round(valores["CN"], 1))
            c4.metric("Matemática", round(valores["MT"], 1))

        escolha = st.radio(
            "Qual conjunto deseja usar no simulador SISU?",
            ["2024", "2023", "GERAL"],
        )

        if st.button("➡️ Usar no Simulador SISU"):
            st.session_state["notas_simuladas"] = {
                "linguagens": resultados[escolha]["LC"],
                "humanas": resultados[escolha]["CH"],
                "natureza": resultados[escolha]["CN"],
                "matematica": resultados[escolha]["MT"],
                "redacao": red,
            }

            st.success("Notas enviadas para o Simulador SISU! Vá para a próxima aba 🚀")

# ========================
# simulador
# ========================
with aba1:
    st.title("🎓 Simulador SISU")
    st.write("Veja onde você tem mais chances de passar")

    col_filtros, col_notas = st.columns([1, 2])

    with col_filtros:
        st.subheader("🔎 Filtros")

        uni = st.multiselect("Universidade", sorted(df["universidade"].unique()))

        if len(uni) > 0:
            df_filtrado = df[df["universidade"].isin(uni)]
        else:
            df_filtrado = df

        curso = st.multiselect("Curso", sorted(df_filtrado["curso"].unique()))

        if len(curso) > 0:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]

    with col_notas:
        st.subheader("📊 Suas notas")

        notas_padrao = st.session_state.get("notas_simuladas", {})

        col1, col2, col3, col4, col5 = st.columns(5)

        redacao = col1.number_input("Redação", 0.0, 1000.0, float(notas_padrao.get("redacao", 600)), key="sim_red")
        humanas = col2.number_input("Humanas", 0.0, 1000.0, float(notas_padrao.get("humanas", 600)), key="sim_hum")
        natureza = col3.number_input("Natureza", 0.0, 1000.0, float(notas_padrao.get("natureza", 600)), key="sim_nat")
        linguagens = col4.number_input("Linguagens", 0.0, 1000.0, float(notas_padrao.get("linguagens", 600)), key="sim_lin")
        matematica = col5.number_input("Matemática", 0.0, 1000.0, float(notas_padrao.get("matematica", 600)), key="sim_mat")

    if st.button("🚀 Calcular minhas chances"):
        df_result = df_filtrado.copy()

        df_result["Minha Nota"] = (
            redacao * df_result["redacao"]
            + humanas * df_result["ciencias humanas"]
            + natureza * df_result["ciencias da natureza"]
            + linguagens * df_result["linguagens e codigos"]
            + matematica * df_result["matematica"]
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

        st.subheader("🏆 Melhores Opções")

        aprovados = df_result[df_result["Diferença"] >= 0]

        if not aprovados.empty:
            top3 = aprovados.sort_values(by="nota corte", ascending=False).head(3)
        else:
            top3 = df_result.head(3)

        cols = st.columns(3)

        for i, (_, row) in enumerate(top3.iterrows()):
            with cols[i]:
                st.metric(row["curso"], f"{row['Minha Nota']}", f"{row['Diferença']} pts")
                st.caption(f"{row['universidade']} - {row['campus']}")

# ========================
# ⚖️ PESOS (INALTERADO)
# ========================
with aba2:
    st.title("⚖️ Pesos dos cursos")
    st.write("Veja como cada curso calcula sua nota")

    st.dataframe(df.head(), hide_index=True)