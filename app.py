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

    senha = st.text_input("Digite a senha", type="password")

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
df_micro = pd.read_csv("microdados.csv", sep=";", decimal=",")

# ========================
# PDF
# ========================

def gerar_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    styleN = styles["Normal"]

    data = [df.columns.tolist()]
    for row in df.values:
        data.append([Paragraph(str(x), styleN) for x in row])

    tabela = Table(data, colWidths=[70,140,120,70,80,80])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("FONTSIZE", (0,0), (-1,-1), 8),
    ]))

    doc.build([tabela])
    buffer.seek(0)
    return buffer

# ========================
# ABAS
# ========================

aba0, aba1, aba2 = st.tabs([
    "📈 Simulação por acertos",
    "🎓 Simulador SISU",
    "⚖️ Pesos dos cursos"
])

# ========================
# 📈 ABA NOVA (ACERTOS)
# ========================

with aba0:

    st.title("📈 Simulação por número de acertos")

    st.warning("⚠️ Valores aproximados baseados nas médias do ENEM 2023 e 2024.")

    col1, col2, col3, col4, col5 = st.columns(5)

    ac_lc = col1.number_input("Linguagens", 0, 45, 30)
    ac_ch = col2.number_input("Humanas", 0, 45, 30)
    ac_mt = col3.number_input("Matemática", 0, 45, 30)
    ac_cn = col4.number_input("Natureza", 0, 45, 30)
    red = col5.number_input("Redação", 0.0, 1000.0, 600.0)

    def buscar(acertos, coluna):
        linha = df_micro[df_micro["ACERTOS"] == acertos]
        if not linha.empty:
            return float(linha.iloc[0][coluna])
        return 0

    if st.button("📊 Calcular notas estimadas"):

        resultados = {
            "2024": [
                buscar(ac_lc,"MED_24_LC"),
                buscar(ac_ch,"MED_24_CH"),
                buscar(ac_mt,"MED_24_MT"),
                buscar(ac_cn,"MED_24_CN"),
            ],
            "2023": [
                buscar(ac_lc,"MED_23_LC"),
                buscar(ac_ch,"MED_23_CH"),
                buscar(ac_mt,"MED_23_MT"),
                buscar(ac_cn,"MED_23_CN"),
            ],
            "Geral": [
                buscar(ac_lc,"MED_GERAL_LC"),
                buscar(ac_ch,"MED_GERAL_CH"),
                buscar(ac_mt,"MED_GERAL_MT"),
                buscar(ac_cn,"MED_GERAL_CN"),
            ]
        }

        opcao = st.radio("Escolha qual usar:", ["2024","2023","Geral"])

        notas = resultados[opcao]

        st.write("### Resultado estimado")
        st.write(f"Linguagens: {notas[0]:.1f}")
        st.write(f"Humanas: {notas[1]:.1f}")
        st.write(f"Matemática: {notas[2]:.1f}")
        st.write(f"Natureza: {notas[3]:.1f}")

        if st.button("➡️ Usar no simulador SISU"):
            st.session_state["notas_sim"] = {
                "lc": notas[0],
                "ch": notas[1],
                "mt": notas[2],
                "cn": notas[3],
                "red": red
            }
            st.success("Notas enviadas! Vá para a aba Simulador.")

# ========================
# 🎓 SIMULADOR (INALTERADO + INTEGRAÇÃO)
# ========================

with aba1:

    st.title("🎓 Simulador SISU")

    col_filtros, col_notas = st.columns([1,2])

    with col_filtros:
        st.subheader("🔎 Filtros")

        uni = st.multiselect("Universidade", sorted(df["universidade"].unique()))

        df_filtrado = df if len(uni)==0 else df[df["universidade"].isin(uni)]

        curso = st.multiselect("Curso", sorted(df_filtrado["curso"].unique()))

        if len(curso)>0:
            df_filtrado = df_filtrado[df_filtrado["curso"].isin(curso)]

    with col_notas:
        st.subheader("📊 Suas notas")

        default = st.session_state.get("notas_sim", {})

        col1,col2,col3,col4,col5 = st.columns(5)

        redacao = col1.number_input("Redação",0.0,1000.0,float(default.get("red",600)))
        humanas = col2.number_input("Humanas",0.0,1000.0,float(default.get("ch",600)))
        natureza = col3.number_input("Natureza",0.0,1000.0,float(default.get("cn",600)))
        linguagens = col4.number_input("Linguagens",0.0,1000.0,float(default.get("lc",600)))
        matematica = col5.number_input("Matemática",0.0,1000.0,float(default.get("mt",600)))

    if st.button("🚀 Calcular minhas chances"):

        df_result = df_filtrado.copy()

        df_result["Minha Nota"] = (
            redacao*df_result["redacao"] +
            humanas*df_result["ciencias humanas"] +
            natureza*df_result["ciencias da natureza"] +
            linguagens*df_result["linguagens e codigos"] +
            matematica*df_result["matematica"]
        ) / df_result["soma pesos"]

        df_result["Diferença"] = df_result["Minha Nota"] - df_result["nota corte"]

        def classificar(d):
            if d>=0: return "Alta chance"
            elif d>=-10: return "Média"
            else: return "Baixa"

        df_result["Chance"] = df_result["Diferença"].apply(classificar)

        df_result = df_result.sort_values(by="Diferença", ascending=False)

        st.subheader("🏆 Melhores opções")

        aprovados = df_result[df_result["Diferença"]>=0]

        top3 = aprovados.sort_values(by="nota corte", ascending=False).head(3) if not aprovados.empty else df_result.head(3)

        cols = st.columns(3)

        for i,(_,row) in enumerate(top3.iterrows()):
            with cols[i]:
                st.metric(row["curso"], f"{row['Minha Nota']:.1f}", f"{row['Diferença']:.1f}")
                st.caption(f"{row['universidade']} - {row['campus']}")

# ========================
# ⚖️ PESOS (INALTERADO)
# ========================

with aba2:

    st.title("⚖️ Pesos dos cursos")

    uni = st.multiselect("Universidade", sorted(df["universidade"].unique()))

    df_peso = df if len(uni)==0 else df[df["universidade"].isin(uni)]

    curso = st.multiselect("Curso", sorted(df_peso["curso"].unique()))

    if len(curso)>0:
        df_peso = df_peso[df_peso["curso"].isin(curso)]

    st.dataframe(df_peso, hide_index=True)