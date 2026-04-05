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

    df_pdf = df[[
        "Universidade",
        "Curso",
        "Campus",
        "Minha Nota",
        "Nota de Corte",
        "Chance"
    ]]

    data = [df_pdf.columns.tolist()]

    for row in df_pdf.values:
        new_row = []
        for cell in row:
            new_row.append(Paragraph(str(cell), styleN))
        data.append(new_row)

    col_widths = [70, 140, 120, 70, 80, 80]

    tabela = Table(data, colWidths=col_widths)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (3, 1), (4, -1), "CENTER"),
        ("ALIGN", (5, 1), (5, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
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
aba0, aba1, aba2 = st.tabs([
    "📊 Simular por acertos",
    "🎓 Simulador",
    "⚖️ Pesos dos cursos"
])

# ========================
# SIMULAÇÃO POR ACERTOS
# ========================
with aba0:
    st.title("📊 Simulação por número de acertos")

    st.warning(
        "⚠️ Essa simulação é baseada em médias do ENEM 2023 e 2024. "
        "Os resultados são estimativas e podem não refletir sua nota real."
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    ac_lc = col1.number_input("Linguagens (acertos)", 0, 45, 30)
    ac_ch = col2.number_input("Humanas (acertos)", 0, 45, 30)
    ac_mt = col3.number_input("Matemática (acertos)", 0, 45, 30)
    ac_cn = col4.number_input("Natureza (acertos)", 0, 45, 30)
    red = col5.number_input("Redação estimada", 0.0, 1000.0, 700.0)

    def buscar_nota(acertos, col):
        linha = df_acertos[df_acertos["ACERTOS"] == acertos]
        if linha.empty:
            return None
        return float(linha.iloc[0][col])

    # SOMENTE MÉDIA GERAL
    lc_g = buscar_nota(ac_lc, "MED_GERAL_LC")
    ch_g = buscar_nota(ac_ch, "MED_GERAL_CH")
    mt_g = buscar_nota(ac_mt, "MED_GERAL_MT")
    cn_g = buscar_nota(ac_cn, "MED_GERAL_CN")

    def formatar(v):
        return "-" if v is None else f"{v:.2f}".replace(".", ",")

    st.markdown("### 📊 Notas estimadas (média geral)")

    # estilo tabela horizontal
    colA, colB, colC, colD, colE = st.columns(5)

    colA.metric("📚 Linguagens", formatar(lc_g))
    colB.metric("🌍 Humanas", formatar(ch_g))
    colC.metric("📐 Matemática", formatar(mt_g))
    colD.metric("🧪 Natureza", formatar(cn_g))
    colE.metric("✍️ Redação", formatar(red))

    st.markdown("---")

    st.info("💡 Use essas notas diretamente no Simulador SISU.")

    # ========================
    # 🚀 INTEGRAÇÃO
    # ========================
    if st.button("Usar notas no Simulador SISU"):
        if None not in (lc_g, ch_g, mt_g, cn_g):
            st.session_state["nota_linguagens_auto"] = lc_g
            st.session_state["nota_humanas_auto"] = ch_g
            st.session_state["nota_matematica_auto"] = mt_g
            st.session_state["nota_natureza_auto"] = cn_g
            st.session_state["nota_redacao_auto"] = red
            st.success("Notas enviadas! Vá para a aba 🎓 Simulador.")
        else:
            st.error("Preencha corretamente os acertos.")

# ========================
# BOTÕES AUXILIARES
# ========================
st.markdown("---")

if st.button("Já sei minhas notas no ENEM"):
    st.info("👉 Vá para a aba 🎓 Simulador para inserir suas notas manualmente.")

if st.button("Quero descobrir os pesos para um curso"):
    st.info("👉 Vá para a aba ⚖️ Pesos dos cursos para ver como sua nota é calculada.")

# ========================
# SIMULADOR
# ========================
with aba1:
    st.title("🎓 Simulador SISU")
    st.write("Veja onde você tem mais chances de passar")

    col_filtros, col_notas = st.columns([1, 2])

    with col_filtros:
        st.subheader("🔎 Filtros")

        uni = st.multiselect("Universidade", sorted(df["universidade"].unique()), key="sim_uni")
        df_filtrado = df[df["universidade"].isin(uni)] if uni else df

        curso = st.multiselect("Curso", sorted(df_filtrado["curso"].unique()), key="sim_curso")
        if curso:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]

    with col_notas:
        st.subheader("📊 Suas notas")

        col1, col2, col3, col4, col5 = st.columns(5)

        redacao = col1.number_input("Redação", 0.0, 1000.0, st.session_state.get("nota_redacao_auto", 600.0))
        humanas = col2.number_input("Humanas", 0.0, 1000.0, st.session_state.get("nota_humanas_auto", 600.0))
        natureza = col3.number_input("Natureza", 0.0, 1000.0, st.session_state.get("nota_natureza_auto", 600.0))
        linguagens = col4.number_input("Linguagens", 0.0, 1000.0, st.session_state.get("nota_linguagens_auto", 600.0))
        matematica = col5.number_input("Matemática", 0.0, 1000.0, st.session_state.get("nota_matematica_auto", 600.0))

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

        st.subheader("🏆 Melhores Opções")

        aprovados = df_result[df_result["Diferença"] >= 0]
        top3 = aprovados.sort_values(by="nota corte", ascending=False).head(3) if not aprovados.empty else df_result.head(3)

        cols = st.columns(3)

        for i, (_, row) in enumerate(top3.iterrows()):
            with cols[i]:
                st.metric(row["curso"], f"{row['Minha Nota']}", f"{row['Diferença']} pts")
                st.caption(f"{row['universidade']} - {row['campus']}")

        df_view = df_result[[
            "universidade","curso","campus","Minha Nota","nota corte","Diferença","Chance"
        ]].rename(columns={
            "universidade":"Universidade","curso":"Curso","campus":"Campus","nota corte":"Nota de Corte"
        })

        # 🔥 RESTAURADO: divisão por abas de chance
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
            st.warning("Nenhum resultado encontrado.")

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
#  PESOS
# ========================
with aba2:
    st.title("⚖️ Pesos dos cursos")
    st.write("Veja como cada curso calcula sua nota")

    col1, col2 = st.columns(2)

    with col1:
        uni_peso = st.multiselect("Universidade", sorted(df["universidade"].unique()), key="peso_uni")
        df_peso = df if not uni_peso else df[df["universidade"].isin(uni_peso)]

    with col2:
        curso_peso = st.multiselect("Curso", sorted(df_peso["curso"].unique()), key="peso_curso")
        if curso_peso:
            df_peso = df_peso[df_peso["curso"].isin(curso_peso)]

    tabela_pesos = df_peso[[
        "universidade","curso","campus","redacao","ciencias humanas",
        "ciencias da natureza","linguagens e codigos","matematica","soma pesos"
    ]].rename(columns={
        "universidade":"Universidade","curso":"Curso","campus":"Campus",
        "redacao":"Redação","ciencias humanas":"Humanas","ciencias da natureza":"Natureza",
        "linguagens e codigos":"Linguagens","matematica":"Matemática","soma pesos":"Soma"
    })

    st.subheader("📊 Pesos por curso")
    st.dataframe(tabela_pesos, hide_index=True)