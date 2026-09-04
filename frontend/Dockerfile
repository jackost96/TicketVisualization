# ---- build: compile the SPA to static files ----
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Baked in at build time (Vite env vars are compile-time). Defaults to a relative path so the
# built app calls whatever origin serves it -- nginx below proxies that path to the backend
# container, so the browser never needs a cross-origin request (no CORS involved).
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ---- runtime: serve the built static files ----
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
