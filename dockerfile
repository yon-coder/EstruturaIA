FROM python:3.11-slim

#define o diretório de trabalho dentro do container
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

#comando para iniciar a API quando o container rodar
CMD ["uvicorn", "MetroAI:app", "--host", "0.0.0.0", "--port", "8000"]