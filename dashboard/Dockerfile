FROM node:22-slim AS frontend
WORKDIR /build
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/index.html dashboard/main.jsx dashboard/style.css dashboard/vite.config.js ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY market_regression.py ./
COPY dashboard/api.py dashboard/api.py
COPY --from=frontend /build/dist dashboard/dist
EXPOSE 8000
CMD ["python", "dashboard/api.py", "--host", "0.0.0.0"]
