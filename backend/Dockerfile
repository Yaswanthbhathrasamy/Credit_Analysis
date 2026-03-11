FROM python:3.11-slim

WORKDIR /app

# System dependencies for PyMuPDF, PaddleOCR, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip + increase timeout (IMPORTANT)
RUN pip install --upgrade pip && \
    pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

COPY . .

# Create directories
RUN mkdir -p uploads reports

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]