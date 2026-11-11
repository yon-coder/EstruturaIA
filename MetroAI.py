from __future__ import annotations

import asyncio
import json
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from pypdf import PdfReader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MetroAI")

# --- Configuração do Ambiente e Gemini ---
load_dotenv()
CHAVE_API = os.environ.get("GEMINI_API_KEY")
if not CHAVE_API:
    logger.critical("A chave GEMINI_API_KEY não foi encontrada no arquivo .env!")
    raise ValueError("A chave GEMINI_API_KEY não foi encontrada.")

genai.configure(api_key=CHAVE_API)
modelo_gemini = genai.GenerativeModel("gemini-1.5-flash")

# Constantes
TAMANHO_MAXIMO_PDF = 10 * 1024 * 1024
PASTA_CURRICULOS = Path(__file__).resolve().parent / "Portifólios_treino"

# --- Configuração de Rate Limiting (Passo 4) ---
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="MetroAI — API de Análise de Currículos",
    description="API assíncrona com IA para análise de currículos e match de vagas.",
    version="2.0.0",
)
# Adicionando o handler do limitador de requisições no FastAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- Modelos Pydantic (Atualizados para o Passo 2) ---
class AnaliseCurriculoResponse(BaseModel):
    candidato: str = Field(..., alias="Candidato")
    area: str = Field(..., alias="Área")
    pontos_fortes: str = Field(..., alias="Pontos fortes")
    habilidades: List[str] = Field(..., alias="Habilidades")
    quantidade_habilidades: int = Field(..., alias="Quantidade de habilidades")
    score_recomendacao: int = Field(..., alias="Score")
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


# --- Funções Core ---
def extrair_texto(caminho_ou_stream: Path | BytesIO) -> str:
    try:
        reader = PdfReader(caminho_ou_stream)
        return "\n".join((pagina.extract_text() or "") for pagina in reader.pages)
    except Exception as erro:
        logger.error("Falha ao extrair texto do PDF.", exc_info=True)
        raise ValueError("Não foi possível ler a estrutura do arquivo PDF.") from erro

# Passo 1 (Async) e Passo 2 (Match de Vagas) aplicados aqui
async def analisar_texto(texto: str, arquivo: str, descricao_vaga: Optional[str] = None) -> dict:
    
    # Adapta a instrução da IA dependendo se o RH enviou uma vaga ou não
    if descricao_vaga:
        contexto_score = f"Calcule o 'Score' (0 a 100) estritamente baseado na aderência entre o currículo e esta vaga: {descricao_vaga}"
        criterio = "Match percentual com a descrição da vaga fornecida."
    else:
        contexto_score = "Calcule o 'Score' (0 a 100) baseado na qualidade técnica geral e quantidade de habilidades relevantes do candidato."
        criterio = "Análise geral de mercado (sem vaga específica)."

    prompt = f"""
    Leia o seguinte currículo e extraia os dados principais.
    {contexto_score}

    Retorne APENAS um objeto JSON válido com as chaves exatas:
    - "Candidato": Nome do candidato (ou "Não identificado").
    - "Área": Área de atuação principal.
    - "Habilidades": Array de strings com as tecnologias/competências.
    - "Score": Número inteiro de 0 a 100.
    - "Justificativa": Uma frase curta (máx 2 linhas) justificando o score recebido.

    Texto do currículo:
    {texto}
    """

    try:
        # Chamada Assíncrona, não bloqueia o servidor!
        resposta = await modelo_gemini.generate_content_async(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        dados = json.loads(resposta.text)
        nome = dados.get("Candidato", Path(arquivo).stem)
        area = dados.get("Área", "Não identificada")
        habilidades = dados.get("Habilidades", [])
        score = dados.get("Score", 0)
        justificativa = dados.get("Justificativa", "Sem justificativa.")
    except Exception as e:
        logger.error(f"Erro na IA ao processar '{arquivo}': {str(e)}", exc_info=True)
        raise RuntimeError("Falha de comunicação com a inteligência artificial.") from e

    resumo = f"{nome}: área {area}. {justificativa}"

    return {
        "Candidato": nome,
        "Área": area,
        "Pontos fortes": ", ".join(habilidades),
        "Habilidades": habilidades,
        "Quantidade de habilidades": len(habilidades),
        "Score": score,
        "Relatório": resumo,
        "Critério do score": criterio,
        "Arquivo": arquivo,
    }

async def analisar_curriculo(caminho: Path) -> dict:
    # Como a leitura de disco é rápida e o pypdf é síncrono, rodamos direto.
    texto = extrair_texto(caminho)
    return await analisar_texto(texto, caminho.name)


# --- Endpoints ---
@app.get("/health", status_code=status.HTTP_200_OK)
async def verificar_saude() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analisar", response_model=AnaliseCurriculoResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute") # Passo 4: Limita a 10 requisições por minuto por IP
async def analisar_upload(
    request: Request, # Obrigatório para o limitador de taxa funcionar
    arquivo: UploadFile = File(...),
    descricao_vaga: Optional[str] = Form(None, description="Descrição da vaga para cálculo de Match")
) -> dict:
    
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
        return await analisar_texto(texto, Path(arquivo.filename).name, descricao_vaga)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Serviço de IA temporariamente indisponível.")


@app.get("/relatorios", response_model=RelatoriosLoteResponse, status_code=status.HTTP_200_OK)
@limiter.limit("2/minute") # Limite rigoroso pois processamento em lote custa caro
async def gerar_relatorios(request: Request) -> dict:
    if not PASTA_CURRICULOS.exists():
        PASTA_CURRICULOS.mkdir(parents=True, exist_ok=True)
    
    arquivos_pdf = list(PASTA_CURRICULOS.glob("*.pdf"))
    relatorios = []
    erros = []
    
    # Processa múltiplos PDFs simultaneamente via asyncio.gather (Muito mais rápido!)
    resultados = await asyncio.gather(*(analisar_curriculo(c) for c in arquivos_pdf), return_exceptions=True)
    
    for caminho, resultado in zip(arquivos_pdf, resultados):
        if isinstance(resultado, Exception):
            logger.error(f"Erro ao processar lote no arquivo {caminho.name}: {resultado}")
            erros.append(caminho.name)
        else:
            relatorios.append(resultado)
            
    scores = [r["Score"] for r in relatorios]
    return {
        "total_curriculos": len(relatorios),
        "score_medio": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "relatorios": relatorios,
        "arquivos_com_erro": erros,
    }