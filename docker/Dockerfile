# --- Frontend build stage: compile Tailwind CSS ---
FROM node:20-alpine AS frontend
WORKDIR /app
COPY package.json ./
RUN npm install
COPY templates ./templates
COPY apps ./apps
COPY static ./static
RUN npm run build:css

# --- Python runtime stage ---
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt

COPY . .
COPY --from=frontend /app/static/css/dist ./static/css/dist

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000