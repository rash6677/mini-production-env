# Start from a small official Python image with Python 3.12 installed.
FROM python:3.12-slim

# Keep Python output visible in container logs and avoid bytecode clutter.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies before copying source so Docker can reuse this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run the service as an unprivileged account.
RUN groupadd --system app && useradd --system --gid app app
USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
