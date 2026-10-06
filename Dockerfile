FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/instance /app/uploads
EXPOSE 5000
CMD ["sh","-c","gunicorn run:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120"]
