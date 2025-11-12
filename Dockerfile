# Usa Python 3.11 slim
FROM python:3.11-slim

# Instala git (necesario para operaciones con repos)
RUN apt-get update && \
    apt-get install -y git curl && \
    rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia requirements primero (cache de Docker)
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY . .

# Crea carpeta para repos temporales (si la usa tu app)
RUN mkdir -p /app/repo_temp && chmod 777 /app/repo_temp

# Expone el puerto de Streamlit
EXPOSE 8501

# Configuración de Streamlit para producción
RUN mkdir -p ~/.streamlit && \
    echo "[server]\n\
    headless = true\n\
    port = 8501\n\
    enableCORS = false\n\
    enableXsrfProtection = false\n\
    address = 0.0.0.0\n\
    \n\
    [browser]\n\
    gatherUsageStats = false\n\
    " > ~/.streamlit/config.toml

# Configura git globalmente (para operaciones de clonado)
RUN git config --global user.email "streamlit@app.com" && \
    git config --global user.name "Streamlit App"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando para ejecutar la app
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
