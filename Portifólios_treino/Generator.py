from __future__ import annotations

import argparse
import random
from pathlib import Path

try:
	from reportlab.lib.pagesizes import A4
	from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
	from reportlab.lib.units import cm
	from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except ImportError as exc:
	raise SystemExit("Instale a dependência com: pip install reportlab") from exc


NOMES = ["Ana Silva", "Bruno Costa", "Carla Mendes", "Diego Santos", "Elisa Rocha"]
AREAS = {
	"Desenvolvimento de Software": ["Python", "APIs REST", "Git", "SQL"],
	"Análise de Dados": ["Python", "Pandas", "SQL", "Power BI"],
	"Design de Produto": ["Figma", "Pesquisa UX", "Prototipação", "Design systems"],
	"Gestão de Projetos": ["Scrum", "Kanban", "Jira", "Gestão de riscos"],
}


def gerar_curriculo(numero: int, pasta: Path, rng: random.Random) -> Path:
	nome = rng.choice(NOMES)
	area = rng.choice(list(AREAS))
	habilidades = rng.sample(AREAS[area], len(AREAS[area]))
	destino = pasta / f"curriculo_sintetico_{numero:03d}.pdf"

	estilos = getSampleStyleSheet()
	titulo = ParagraphStyle("Titulo", parent=estilos["Title"], fontSize=18, spaceAfter=10)
	secao = ParagraphStyle("Secao", parent=estilos["Heading2"], spaceBefore=10)
	corpo = ParagraphStyle("Corpo", parent=estilos["BodyText"], leading=15)
	documento = SimpleDocTemplate(
		str(destino), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
		topMargin=1.5 * cm, bottomMargin=1.5 * cm,
	)
	partes = [
		Paragraph("CURRÍCULO SINTÉTICO — DADOS FICTÍCIOS", titulo),
		Paragraph(f"<b>{nome}</b>", secao),
		Paragraph(f"Profissional de {area} | contato-{numero:03d}@exemplo.invalid", corpo),
		Paragraph("PERFIL", secao),
		Paragraph(
			f"Profissional fictício com experiência simulada em {area.lower()}, "
			"criado exclusivamente para testes e treinamento.", corpo,
		),
		Paragraph("EXPERIÊNCIA PROFISSIONAL", secao),
		Paragraph(
			f"Empresa Exemplo {numero:03d} — {area} (2021–2024)<br/>"
			"Participação em projetos internos simulados e colaboração com equipes.", corpo,
		),
		Paragraph("FORMAÇÃO", secao),
		Paragraph("Curso superior fictício — Instituto de Exemplo (2020)", corpo),
		Paragraph("HABILIDADES", secao),
		Paragraph(" • " + "<br/> • ".join(habilidades), corpo),
		Spacer(1, 12),
		Paragraph("AVISO: este documento não representa uma pessoa real.", corpo),
	]
	documento.build(partes)
	return destino


def gerar_curriculo_texto(numero: int, rng: random.Random) -> dict:
	"""Retorna a representação estruturada usada para testes sem criar PDF."""
	nome = rng.choice(NOMES)
	area = rng.choice(list(AREAS))
	habilidades = rng.sample(AREAS[area], len(AREAS[area]))
	return {"Candidato": nome, "Área": area, "Habilidades": habilidades,
			"Texto": f"Profissional fictício de {area}. Habilidades: {', '.join(habilidades)}."}


def main() -> None:
	parser = argparse.ArgumentParser(description="Gera currículos PDF sintéticos")
	parser.add_argument("--quantidade", type=int, default=1, help="número de PDFs (1-1000)")
	parser.add_argument("--seed", type=int, help="semente para resultados reproduzíveis")
	args = parser.parse_args()
	if not 1 <= args.quantidade <= 1000:
		parser.error("quantidade deve estar entre 1 e 1000")

	pasta = Path(__file__).resolve().parent
	rng = random.Random(args.seed)
	for numero in range(1, args.quantidade + 1):
		print(gerar_curriculo(numero, pasta, rng))


if __name__ == "__main__":
	main()
