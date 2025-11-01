FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias Python necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask requests flask-cors docker

# Copiar todos los archivos Python del manager
COPY manager.py .
COPY roble_client.py .
COPY auth_routes.py .
COPY projects_routes.py .
COPY deploy_service.py .

EXPOSE 5000

CMD ["python", "manager.py"]
