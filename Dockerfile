# Imagem base enxuta
FROM python:3.12-slim

# Diretório de trabalho
WORKDIR /app

# Instala dependências primeiro (cache de layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Porta exposta
EXPOSE 5000

# Comando de desenvolvimento (com reload automático)
CMD ["python", "app.py"]
