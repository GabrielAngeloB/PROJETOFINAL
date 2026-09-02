# 1. Pega um Linux "limpo" já com Python e os navegadores do Playwright instalados
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# 2. Cria uma pasta chamada /app lá dentro e diz que vamos trabalhar nela
WORKDIR /app

# 3. Copia a sua lista de pacotes para dentro do contêiner e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia todos os seus códigos Python para dentro da pasta /app
COPY . .

# 5. Fica aguardando. Quando o contêiner ligar, ele vai rodar o seu script
CMD ["python", "crawler.py"]