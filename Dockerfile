# Use a imagem base do Python
FROM python:3.8

# Crie um diretório de trabalho no container
WORKDIR /app

# Instale o git no container (caso não esteja instalado)
RUN apt-get update && apt-get install -y git

# Clone o repositório Git para o container
RUN git clone https://github.com/viivazz/api-tempo.git .

# Copie o arquivo requirements.txt para o container
COPY requirements.txt .

# Crie e ative um ambiente virtual
RUN python -m venv venv
RUN . /app/venv/bin/activate

# Instale as dependências
RUN pip install -r requirements.txt

# Inicialize o aplicativo Flask
CMD ["python", "api_tempo.py"]
