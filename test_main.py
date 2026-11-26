from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from MetroAI import analisar_localmente, analisar_texto, app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analise_local_extrai_evidencias_sem_nota():
    texto = """Carlos Silva
    Desenvolvedor de Software
    Experiência: atuou na Empresa Exemplo com APIs REST e AWS.
    Formação: Bacharelado em Engenharia de Software.
    Habilidades: Python, SQL, Docker, Git e Java.
    """

    dados = analisar_localmente(texto, "curriculo_carlos.pdf", "Bacharelado em Engenharia de Software, AWS")

    assert dados["Candidato"] == "Carlos Silva"
    assert dados["Área"] == "Desenvolvimento de Software"
    assert {"Python", "AWS", "Docker", "Git", "Java"}.issubset(dados["Habilidades"])
    assert dados["Critérios observados"] == [
        "Evidência encontrada para: Bacharelado em Engenharia de Software",
        "Evidência encontrada para: AWS",
    ]
    assert "Score" not in dados

def test_analisar_upload_extensao_invalida():
    response = client.post(
        "/analisar",
        files={"arquivo": ("foto.jpg", BytesIO(b"conteudo de imagem"), "image/jpeg")},
    )
    assert response.status_code == 415
    assert "Envie um arquivo .pdf" in response.json()["detail"]


@patch("MetroAI.cliente_openai.responses.create", new_callable=AsyncMock)
def test_mantem_resultado_local_quando_resumo_ia_falha(mock_openai):
    mock_openai.side_effect = RuntimeError("sem créditos")

    import asyncio

    dados = asyncio.run(analisar_texto("Ana Lima\nHabilidades: Python e SQL", "ana.pdf", usar_ia=True))

    assert dados["Fonte do resumo"] == "Análise local; resumo por IA indisponível."
    assert "Python" in dados["Habilidades"]
