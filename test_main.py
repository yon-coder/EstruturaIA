import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from io import BytesIO

# Importa a sua API
from MetroAI import app 

client = TestClient(app)

def test_health_check():
    """Testa se a API está online."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# O @patch substitui a chamada real do Gemini por uma função fantasma (AsyncMock)
@patch("MetroAI.modelo_gemini.generate_content_async", new_callable=AsyncMock)
@patch("MetroAI.extrair_texto")
def test_analisar_upload_com_vaga(mock_extrair, mock_gemini):
    """Testa o endpoint de upload enviando uma descrição de vaga."""
    
    # 1. Dizemos para o nosso teste fingir que extraiu este texto do PDF
    mock_extrair.return_value = "Desenvolvedor Sênior com 10 anos de Python e AWS."
    
    # 2. Criamos a resposta falsa (Mock) simulando o que o Gemini devolveria
    class MockRespostaIA:
        text = '{"Candidato": "Carlos", "Área": "TI", "Habilidades": ["Python", "AWS"], "Score": 95, "Justificativa": "Excelente match."}'
    
    mock_gemini.return_value = MockRespostaIA()

    # 3. Disparamos a requisição de teste para a nossa própria API
    pdf_falso = BytesIO(b"%PDF-1.4 Mocked content")
    response = client.post(
        "/analisar",
        files={"arquivo": ("curriculo_carlos.pdf", pdf_falso, "application/pdf")},
        data={"descricao_vaga": "Preciso de especialista em Python e Nuvem (AWS)"}
    )

    # 4. Verificamos se as regras de negócio funcionaram
    assert response.status_code == 200
    dados = response.json()
    
    assert dados["Candidato"] == "Carlos"
    assert dados["Score"] == 95
    assert "Match percentual" in dados["Critério do score"]

def test_analisar_upload_extensao_invalida():
    """Garante que a API rejeita arquivos que não sejam PDF."""
    arquivo_falso = BytesIO(b"conteudo de imagem")
    response = client.post(
        "/analisar",
        files={"arquivo": ("foto.jpg", arquivo_falso, "image/jpeg")}
    )
    assert response.status_code == 415
    assert "Envie um arquivo .pdf" in response.json()["detail"]