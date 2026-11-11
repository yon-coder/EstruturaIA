from __future__ import annotations

import json
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import List

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from pypdf import PdfReader

# --- Configuração de Logs (Passo 3) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MetroAI")

# --- Configuração do Ambiente e Gemini ---
load_dotenv()

CHAVE_API = os.environ.get("GEMINI_API_KEY")
if not CHAVE_API:
    logger.critical("A chave GEMINI_API_KEY não foi encontrada no arquivo .env!")
    raise ValueError("A chave GEMINI_API_KEY não foi encontrada no arquivo .env")

genai.configure(api_key=CHAVE_API)
modelo_gemini = genai.GenerativeModel("gemini-1.5-flash")

# Constantes (10 MB)
TAMANHO_MAXIMO_PDF = 10 * 1024 * 1024
PASTA_CURRICULOS = Path(__file__).resolve().parent / "Portifólios_treino"

app = FastAPI(
    title="MetroAI — API de Análise de Currículos",
    description="Extrai habilidades, gera relatórios e calcula o score usando IA do Gemini.",
    version="1.2.0",
)

class AnaliseCurriculoResponse(BaseModel):
    candidato: str = Field(..., alias="Candidato")
    area: str = Field(..., alias="Área")
    pontos_fortes: str = Field(..., alias="Pontos fortes")
    habilidades: List[str] = Field(..., alias="Habilidades")
    quantidade_habilidades: int = Field(..., alias="Quantidade de habilidades")
    score_recomendacao: int = Field(..., alias="Score de recomendação")
    relatorio: str = Field(..., alias="Relatório")
    criterio_score: str = Field(..., alias="Critério do score")
    arquivo: str = Field(..., alias="Arquivo")

    class Config:
        populate_by_name = True

class RelatoriosLoteResponse(BaseModel):
    total_curriculos: int
    score_medio: float
    relatorios: List[AnaliseCurriculoResponse]
    arquivos_com_erro: List[str]

def extrair_texto(caminho_ou_stream: Path | BytesIO) -> str:
    try:
        reader = PdfReader(caminho_ou_stream)
        texto = "\n".join((pagina.extract_text() or "") for pagina in reader.pages)
        return texto
    except Exception as erro:
        logger.error("Falha ao extrair texto do PDF.", exc_info=True)
        raise ValueError("Não foi possível ler a estrutura do arquivo PDF.") from erro

def analisar_texto(texto: str, arquivo: str) -> dict:
    prompt = f"""
    Leia o seguinte currículo e extraia os dados principais.
    Retorne APENAS um objeto JSON válido com as seguintes chaves:
    - "Candidato": Nome do candidato (ou "Não identificado").
    - "Área": Área de atuação principal (ex: "Desenvolvimento", "Design", etc).
    - "Habilidades": Uma lista (array) de strings com as ferramentas, tecnologias ou competências citadas.

    Texto do currículo:
    {texto}
    """

    try:
        resposta = modelo_gemini.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        dados = json.loads(resposta.text)
        nome = dados.get("Candidato", Path(arquivo).stem)
        area = dados.get("Área", "Não identificada")
        habilidades = dados.get("Habilidades", [])
    except Exception as e:
        # Passo 3: Log detalhado do erro da IA
        logger.error(f"Erro na API do Gemini ao processar '{arquivo}': {str(e)}", exc_info=True)
        raise RuntimeError("Falha de comunicação com a inteligência artificial.") from e

    score = min(100, 40 + len(habilidades) * 10)
    resumo = (
        f"{nome}: área {area}. Foram identificadas {len(habilidades)} habilidades: "
        f"{', '.join(habilidades) if habilidades else 'nenhuma habilidade extraída'}. "
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

def analisar_curriculo(caminho: Path) -> dict:
    texto = extrair_texto(caminho)
    return analisar_texto(texto, caminho.name)

@app.get("/health", status_code=status.HTTP_200_OK)
async def verificar_saude() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/analisar", response_model=AnaliseCurriculoResponse, status_code=status.HTTP_200_OK)
async def analisar_upload(arquivo: UploadFile = File(...)) -> dict:
    if not arquivo.filename or Path(arquivo.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Envie um arquivo .pdf.")
    
    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAXIMO_PDF:
        raise HTTPException(status_code=413, detail="Máximo de 10 MB.")
    
    try:
        texto = extrair_texto(BytesIO(conteudo))
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))
    
    if not texto.strip():
        raise HTTPException(status_code=422, detail="PDF sem texto.")
    
    try:
        return analisar_texto(texto, Path(arquivo.filename).name)
    except RuntimeError:
        # Passo 3: Retorna erro 503 se a IA cair, informando o front-end
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Serviço de IA temporariamente indisponível."
        )

@app.get("/relatorios", response_model=RelatoriosLoteResponse, status_code=status.HTTP_200_OK)
async def gerar_relatorios() -> dict:
    if not PASTA_CURRICULOS.exists():
        PASTA_CURRICULOS.mkdir(parents=True, exist_ok=True)
    relatorios, erros = [], []
    
    for caminho in sorted(PASTA_CURRICULOS.glob("*.pdf")):
        try:
            relatorios.append(analisar_curriculo(caminho))
        except Exception as e:
            # Passo 3: Loga o arquivo específico que falhou no lote sem quebrar os demais
            logger.error(f"Erro ao processar lote no arquivo {caminho.name}: {e}")
            erros.append(caminho.name)
            
    scores = [r["Score de recomendação"] for r in relatorios]
    return {
        "total_curriculos": len(relatorios),
        "score_medio": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "relatorios": relatorios,
        "arquivos_com_erro": erros,
    }