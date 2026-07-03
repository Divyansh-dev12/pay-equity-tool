# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# Stage 2: FastAPI backend + built frontend
FROM python:3.11-slim
WORKDIR /app/backend

# Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend source (imports resolve relative to /app/backend)
COPY backend/ ./

# Frontend build → /app/frontend_dist (main.py mounts this path)
COPY --from=frontend-builder /app/frontend/dist /app/frontend_dist

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
