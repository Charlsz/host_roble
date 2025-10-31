FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias Python necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask requests flask-cors docker

COPY manager.py . 

EXPOSE 5000

CMD ["python", "manager.py"]
