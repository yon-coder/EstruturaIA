"""Dashboard de análise dos currículos sintéticos gerados pelo Generator.py.

Execute com: streamlit run MetroAI.py
Dependências: pip install streamlit pypdf pandas plotly
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

try:
	from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
	raise SystemExit("Instale as dependências: pip install streamlit pypdf pandas plotly") from exc


PASTA_CURRICULOS = Path(__file__).resolve().parent / "Portifólios_treino"
AREAS = [
	"Desenvolvimento de Software", "Análise de Dados", "Design de Produto",
	"Gestão de Projetos",
]


def extrair_texto(caminho: Path) -> str:
	return "\n".join((pagina.extract_text() or "") for pagina in PdfReader(str(caminho)).pages)


def analisar_curriculo(caminho: Path) -> dict:
	texto = extrair_texto(caminho)
	linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
	nome = next((linha for linha in linhas if linha in {
		"Ana Silva", "Bruno Costa", "Carla Mendes", "Diego Santos", "Elisa Rocha"
	}), caminho.stem)
	area = next((item for item in AREAS if item in texto), "Não identificada")
	inicio = texto.find("HABILIDADES")
	fim = texto.find("AVISO", inicio)
	habilidades = [] if inicio < 0 else re.findall(
		r"(?:•|\n)\s*([^\n•]+)", texto[inicio:fim if fim >= 0 else None]
	)
	habilidades = [item.strip() for item in habilidades if item.strip()]
	return {
		"Candidato": nome,
		"Área": area,
		"Pontos fortes": ", ".join(habilidades),
		"Quantidade de habilidades": len(habilidades),
		"Arquivo": caminho.name,
	}


@st.cache_data
def carregar_curriculos(pasta: str) -> pd.DataFrame:
	arquivos = sorted(Path(pasta).glob("*.pdf"))
	return pd.DataFrame([analisar_curriculo(arquivo) for arquivo in arquivos])


def main() -> None:
	st.set_page_config(page_title="MetroAI — Currículos", page_icon="📄", layout="wide")
	st.title("📄 MetroAI — pontos fortes dos candidatos")
	pasta = st.sidebar.text_input("Pasta dos currículos", str(PASTA_CURRICULOS))
	try:
		dados = carregar_curriculos(pasta)
	except Exception as erro:
		st.error(f"Não foi possível ler os PDFs: {erro}")
		return
	if dados.empty:
		st.warning("Nenhum currículo PDF encontrado na pasta informada.")
		return

	areas = st.sidebar.multiselect("Filtrar por área", sorted(dados["Área"].unique()))
	exibidos = dados[dados["Área"].isin(areas)] if areas else dados
	colunas = st.columns(3)
	colunas[0].metric("Candidatos", len(exibidos))
	colunas[1].metric("Habilidades extraídas", int(exibidos["Quantidade de habilidades"].sum()))
	colunas[2].metric("Média por candidato", f"{exibidos['Quantidade de habilidades'].mean():.1f}")

	st.subheader("Pontos fortes por candidato")
	st.dataframe(exibidos[["Candidato", "Área", "Pontos fortes"]], hide_index=True, use_container_width=True)
	st.subheader("Comparativo de habilidades")
	grafico = exibidos[["Candidato", "Quantidade de habilidades"]].set_index("Candidato")
	st.bar_chart(grafico)
	st.download_button("Baixar análise CSV", exibidos.to_csv(index=False).encode("utf-8"),
					   "analise_curriculos.csv", "text/csv")


if __name__ == "__main__":
	main()
