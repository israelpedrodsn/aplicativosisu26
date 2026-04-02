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

# ========================
# FUNÇÃO PDF
# ========================

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

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

    # reduzir colunas
    df_pdf = df[[
        "Universidade", "Curso", "Campus",
        "Minha Nota", "Nota de Corte", "Chance"
    ]]

    # quebrar texto automaticamente
    data = [df_pdf.columns.tolist()]
    for row in df_pdf.values:
        new_row = []
        for cell in row:
            new_row.append(Paragraph(str(cell), styleN))
        data.append(new_row)

    # largura das colunas 
    col_widths = [70, 140, 120, 70, 80, 80]

    tabela = Table(data, colWidths=col_widths)

    tabela.setStyle(TableStyle([
        # HEADER
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        # CORPO
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),

        # ALINHAMENTO
        ("ALIGN", (3, 1), (4, -1), "CENTER"),
        ("ALIGN", (5, 1), (5, -1), "CENTER"),

        # GRID
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),

        # ESPAÇAMENTO
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    doc.build([tabela])

    buffer.seek(0)
    return buffer
# ========================
# ABAS
# ========================

aba1, aba2 = st.tabs(["🎓 Simulador", "⚖️ Pesos dos cursos"])

# ========================
# 🎓 SIMULADOR
# ========================


with aba1:
    st.title("🎓 Simulador SISU")
    st.write("Veja onde você tem mais chances de passar")

    col_filtros, col_notas = st.columns([1, 2])

    with col_filtros:
        st.subheader("🔎 Filtros")

        uni = st.multiselect(
            "Universidade",
            sorted(df["universidade"].unique()),
            key="sim_uni"
        )

        if len(uni) > 0:
            df_filtrado = df[df["universidade"].isin(uni)]
        else:
            df_filtrado = df

        curso = st.multiselect(
            "Curso",
            sorted(df_filtrado["curso"].unique()),
            key="sim_curso"
        )

        if len(curso) > 0:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]
    with col_notas:
        st.subheader("📊 Suas notas")

        col1, col2, col3, col4, col5 = st.columns(5)

        redacao = col1.number_input("Redação", 0.0, 1000.0, 600.0, step=None)
        humanas = col2.number_input("Humanas", 0.0, 1000.0, 600.0, step=None)
        natureza = col3.number_input("Natureza", 0.0, 1000.0, 600.0, step=None)
        linguagens = col4.number_input("Linguagens", 0.0, 1000.0, 600.0, step=None)
        matematica = col5.number_input("Matemática", 0.0, 1000.0, 600.0, step=None)

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

        # TOP 3
        st.subheader("🏆 Melhores Opções")

        aprovados = df_result[df_result["Diferença"] >= 0]

        if not aprovados.empty:
            top3 = aprovados.sort_values(by="nota corte", ascending=False).head(3)
        else:
            top3 = df_result.head(3)

        cols = st.columns(3)

        for i, (_, row) in enumerate(top3.iterrows()):
            with cols[i]:
                st.metric(
                    row["curso"],
                    f"{row['Minha Nota']}",
                    f"{row['Diferença']} pts"
                )
                st.caption(f"{row['universidade']} - {row['campus']}")

        # TABELA
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

        st.subheader("📊 Resultados")

        if abas:
            tabs = st.tabs(nomes)

            for tab, tabela in zip(tabs, abas):
                with tab:
                    st.dataframe(tabela, hide_index=True)
        else:
            st.warning("Nenhum resultado encontrado com esses filtros.")

        # ========================
        # PDF DOWNLOAD
        # ========================

        st.markdown("---")
        st.subheader("📥 Exportar resultados")

        pdf = gerar_pdf(df_view)

        st.download_button(
            label="📄 Baixar tabela em PDF",
            data=pdf,
            file_name="simulador_sisu.pdf",
            mime="application/pdf"
        )

# ========================
# ⚖️ PESOS
# ========================

with aba2:

    st.title("⚖️ Pesos dos cursos")
    st.write("Veja como cada curso calcula sua nota")

    col1, col2 = st.columns(2)

    with col1:
        uni_peso = st.multiselect(
            "Universidade",
            sorted(df["universidade"].unique()),
            key="peso_uni"
        )

   
    if len(uni_peso) == 0:
        df_peso = df
    else:
        df_peso = df[df["universidade"].isin(uni_peso)]

    with col2:
        curso_peso = st.multiselect(
            "Curso",
            sorted(df_peso["curso"].unique()),
            key="peso_curso"
        )

  
    if len(curso_peso) != 0:
        df_peso = df_peso[df_peso["curso"].isin(curso_peso)]

    tabela_pesos = df_peso[[
        "universidade", "curso", "campus",
        "redacao", "ciencias humanas",
        "ciencias da natureza", "linguagens e codigos",
        "matematica", "soma pesos"
    ]].rename(columns={
        "universidade": "Universidade",
        "curso": "Curso",
        "campus": "Campus",
        "redacao": "Redação",
        "ciencias humanas": "Humanas",
        "ciencias da natureza": "Natureza",
        "linguagens e codigos": "Linguagens",
        "matematica": "Matemática",
        "soma pesos": "Soma"
    })

    st.subheader("📊 Pesos por curso")
    st.dataframe(tabela_pesos, hide_index=True)