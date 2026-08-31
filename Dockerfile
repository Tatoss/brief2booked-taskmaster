FROM node:22-bookworm-slim AS dashboard
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY app ./app
COPY public ./public
COPY vendor ./vendor
COPY next.config.ts postcss.config.mjs tsconfig.json ./
RUN npm run build:cloud

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    WEB_ROOT=/app/dashboard
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/brief2booked ./brief2booked
COPY backend/configure_gmail_watch.py ./configure_gmail_watch.py
COPY --from=dashboard /web/out ./dashboard
CMD exec uvicorn brief2booked.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers
