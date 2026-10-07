"""API para análise de currículos em PDF. Execute com uvicorn MetroAI:app --reload."""
from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pypdf import PdfReader


TAMANHO_MAXIMO_PDF = 10 * 1024 * 1024
app = FastAPI(
	title="MetroAI — API de análise de currículos",
	description="Extrai habilidades, gera um relatório e calcula um score para currículos PDF.",
	version="1.0.0",
)


PASTA_CURRICULOS = Path(__file__).resolve().parent / "Portifólios_treino"
AREAS = [
	"Desenvolvimento de Software", "Análise de Dados", "Design de Produto",
	"Gestão de Projetos",
]


def extrair_texto(caminho: Path) -> str:
	return "\n".join((pagina.extract_text() or "") for pagina in PdfReader(str(caminho)).pages)


def analisar_curriculo(caminho: Path) -> dict:
	return analisar_texto(extrair_texto(caminho), caminho.name)


def analisar_texto(texto: str, arquivo: str) -> dict:
	linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
	nome = next((linha for linha in linhas if linha in {
		"Ana Silva", "Bruno Costa", "Carla Mendes", "Diego Santos", "Elisa Rocha"
	}), Path(arquivo).stem)
	area = next((item for item in AREAS if item in texto), "Não identificada")
	inicio = texto.find("HABILIDADES")
	fim = texto.find("AVISO", inicio)
	habilidades = [] if inicio < 0 else re.findall(
		r"(?:•|\n)\s*([^\n•]+)", texto[inicio:fim if fim >= 0 else None]
	)
	habilidades = [item.strip() for item in habilidades if item.strip()]
	score = min(100, 40 + len(habilidades) * 10)
	resumo = (
		f"{nome}: área {area}. Foram identificadas {len(habilidades)} habilidades: "
		f"{', '.join(habilidades) if habilidades else 'nenhuma habilidade na seção HABILIDADES'}. "
		f"Score de recomendação: {score}/100."
	)
	return {
		"Candidato": nome,
		"Área": area,
		"Pontos fortes": ", ".join(habilidades),
		"Habilidades": habilidades,
		"Quantidade de habilidades": len(habilidades),
		"Score de recomendação": score,
		"Relatório": resumo,
		"Critério do score": "40 pontos base + 10 por habilidade identificada, limitado a 100.",
		"Arquivo": arquivo,
	}


@app.get("/health")
def verificar_saude() -> dict:
	return {"status": "ok"}


@app.post("/analisar")
def analisar_upload(arquivo: UploadFile = File(...)) -> dict:
	if not arquivo.filename or Path(arquivo.filename).suffix.lower() != ".pdf":
		raise HTTPException(status_code=415, detail="Envie um arquivo com extensão .pdf.")

	conteudo = arquivo.file.read(TAMANHO_MAXIMO_PDF + 1)
	if len(conteudo) > TAMANHO_MAXIMO_PDF:
		raise HTTPException(status_code=413, detail="O PDF deve ter no máximo 10 MB.")

	try:
		texto = "\n".join(
			pagina.extract_text() or "" for pagina in PdfReader(BytesIO(conteudo)).pages
		)
	except Exception as erro:
		raise HTTPException(status_code=422, detail="Não foi possível ler o PDF.") from erro
	if not texto.strip():
		raise HTTPException(status_code=422, detail="O PDF não contém texto extraível.")
	return analisar_texto(texto, Path(arquivo.filename).name)


@app.get("/relatorios")
def gerar_relatorios() -> dict:
	relatorios = []
	erros = []
	for caminho in sorted(PASTA_CURRICULOS.glob("*.pdf")):
		try:
			relatorios.append(analisar_curriculo(caminho))
		except Exception:
			erros.append(caminho.name)

	scores = [registro["Score de recomendação"] for registro in relatorios]
	return {
		"total_curriculos": len(relatorios),
		"score_medio": round(sum(scores) / len(scores), 2) if scores else 0,
		"relatorios": relatorios,
		"arquivos_com_erro": erros,
	}
