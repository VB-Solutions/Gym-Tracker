# Frontend de Gym-Tracker: build de Vite servido por nginx. Ver docs/DEPLOY.md.

# --- Build ---
# node:*-slim (glibc) y no alpine: los binarios nativos de rolldown/tailwind/lightningcss vienen para glibc
FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# URL pública de la API. Vite la incrusta en el JS durante el build (en Coolify: "Build Variable")
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Runtime ---
FROM nginx:1.29-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# Coolify usa este HEALTHCHECK (wget viene en la imagen alpine)
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1
