# ---- stage 1: build the React app ----
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- stage 2: Python server + built frontend ----
FROM python:3.13-slim
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app
WORKDIR /app
COPY --chown=user backend/requirements.txt ./
ENV PATH="/home/user/.local/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user backend/ ./
COPY --chown=user --from=web /web/dist ./static
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]